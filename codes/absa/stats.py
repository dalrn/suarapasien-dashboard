"""
Statistical aggregation of findings into per-puskesmas SERVQUAL profiles and
kabupaten-level topic analysis — the inferential layer of SuaraPasien.

Every dashboard number is treated as a SAMPLE ESTIMATE with uncertainty, not a
raw count. Four components (in priority order):

  1. SERVQUAL scores: negativity ratio per dimension as a proportion with a
     Wilson CI, then empirical-Bayes (Beta-Binomial) shrinkage toward the
     kabupaten mean so small-n puskesmas are not over-confident. Mapped to 1-5.
  2. Comparison badges: hypothesis tests of one puskesmas vs its peers
     (two-proportion z-test), plus a star-rating-vs-text-sentiment mismatch flag.
  3. Cross-region association: chi-square independence test + standardized
     residuals on dimension x wilayah; co-occurrence of dimensions within a
     review via lift.
  4. (sub_issue canonicalization lives in clustering.py — embeddings.)

All functions take the long findings DataFrame:
  columns = review_id, puskesmas_id, puskesmas_name, wilayah, rating,
            dimension, polarity, sub_issue, quote, [sumber]
"""

from __future__ import annotations
import math
import numpy as np
import pandas as pd
from scipy import stats as scipy_stats

from .prompts import SERVQUAL_DIMS


# ---------------------------------------------------------------------------
# Wilson CI (shared with evaluate.py but re-stated here to keep stats.py standalone)
# ---------------------------------------------------------------------------

def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    half = (z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


# ---------------------------------------------------------------------------
# 1. Per-puskesmas SERVQUAL scores with Beta-Binomial shrinkage
# ---------------------------------------------------------------------------

def _review_level_polarity(findings: pd.DataFrame) -> pd.DataFrame:
    """
    Collapse findings to one (review, dimension) row with a single polarity:
    'neg' if any neg finding for that dim in that review, else 'pos'.
    A review contributes at most one observation per dimension — prevents a
    chatty review from dominating.
    """
    df = findings.copy()
    df = df[df["dimension"].isin(SERVQUAL_DIMS)]
    # neg dominates: a dimension counts as negative if any neg finding exists
    df["is_neg"] = (df["polarity"] == "neg").astype(int)
    agg = (
        df.groupby(["puskesmas_id", "puskesmas_name", "wilayah", "review_id", "dimension"])["is_neg"]
        .max()
        .reset_index()
    )
    return agg


def _empirical_bayes_params(neg: np.ndarray, tot: np.ndarray) -> tuple[float, float]:
    """
    Estimate Beta prior (alpha, beta) for the negativity rate across puskesmas
    via method of moments on the observed per-puskesmas rates (weighted by n).
    Used to shrink small-n estimates toward the kabupaten mean.
    """
    mask = tot > 0
    if mask.sum() < 2:
        return (1.0, 1.0)   # uninformative fallback
    rates = neg[mask] / tot[mask]
    w = tot[mask] / tot[mask].sum()
    mean = float(np.sum(w * rates))
    var = float(np.sum(w * (rates - mean) ** 2))
    if var <= 1e-9 or mean <= 0 or mean >= 1:
        return (1.0, 1.0)
    # method of moments for Beta
    common = mean * (1 - mean) / var - 1
    alpha = max(mean * common, 1e-3)
    beta = max((1 - mean) * common, 1e-3)
    return (alpha, beta)


def _confidence_label(n: int) -> str:
    if n >= 30:
        return "Cukup banyak data"
    if n >= 10:
        return "Datanya sedang"
    return "Data terbatas"


def _intensity_to_score(rate_shrunk: float, all_rates: np.ndarray,
                        higher_is_worse: bool = True) -> float:
    """
    Map a complaint-intensity rate to a 1-5 score by its PERCENTILE among all
    puskesmas (for that dimension). Percentile mapping is what gives spread when
    raw rates are bunched — every review here is negative, so absolute rates are
    near-uniform; relative standing is the informative signal.

    higher_is_worse=True  → 5 = most complained-about (priority).
    higher_is_worse=False → 5 = least complained-about. Flip anytime via this arg.
    """
    if len(all_rates) < 2 or np.all(np.isnan(all_rates)):
        return 3.0
    pct = (all_rates < rate_shrunk).mean()   # 0..1 percentile rank
    if not higher_is_worse:
        pct = 1 - pct
    return round(1 + pct * 4, 2)


def complaint_scores(findings: pd.DataFrame, min_n_score: int = 10,
                     higher_is_worse: bool = True) -> pd.DataFrame:
    """
    Per puskesmas x dimension COMPLAINT profile. This is NOT a satisfaction score
    — the dataset is 1-2 star reviews, so it measures how strongly each dimension
    is COMPLAINED ABOUT. Two complementary metrics:

      - komposisi_pct : of all this puskesmas's complaints, what share is this
        dimension? (its complaint *profile* — what the main problem here is)
      - intensitas_rate (+CI, +EB-shrunk): per review of this puskesmas, the rate
        that mention this dimension as a complaint — comparable across puskesmas.
      - skor_1_5 : percentile of the shrunk intensity among all puskesmas, mapped
        to 1-5. Direction set by `higher_is_worse` (default 5 = most complained).

    EB shrinkage (Beta-Binomial, per dimension) pulls small-n puskesmas toward
    the kabupaten mean so they aren't ranked on noise.
    """
    # review-level: does each review of each puskesmas complain about dim?
    df = findings[findings["dimension"].isin(SERVQUAL_DIMS)].copy()
    df["is_neg"] = (df["polarity"] == "neg").astype(int)
    rl = (
        df.groupby(["puskesmas_id", "puskesmas_name", "wilayah", "review_id", "dimension"])["is_neg"]
        .max().reset_index()
    )

    # total complaints per puskesmas (across dims) for komposisi
    neg_only = rl[rl["is_neg"] == 1]
    total_complaints = neg_only.groupby("puskesmas_id").size()

    # n reviews per puskesmas (any finding) — the SINGLE denominator used for
    # both the intensity rate AND the EB prior, so the prior is fit on the same
    # scale it is applied to (complaints per ALL reviews, not per-mention).
    n_reviews_pusk = findings.groupby("puskesmas_id")["review_id"].nunique()
    all_pids = n_reviews_pusk.index
    meta_by_pid = (
        findings.groupby("puskesmas_id")[["puskesmas_name", "wilayah"]].first()
    )

    rows = []
    for dim in SERVQUAL_DIMS:
        sub = rl[(rl["dimension"] == dim) & (rl["is_neg"] == 1)]
        # complaints about `dim` per puskesmas, over EVERY puskesmas (0 if none)
        comp = sub.groupby("puskesmas_id").size().reindex(all_pids, fill_value=0)
        # EB prior fit on intensity = complaints / all-reviews (the posterior base)
        alpha, beta = _empirical_bayes_params(comp.to_numpy(), n_reviews_pusk.to_numpy())

        recs = []
        for pid in all_pids:
            neg = int(comp.get(pid, 0))
            denom = int(n_reviews_pusk.get(pid, 0))
            if denom == 0:
                continue
            pname = meta_by_pid.loc[pid, "puskesmas_name"]
            wil = meta_by_pid.loc[pid, "wilayah"]
            lo, hi = wilson_ci(neg, denom)
            shrunk = (neg + alpha) / (denom + alpha + beta)
            komposisi = neg / total_complaints.get(pid, 1) if total_complaints.get(pid, 0) else 0.0
            recs.append({
                "puskesmas_id": pid, "puskesmas_name": pname, "wilayah": wil,
                "dimension": dim, "n_reviews": denom, "n_complaint": neg,
                "komposisi_pct": round(komposisi * 100, 1),
                "intensitas_rate": round(neg / denom, 3) if denom else 0.0,
                "intensitas_ci95": f"[{lo:.2f}, {hi:.2f}]",
                "intensitas_shrunk": round(shrunk, 3),
                "kepercayaan": _confidence_label(denom),
                "cukup_dinilai": denom >= min_n_score,
            })
        all_rates = np.array([x["intensitas_shrunk"] for x in recs])
        for x in recs:
            x["skor_1_5"] = _intensity_to_score(x["intensitas_shrunk"], all_rates, higher_is_worse)
        rows.extend(recs)
    return pd.DataFrame(rows)


# backward-compatible alias (notebook 08 may still import servqual_scores)
def servqual_scores(findings: pd.DataFrame, min_n_score: int = 10) -> pd.DataFrame:
    """Deprecated name → complaint_scores (5 = paling banyak dikeluhkan)."""
    return complaint_scores(findings, min_n_score=min_n_score, higher_is_worse=True)


# ---------------------------------------------------------------------------
# 2. Comparison badges: puskesmas vs peers (two-proportion z-test)
# ---------------------------------------------------------------------------

def _two_proportion_z(k1: int, n1: int, k2: int, n2: int) -> tuple[float, float]:
    """Two-proportion z-test. Returns (z, two-sided p). H0: p1 == p2."""
    if n1 == 0 or n2 == 0:
        return (float("nan"), float("nan"))
    p1, p2 = k1 / n1, k2 / n2
    p_pool = (k1 + k2) / (n1 + n2)
    se = math.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))
    if se == 0:
        return (float("nan"), float("nan"))
    z = (p1 - p2) / se
    p = 2 * (1 - scipy_stats.norm.cdf(abs(z)))
    return (round(z, 3), round(p, 4))


def peer_comparison(scores: pd.DataFrame, alpha: float = 0.05) -> pd.DataFrame:
    """
    For each puskesmas x dimension, test its complaint rate against the pooled
    rate of all OTHER puskesmas (its peers) via two-proportion z-test.
    Verdict (peer-relative, only when significant; else 'setara'):
      'lebih sering dikeluhkan' / 'lebih jarang dikeluhkan' / 'setara'.
    """
    rows = []
    for dim, grp in scores.groupby("dimension"):
        tot_neg = grp["n_complaint"].sum()
        tot_n = grp["n_reviews"].sum()
        for _, r in grp.iterrows():
            k1, n1 = int(r["n_complaint"]), int(r["n_reviews"])
            k2, n2 = int(tot_neg - k1), int(tot_n - n1)   # peers = all others
            z, p = _two_proportion_z(k1, n1, k2, n2)
            verdict = "setara"
            if not math.isnan(p) and p < alpha:
                verdict = "lebih sering dikeluhkan" if (k1 / n1) > (k2 / n2) else "lebih jarang dikeluhkan"
            rows.append({
                "puskesmas_id": r["puskesmas_id"], "dimension": dim,
                "z": z, "p": p, "vs_peer": verdict, "n_peer": n2,
            })
    return pd.DataFrame(rows)


def rating_text_mismatch(findings: pd.DataFrame, reviews: pd.DataFrame) -> pd.DataFrame:
    """
    Per puskesmas: flag "bintang tinggi tapi banyak keluhan di teks".
    Compares mean star rating (from `reviews`) against the text negativity rate
    (share of that puskesmas's reviews with >=1 negative finding).
    Returns puskesmas where high stars (>=4) coexist with high text-negativity (>=0.5).
    """
    rev = reviews.copy()
    rev["review_id"] = rev["review_id"].astype(str)
    star = rev.groupby("puskesmas_id")["rating"].mean()

    neg_reviews = (
        findings[findings["polarity"] == "neg"]
        .groupby("puskesmas_id")["review_id"].nunique()
    )
    tot_reviews = rev.groupby("puskesmas_id")["review_id"].nunique()
    text_neg_rate = (neg_reviews / tot_reviews).fillna(0)

    out = pd.DataFrame({
        "rating_bintang": star.round(2),
        "text_neg_rate": text_neg_rate.round(3),
        "n_reviews": tot_reviews,
    })
    out["mismatch"] = (out["rating_bintang"] >= 4) & (out["text_neg_rate"] >= 0.5)
    return out.reset_index()


# ---------------------------------------------------------------------------
# 3. Cross-region association + within-review co-occurrence
# ---------------------------------------------------------------------------

def region_dimension_chi2(findings: pd.DataFrame) -> dict:
    """
    Chi-square test of independence: dimension x wilayah on NEGATIVE findings.
    Returns chi2, dof, p, the contingency table, and standardized residuals
    (which cells deviate most from independence).
    """
    neg = findings[(findings["polarity"] == "neg") & findings["dimension"].isin(SERVQUAL_DIMS)]
    ct = pd.crosstab(neg["dimension"], neg["wilayah"])
    chi2, p, dof, expected = scipy_stats.chi2_contingency(ct)
    std_resid = (ct - expected) / np.sqrt(expected)
    return {
        "chi2": round(float(chi2), 3),
        "dof": int(dof),
        "p": float(p),
        "contingency": ct,
        "std_residuals": std_resid.round(2),
    }


def cooccurrence_lift(findings: pd.DataFrame) -> pd.DataFrame:
    """
    Within-review co-occurrence of dimensions, measured by LIFT.
    lift(A,B) = P(A & B) / (P(A) * P(B)); >1 means they co-occur more than chance.
    Computed over reviews (a review 'has' dim X if it has any finding in X).
    """
    df = findings[findings["dimension"].isin(SERVQUAL_DIMS)]
    by_review = df.groupby("review_id")["dimension"].apply(set)
    n = len(by_review)
    if n == 0:
        return pd.DataFrame()
    p_single = {d: by_review.apply(lambda s: d in s).mean() for d in SERVQUAL_DIMS}
    rows = []
    for i, a in enumerate(SERVQUAL_DIMS):
        for b in SERVQUAL_DIMS[i + 1:]:
            p_both = by_review.apply(lambda s: a in s and b in s).mean()
            denom = p_single[a] * p_single[b]
            lift = p_both / denom if denom > 0 else float("nan")
            rows.append({
                "dim_a": a, "dim_b": b,
                "p_a": round(p_single[a], 3), "p_b": round(p_single[b], 3),
                "p_both": round(p_both, 3),
                "lift": round(lift, 2) if not math.isnan(lift) else float("nan"),
            })
    return pd.DataFrame(rows).sort_values("lift", ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------------------
# 4. sub_issue canonicalization via SEMANTIC embeddings
# ---------------------------------------------------------------------------
# Char-ngram TF-IDF failed: it clusters on SPELLING, so "antre lama" and
# "nunggu lama" (same meaning, different words) never merge — yet "antre lama"
# and "antre obat lama" (different problems) do. We need MEANING, so we embed
# each sub_issue with a multilingual sentence model and cluster the vectors.

_EMBED_MODEL = None

def _get_embedder(model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
    """Lazy-load the multilingual sentence-transformer (cached across calls)."""
    global _EMBED_MODEL
    if _EMBED_MODEL is None:
        from sentence_transformers import SentenceTransformer
        _EMBED_MODEL = SentenceTransformer(model_name)
    return _EMBED_MODEL


# Intensifiers / fillers that change wording but NOT the underlying issue.
# Stripped before embedding so "antre sangat lama" ≈ "antre lama".
_INTENSIFIERS = [
    "sangat", "banget", "bgt", "amat", "terlalu", "begitu", "sekali",
    "berjam-jam", "berjam jam", "lama sekali", "parah", "amat sangat",
]

def _strip_intensifiers(phrase: str) -> str:
    """Remove intensifier words so phrases that differ only in emphasis collapse."""
    import re
    s = phrase
    for w in _INTENSIFIERS:
        s = re.sub(rf"\b{re.escape(w)}\b", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s or phrase   # never return empty


def canonicalize_sub_issues(
    findings: pd.DataFrame,
    dimension: str,
    *,
    k_range: tuple[int, int] = (6, 12),
    polarity: str = "neg",
    random_state: int = 42,
) -> pd.DataFrame:
    """
    Group a dimension's free-text sub_issues into ~k_range canonical issues by
    SEMANTIC similarity. Returns the per-finding rows with a 'cluster_label'
    column (the canonical issue name = most frequent ORIGINAL member of its cluster).

    Method: lightly normalize each phrase (strip intensifiers like "sangat",
    "berjam-jam" so emphasis variants merge) → embed the normalized form with a
    multilingual model → KMeans, choosing k in `k_range` by best silhouette.
    The display name still comes from the original phrasing. Falls back gracefully
    when there are too few unique phrases.
    """
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score
    from sklearn.preprocessing import normalize

    sub = findings[(findings["dimension"] == dimension)].copy()
    if polarity:
        sub = sub[sub["polarity"] == polarity]
    sub["sub_issue"] = sub["sub_issue"].astype(str).str.strip().str.lower()
    sub = sub[sub["sub_issue"] != ""]
    if sub.empty:
        sub["cluster_label"] = []
        return sub

    uniq = sub["sub_issue"].unique()
    if len(uniq) <= k_range[0]:
        # too few distinct phrases to cluster — each is its own canonical issue
        sub["cluster_label"] = sub["sub_issue"]
        return sub

    # embed the intensifier-stripped form so emphasis variants land together
    norm_uniq = [_strip_intensifiers(u) for u in uniq]
    emb = _get_embedder().encode(norm_uniq, show_progress_bar=False)
    emb = normalize(emb)   # cosine geometry

    best_k, best_labels, best_score = None, None, -1.0
    hi = min(k_range[1], len(uniq) - 1)
    for k in range(k_range[0], hi + 1):
        km = KMeans(n_clusters=k, random_state=random_state, n_init=10)
        labels = km.fit_predict(emb)
        score = silhouette_score(emb, labels, metric="cosine")
        if score > best_score:
            best_k, best_labels, best_score = k, labels, score

    # canonical name per cluster = most frequent sub_issue in it
    freq = sub["sub_issue"].value_counts()
    canon = {}
    for lab in set(best_labels):
        members = [uniq[i] for i in range(len(uniq)) if best_labels[i] == lab]
        canon_name = max(members, key=lambda m: freq.get(m, 0))
        for m in members:
            canon[m] = canon_name
    sub["cluster_label"] = sub["sub_issue"].map(canon)
    return sub
