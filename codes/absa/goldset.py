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
