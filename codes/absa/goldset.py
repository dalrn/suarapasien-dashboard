"""
Gold-standard sample construction and annotation-template writer.

The sample is stratified to OVERSAMPLE failure regions, not drawn uniformly:
random sampling would be dominated by easy "antri lama" cases and tell us
nothing about the hard ones. We deliberately balance across:
  - wilayah (Surabaya / Semarang / Bantul)
  - panjang teks (pendek / sedang / panjang) — short reviews carry global sentiment
  - rating (1 vs 2) — 2-star reviews are more ambiguous than 1-star

Allocation uses sqrt-proportional weighting (between uniform and proportional),
which lifts rare-but-hard strata above their natural frequency.

Templates are written as .xlsx (openpyxl) so annotators can open directly in
Excel without encoding issues on Indonesian text.
"""

from __future__ import annotations
import numpy as np
import pandas as pd

from .prompts import CATEGORIES

# Columns the annotator fills: one polarity cell per category.
# Allowed values: "neg", "pos", "both" (both polarities present), or "" (absent).
ANNOTATION_COLUMNS = CATEGORIES
META_COLUMNS = ["review_id", "wilayah", "rating", "stratum", "review_text"]


# ---------------------------------------------------------------------------
# Stratification
# ---------------------------------------------------------------------------

def _length_bucket(n: int) -> str:
    if n < 50:
        return "pendek"
    if n <= 200:
        return "sedang"
    return "panjang"


def build_sample(
    df: pd.DataFrame,
    n_total: int = 200,
    seed: int = 42,
    exclude_ids: set[str] | None = None,
) -> pd.DataFrame:
    """
    Return a stratified gold-set sample of ~n_total reviews.
    Adds a 'stratum' column documenting which cell each review came from.

    exclude_ids: review_ids to drop before sampling — used to build a held-out
    TEST set that does not overlap the training/dev gold set. Same stratification
    so the two sets are comparable.
    """
    df = df.copy()
    if exclude_ids:
        df = df[~df["review_id"].astype(str).isin(set(exclude_ids))]
    df["_len_bucket"] = df["text_length"].apply(_length_bucket)
    df["stratum"] = (
        df["wilayah"] + " | " + df["_len_bucket"] + " | " + df["rating"].astype(str) + "★"
    )

    sizes = df.groupby("stratum").size()

    # sqrt-proportional allocation: flatter than proportional, so rare strata
    # (e.g. short 2-star Bantul reviews) get lifted above their natural share.
    weights = np.sqrt(sizes)
    alloc = (weights / weights.sum() * n_total).round().astype(int)
    alloc = alloc.clip(upper=sizes)          # never ask for more than a stratum has
    alloc = alloc.clip(lower=1)              # guarantee every stratum is represented

    rng = np.random.RandomState(seed)
    parts = []
    for stratum, k in alloc.items():
        pool = df[df["stratum"] == stratum]
        k = min(k, len(pool))
        parts.append(pool.sample(k, random_state=rng))

    sample = (
        pd.concat(parts)
        .drop(columns=["_len_bucket"])
        .sample(frac=1, random_state=seed)   # shuffle so annotators don't see strata grouped
        .reset_index(drop=True)
    )
    return sample


# ---------------------------------------------------------------------------
# Annotation template (Excel .xlsx)
# ---------------------------------------------------------------------------

def write_template(sample: pd.DataFrame, out_path: str) -> None:
    """
    Write an empty annotation template as .xlsx (openpyxl).
    One row per review; annotator fills the category columns with neg/pos/both.
    Column widths are set so the file is immediately usable in Excel.
    """
    cols = META_COLUMNS + list(ANNOTATION_COLUMNS)
    rows = []
    for _, r in sample.iterrows():
        row = {col: r[col] if col in r.index else "" for col in META_COLUMNS}
        for cat in ANNOTATION_COLUMNS:
            row[cat] = ""
        rows.append(row)

    df_out = pd.DataFrame(rows, columns=cols)

    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        df_out.to_excel(writer, index=False, sheet_name="Anotasi")
        ws = writer.sheets["Anotasi"]

        # set column widths: review_text wide, category columns narrow
        col_widths = {
            "review_id": 14, "wilayah": 12, "rating": 8,
            "stratum": 28, "review_text": 60,
        }
        for cat in ANNOTATION_COLUMNS:
            col_widths[cat] = 16

        for i, col_name in enumerate(cols, start=1):
            ws.column_dimensions[
                ws.cell(row=1, column=i).column_letter
            ].width = col_widths.get(col_name, 14)

        # freeze the header row and the first two columns so annotator can scroll
        ws.freeze_panes = "C2"


def load_annotations(path: str) -> pd.DataFrame:
    """
    Load a completed annotation file (.xlsx or .csv) into long form:
    one row per (review_id, category) where the annotator marked a polarity.
    Normalises blank/whitespace to absent.
    """
    path = str(path)
    if path.endswith(".xlsx"):
        df = pd.read_excel(path, sheet_name="Anotasi", dtype=str).fillna("")
    else:
        df = pd.read_csv(path, encoding="utf-8-sig", dtype=str).fillna("")

    rows = []
    for _, r in df.iterrows():
        for cat in ANNOTATION_COLUMNS:
            val = str(r.get(cat, "")).strip().lower()
            if val in ("pos", "neg", "both"):
                rows.append({"review_id": r["review_id"], "category": cat, "polarity": val})
    return pd.DataFrame(rows, columns=["review_id", "category", "polarity"])


# ---------------------------------------------------------------------------
# FULL-DATASET manual labeling (dimension + polarity + sub_issue + quote)
# ---------------------------------------------------------------------------
# Unlike the gold-set template above (one polarity cell per category, for
# evaluation), this template captures the SAME shape as the model output so
# manual labels can be merged straight into findings_full.csv. The dashboard's
# "sumber komplain" + "lihat ulasan asli" features depend on sub_issue & quote.

# Columns the annotator fills, one ROW PER FINDING. A review with no service
# content gets a single row with all four blank.
FINDING_COLUMNS = ["dimension", "polarity", "sub_issue", "quote"]
LABEL_META_COLUMNS = ["review_id", "puskesmas_id", "puskesmas_name", "wilayah", "rating", "review_text"]


def write_label_template(
    reviews: pd.DataFrame, out_path: str, blank_rows_per_review: int = 3
) -> None:
    """
    Write a full-label template (.xlsx) for manual extraction matching the model
    output. For each review: one pre-filled meta row plus `blank_rows_per_review`
    empty finding-rows (dimension / polarity / sub_issue / quote) for the
    annotator to fill. Meta columns repeat the review_id so rows stay linked;
    only the first row of each review shows the review_text (to reduce clutter).

    Annotator instructions (also in the notebook guide):
      - dimension: one of Responsiveness/Reliability/Assurance/Empathy/Tangibles/Umum
      - polarity:  neg / pos
      - sub_issue: short Indonesian noun phrase (2-5 words), e.g. "antre lama"
      - quote:     verbatim span copied from review_text
      - If a review has more findings than blank rows, add rows (keep same review_id).
      - If a review has NO service content (off-topic / pure inquiry), leave one row
        with review_id filled and the four finding columns blank.
    """
    cols = LABEL_META_COLUMNS + FINDING_COLUMNS
    rows = []
    for _, r in reviews.iterrows():
        for k in range(blank_rows_per_review):
            row = {c: "" for c in cols}
            row["review_id"] = r["review_id"]
            if k == 0:
                # show full meta only on the first row of each review block
                for c in LABEL_META_COLUMNS:
                    row[c] = r[c] if c in r.index else ""
            else:
                row["review_id"] = r["review_id"]   # keep link, blank the rest
            rows.append(row)

    df_out = pd.DataFrame(rows, columns=cols)

    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        df_out.to_excel(writer, index=False, sheet_name="Label")
        ws = writer.sheets["Label"]
        widths = {
            "review_id": 26, "puskesmas_id": 14, "puskesmas_name": 22,
            "wilayah": 12, "rating": 7, "review_text": 70,
            "dimension": 16, "polarity": 9, "sub_issue": 28, "quote": 50,
        }
        for i, col_name in enumerate(cols, start=1):
            ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = widths.get(col_name, 14)
        ws.freeze_panes = "B2"


def load_label_template(path: str) -> pd.DataFrame:
    """
    Load a completed full-label template into model-compatible long form:
    one row per finding with columns review_id, dimension, polarity, sub_issue, quote.

    Rows where dimension/polarity are blank are dropped (they were just spare
    finding-rows or no-content markers). Whitespace is trimmed; dimension is
    title-cased to match CATEGORIES; polarity lower-cased.
    """
    path = str(path)
    if path.endswith(".xlsx"):
        df = pd.read_excel(path, sheet_name="Label", dtype=str).fillna("")
    else:
        df = pd.read_csv(path, encoding="utf-8-sig", dtype=str).fillna("")

    valid_dims = {c.lower(): c for c in CATEGORIES}
    out = []
    for _, r in df.iterrows():
        dim = str(r.get("dimension", "")).strip().lower()
        pol = str(r.get("polarity", "")).strip().lower()
        if dim not in valid_dims or pol not in ("neg", "pos"):
            continue   # blank/spare row or invalid entry → skip
        out.append({
            "review_id": str(r["review_id"]).strip(),
            "dimension": valid_dims[dim],
            "polarity": pol,
            "sub_issue": str(r.get("sub_issue", "")).strip(),
            "quote": str(r.get("quote", "")).strip(),
        })
    return pd.DataFrame(out, columns=["review_id", "dimension", "polarity", "sub_issue", "quote"])
