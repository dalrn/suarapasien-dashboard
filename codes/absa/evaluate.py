"""
Evaluation of ABSA extraction against a human gold standard.

Pipeline:
  1. Inter-annotator agreement (Cohen's kappa, pairwise over 3 annotators) —
     validate the SCHEMA before blaming the model.
  2. Adjudicate three annotators into a single gold standard via majority vote.
  3. Score the model against gold: per-category precision / recall / F1 with
     Wilson confidence intervals, polarity accuracy, and an error taxonomy.

Everything works at REVIEW level: a review's category set is the union of its
chunks' findings. This is what lets us measure recall (missed aspects).
"""

from __future__ import annotations
import math
import itertools
import numpy as np
import pandas as pd
from scipy import stats as scipy_stats
from sklearn.metrics import cohen_kappa_score

from .prompts import CATEGORIES


# ---------------------------------------------------------------------------
# Confidence interval
# ---------------------------------------------------------------------------

def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion k/n. Returns (low, high)."""
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    half = (z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


# ---------------------------------------------------------------------------
# Convert annotations / model output to review-level dicts
# ---------------------------------------------------------------------------

def annotations_to_dict(long_df: pd.DataFrame) -> dict[str, dict[str, str]]:
    """long form (review_id, category, polarity) -> {review_id: {category: polarity}}."""
    out: dict[str, dict[str, str]] = {}
    for _, r in long_df.iterrows():
        out.setdefault(r["review_id"], {})[r["category"]] = r["polarity"]
    return out


def model_to_dict(raw_records: list[dict]) -> dict[str, dict[str, str]]:
    """
    Chunk-level model output -> {review_id: {category: polarity}}.
    A review's polarity per category: 'both' if it has both pos and neg findings,
    else the single polarity seen.
    """
    import json
    acc: dict[str, dict[str, set]] = {}
    for rec in raw_records:
        findings = rec.get("findings", [])
        if isinstance(findings, str):
            try:
                findings = json.loads(findings)
            except json.JSONDecodeError:
                continue
        rid = rec["review_id"]
        for f in findings:
            if not isinstance(f, dict):
                continue
            cat, pol = f.get("dimension"), f.get("polarity")
            if cat in CATEGORIES and pol in ("pos", "neg"):
                acc.setdefault(rid, {}).setdefault(cat, set()).add(pol)
    out: dict[str, dict[str, str]] = {}
    for rid, cats in acc.items():
        out[rid] = {
            cat: ("both" if pols == {"pos", "neg"} else next(iter(pols)))
            for cat, pols in cats.items()
        }
    return out


# ---------------------------------------------------------------------------
# Kappa with SE, z, p, and 95% CI (equivalent to SPSS Symmetric Measures)
# ---------------------------------------------------------------------------

def _kappa_stats(y1: list, y2: list) -> dict:
    """
    Compute Cohen's κ with asymptotic SE, z-statistic, two-tailed p-value,
    and 95% CI for one annotator pair.

    SE formula: Fleiss, Cohen & Everitt (1969) — the standard used by SPSS.
    H0: κ = 0 (agreement is no better than chance).
    """
    n = len(y1)
    if n == 0 or len(set(list(y1) + list(y2))) < 2:
        nan = float("nan")
        return {"kappa": nan, "SE": nan, "z": nan, "p": nan, "CI95_lo": nan, "CI95_hi": nan, "n": n}

    k = cohen_kappa_score(y1, y2)

    # marginal proportions
    labels = sorted(set(list(y1) + list(y2)))
    p_i = np.array([y1.count(l) / n for l in labels])   # rater 1 marginals
    p_j = np.array([y2.count(l) / n for l in labels])   # rater 2 marginals
    p_e = float(np.dot(p_i, p_j))                        # expected agreement

    # asymptotic SE (Fleiss et al. 1969)
    if p_e == 1.0:
        se = float("nan")
    else:
        se = math.sqrt((p_e + p_e**2 - sum(
            (p_i[idx] + p_j[idx]) * p_i[idx] * p_j[idx] for idx in range(len(labels))
        )) / (n * (1 - p_e)**2))

    z = k / se if (se and not math.isnan(se)) else float("nan")
    p = float(2 * (1 - scipy_stats.norm.cdf(abs(z)))) if not math.isnan(z) else float("nan")
    ci_lo = k - 1.96 * se if not math.isnan(se) else float("nan")
    ci_hi = k + 1.96 * se if not math.isnan(se) else float("nan")

    return {
        "kappa":   round(k, 3),
        "SE":      round(se, 4) if not math.isnan(se) else float("nan"),
        "z":       round(z, 3)  if not math.isnan(z)  else float("nan"),
        "p":       round(p, 4)  if not math.isnan(p)  else float("nan"),
        "CI95_lo": round(ci_lo, 3) if not math.isnan(ci_lo) else float("nan"),
        "CI95_hi": round(ci_hi, 3) if not math.isnan(ci_hi) else float("nan"),
        "n": n,
    }


# ---------------------------------------------------------------------------
# Inter-annotator agreement (3 annotators, pairwise Cohen's κ)
# ---------------------------------------------------------------------------

def kappa_detection(
    ann1: dict[str, dict[str, str]],
    ann2: dict[str, dict[str, str]],
    ann3: dict[str, dict[str, str]],
    review_ids: list[str],
    categories: list[str] = CATEGORIES,
) -> pd.DataFrame:
    """
    Pairwise Cohen's kappa on category DETECTION (present/absent) for 3 annotators.
    Returns per-category and overall kappas with SE, z, p, and 95% CI for each pair,
    plus the mean kappa — equivalent to SPSS Symmetric Measures table.
    """
    annotators = [ann1, ann2, ann3]
    pairs = list(itertools.combinations(range(3), 2))
    pair_labels = ["1v2", "1v3", "2v3"]

    rows = []
    for cat in categories:
        vecs = [
            [int(cat in ann.get(rid, {})) for rid in review_ids]
            for ann in annotators
        ]
        row: dict = {"category": cat}
        kappa_vals = []
        for (i, j), label in zip(pairs, pair_labels):
            s = _kappa_stats(vecs[i], vecs[j])
            row[f"κ_{label}"]      = s["kappa"]
            row[f"SE_{label}"]     = s["SE"]
            row[f"z_{label}"]      = s["z"]
            row[f"p_{label}"]      = s["p"]
            row[f"CI95_{label}"]   = f"[{s['CI95_lo']}, {s['CI95_hi']}]"
            if not math.isnan(s["kappa"]):
                kappa_vals.append(s["kappa"])
        row["κ_rata2"]   = round(np.mean(kappa_vals), 3) if kappa_vals else float("nan")
        row["n_pos_a1"]  = sum(vecs[0])
        row["n_pos_a2"]  = sum(vecs[1])
        row["n_pos_a3"]  = sum(vecs[2])
        rows.append(row)

    # Overall row (flatten all category vectors)
    all_vecs = [
        [int(cat in ann.get(rid, {})) for rid in review_ids for cat in categories]
        for ann in annotators
    ]
    overall_row: dict = {"category": "(KESELURUHAN)"}
    kappa_vals = []
    for (i, j), label in zip(pairs, pair_labels):
        s = _kappa_stats(all_vecs[i], all_vecs[j])
        overall_row[f"κ_{label}"]    = s["kappa"]
        overall_row[f"SE_{label}"]   = s["SE"]
        overall_row[f"z_{label}"]    = s["z"]
        overall_row[f"p_{label}"]    = s["p"]
        overall_row[f"CI95_{label}"] = f"[{s['CI95_lo']}, {s['CI95_hi']}]"
        if not math.isnan(s["kappa"]):
            kappa_vals.append(s["kappa"])
    overall_row["κ_rata2"]  = round(np.mean(kappa_vals), 3) if kappa_vals else float("nan")
    overall_row["n_pos_a1"] = sum(all_vecs[0])
    overall_row["n_pos_a2"] = sum(all_vecs[1])
    overall_row["n_pos_a3"] = sum(all_vecs[2])
    rows.append(overall_row)

    return pd.DataFrame(rows)


def kappa_polarity(
    ann1: dict[str, dict[str, str]],
    ann2: dict[str, dict[str, str]],
    ann3: dict[str, dict[str, str]],
    review_ids: list[str],
    categories: list[str] = CATEGORIES,
) -> pd.DataFrame:
    """
    Pairwise Cohen's kappa on polarity over (review, category) items BOTH annotators marked.
    Returns a DataFrame with κ, SE, z, p, 95% CI for each pair plus the mean kappa.
    Equivalent to SPSS Symmetric Measures table.
    """
    annotators = [ann1, ann2, ann3]
    pairs = list(itertools.combinations(range(3), 2))
    pair_labels = ["1v2", "1v3", "2v3"]

    rows = []
    kappa_vals = []
    for (i, j), label in zip(pairs, pair_labels):
        p_i, p_j = [], []
        for rid in review_ids:
            for cat in categories:
                if cat in annotators[i].get(rid, {}) and cat in annotators[j].get(rid, {}):
                    p_i.append(annotators[i][rid][cat])
                    p_j.append(annotators[j][rid][cat])
        s = _kappa_stats(p_i, p_j)
        rows.append({
            "pasangan":  label,
            "n_item":    s["n"],
            "kappa":     s["kappa"],
            "SE":        s["SE"],
            "z":         s["z"],
            "p":         s["p"],
            "CI95":      f"[{s['CI95_lo']}, {s['CI95_hi']}]",
        })
        if not math.isnan(s["kappa"]):
            kappa_vals.append(s["kappa"])

    rows.append({
        "pasangan": "(rata2)",
        "n_item":   "",
        "kappa":    round(np.mean(kappa_vals), 3) if kappa_vals else float("nan"),
        "SE": "", "z": "", "p": "", "CI95": "",
    })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Adjudication (3 annotators → majority vote)
# ---------------------------------------------------------------------------

def disagreements(
    ann1: dict[str, dict[str, str]],
    ann2: dict[str, dict[str, str]],
    ann3: dict[str, dict[str, str]],
    review_ids: list[str],
    categories: list[str] = CATEGORIES,
) -> pd.DataFrame:
    """
    Table of every (review, category) where the three annotators do NOT all agree.
    Includes a 'kesepakatan' column: '2/3' when two agree, '0/3' when all differ.
    """
    rows = []
    for rid in review_ids:
        for cat in categories:
            a = ann1.get(rid, {}).get(cat, "")
            b = ann2.get(rid, {}).get(cat, "")
            c = ann3.get(rid, {}).get(cat, "")
            if a == b == c:
                continue
            # find majority if any two agree
            if a == b:
                kesepakatan, majority = "2/3 (A1+A2)", a
            elif a == c:
                kesepakatan, majority = "2/3 (A1+A3)", a
            elif b == c:
                kesepakatan, majority = "2/3 (A2+A3)", b
            else:
                kesepakatan, majority = "0/3", ""
            rows.append({
                "review_id": rid, "category": cat,
                "anotator_1": a or "(kosong)",
                "anotator_2": b or "(kosong)",
                "anotator_3": c or "(kosong)",
                "kesepakatan": kesepakatan,
                "mayoritas": majority or "(tidak ada)",
                "keputusan": "",   # kolom untuk diisi manual jika 0/3
            })
    return pd.DataFrame(rows, columns=[
        "review_id", "category",
        "anotator_1", "anotator_2", "anotator_3",
        "kesepakatan", "mayoritas", "keputusan",
    ])


# ---------------------------------------------------------------------------
# Scoring model vs gold
# ---------------------------------------------------------------------------

def score_detection(
    gold: dict[str, dict[str, str]],
    pred: dict[str, dict[str, str]],
    review_ids: list[str],
    categories: list[str] = CATEGORIES,
) -> pd.DataFrame:
    """Per-category detection precision/recall/F1 with Wilson CIs, plus micro & macro rows."""
    rows = []
    tot_tp = tot_fp = tot_fn = 0
    macro_f1s = []
    for cat in categories:
        tp = sum(1 for rid in review_ids if cat in gold.get(rid, {}) and cat in pred.get(rid, {}))
        fp = sum(1 for rid in review_ids if cat not in gold.get(rid, {}) and cat in pred.get(rid, {}))
        fn = sum(1 for rid in review_ids if cat in gold.get(rid, {}) and cat not in pred.get(rid, {}))
        support = tp + fn

        if support == 0 and (tp + fp) == 0:
            prec = rec = f1 = float("nan")
        else:
            prec = tp / (tp + fp) if (tp + fp) else 0.0
            rec = tp / support if support else 0.0
            f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
            if support > 0:
                macro_f1s.append(f1)

        rlo, rhi = wilson_ci(tp, support)
        rows.append({
            "category": cat, "support": support, "TP": tp, "FP": fp, "FN": fn,
            "precision": round(prec, 3) if not math.isnan(prec) else float("nan"),
            "recall": round(rec, 3) if not math.isnan(rec) else float("nan"),
            "F1": round(f1, 3) if not math.isnan(f1) else float("nan"),
            "recall_CI95": f"[{rlo:.2f}, {rhi:.2f}]" if support else "",
        })
        tot_tp += tp; tot_fp += fp; tot_fn += fn

    micro_p = tot_tp / (tot_tp + tot_fp) if (tot_tp + tot_fp) else float("nan")
    micro_r = tot_tp / (tot_tp + tot_fn) if (tot_tp + tot_fn) else float("nan")
    micro_f1 = 2 * micro_p * micro_r / (micro_p + micro_r) if (micro_p + micro_r) else float("nan")
    macro_f1 = np.mean(macro_f1s) if macro_f1s else float("nan")

    rows.append({"category": "(MICRO)", "support": tot_tp + tot_fn, "TP": tot_tp, "FP": tot_fp,
                 "FN": tot_fn, "precision": round(micro_p, 3), "recall": round(micro_r, 3),
                 "F1": round(micro_f1, 3), "recall_CI95": ""})
    rows.append({"category": "(MACRO)", "support": "", "TP": "", "FP": "", "FN": "",
                 "precision": "", "recall": "", "F1": round(macro_f1, 3), "recall_CI95": ""})
    return pd.DataFrame(rows)


def polarity_accuracy(
    gold: dict[str, dict[str, str]],
    pred: dict[str, dict[str, str]],
    review_ids: list[str],
    categories: list[str] = CATEGORIES,
) -> tuple[float, int]:
    """Polarity accuracy over (review, category) pairs BOTH gold and model detected. Returns (acc, n)."""
    correct = total = 0
    for rid in review_ids:
        for cat in categories:
            if cat in gold.get(rid, {}) and cat in pred.get(rid, {}):
                total += 1
                if gold[rid][cat] == pred[rid][cat]:
                    correct += 1
    return (correct / total if total else float("nan"), total)


def error_table(
    gold: dict[str, dict[str, str]],
    pred: dict[str, dict[str, str]],
    review_ids: list[str],
    categories: list[str] = CATEGORIES,
) -> pd.DataFrame:
    """Every model error tagged by type: terlewat (FN), berlebih (FP), polaritas_salah."""
    rows = []
    for rid in review_ids:
        g, p = gold.get(rid, {}), pred.get(rid, {})
        for cat in categories:
            in_g, in_p = cat in g, cat in p
            if in_g and not in_p:
                rows.append({"review_id": rid, "category": cat, "tipe": "terlewat",
                             "gold": g[cat], "model": "-"})
            elif in_p and not in_g:
                rows.append({"review_id": rid, "category": cat, "tipe": "berlebih",
                             "gold": "-", "model": p[cat]})
            elif in_g and in_p and g[cat] != p[cat]:
                rows.append({"review_id": rid, "category": cat, "tipe": "polaritas_salah",
                             "gold": g[cat], "model": p[cat]})
    return pd.DataFrame(rows, columns=["review_id", "category", "tipe", "gold", "model"])


def bootstrap_macro_f1(
    gold: dict[str, dict[str, str]],
    pred: dict[str, dict[str, str]],
    review_ids: list[str],
    categories: list[str] = CATEGORIES,
    n_boot: int = 1000,
    seed: int = 42,
) -> tuple[float, float]:
    """95% bootstrap CI for macro-F1 by resampling reviews with replacement."""
    rng = np.random.RandomState(seed)
    ids = np.array(review_ids)
    scores = []
    for _ in range(n_boot):
        sample_ids = list(rng.choice(ids, size=len(ids), replace=True))
        df = score_detection(gold, pred, sample_ids, categories)
        macro = df.loc[df["category"] == "(MACRO)", "F1"].iloc[0]
        if not (isinstance(macro, float) and math.isnan(macro)):
            scores.append(macro)
    if not scores:
        return (float("nan"), float("nan"))
    return (round(np.percentile(scores, 2.5), 3), round(np.percentile(scores, 97.5), 3))
