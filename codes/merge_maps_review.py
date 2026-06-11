"""
SuaraPasien — Konsolidasi Master Dataset
Menggabungkan semua CSV puskesmas dari 3 folder (Bantul, Surabaya, Semarang)
menjadi satu master dataset dengan schema seragam.

Struktur folder yang diharapkan:
    data/
    ├── Bantul/
    │   ├── Puskesmas Bambanglipuro.csv     ← dengan spasi
    │   └── ...
    ├── Surabaya/
    │   ├── PuskesmasAsemrowo.csv           ← tanpa spasi
    │   └── ...
    └── Semarang/
        └── ...

Schema input (per file CSV):
    title, url, stars, name, reviewUrl, text

Schema output (master file):
    review_id              — unique ID per review (generated)
    puskesmas_id           — format PKM_{WILAYAH}_{NNN}
    puskesmas_name         — nama puskesmas (dari nama file)
    puskesmas_title        — title dari Google Maps (dari kolom title)
    wilayah                — Bantul / Surabaya / Semarang
    rating                 — 1-5 (dari kolom stars)
    review_text            — teks ulasan (dari kolom text)
    reviewer_name          — nama reviewer (dari kolom name)
    review_url             — URL ulasan (dari kolom reviewUrl)
    puskesmas_url          — URL puskesmas (dari kolom url)
    source_file            — nama file asal

Usage:
    python consolidate.py

Output:
    data/master/reviews_all.csv      — master dataset
    data/master/puskesmas_summary.csv — ringkasan per puskesmas
    data/master/consolidation_log.txt — log proses & warning
"""

import os
import re
import sys
import hashlib
import pandas as pd
from pathlib import Path
from datetime import datetime

# ── Konfigurasi ──
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
BASE_DIR = os.path.join(PROJECT_ROOT, "data")
WILAYAH_FOLDERS = ["Bantul", "Surabaya", "Semarang"]
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data")
OUTPUT_REVIEWS = os.path.join(OUTPUT_DIR, "reviews_all.csv")
OUTPUT_SUMMARY = os.path.join(OUTPUT_DIR, "puskesmas_summary.csv")
OUTPUT_LOG = os.path.join(OUTPUT_DIR, "consolidation_log.txt")


# Schema yang diharapkan dari input
EXPECTED_COLUMNS = {"title", "url", "stars", "name", "reviewUrl", "text"}

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Logger sederhana ──
log_messages = []

def log(msg, level="INFO"):
    line = f"[{level}] {msg}"
    print(line)
    log_messages.append(line)


def extract_puskesmas_name(filename: str, wilayah: str) -> str:
    """
    Extract nama puskesmas dari nama file.
    
    Bantul/Semarang: "Puskesmas Bambanglipuro.csv" → "Bambanglipuro"
    Surabaya:        "PuskesmasAsemrowo.csv"        → "Asemrowo"
    """
    # Hilangkan extension
    name = filename.replace(".csv", "")
    
    # Hilangkan prefix "Puskesmas" (dengan atau tanpa spasi)
    # Pattern: "Puskesmas " atau "Puskesmas"
    name = re.sub(r"^Puskesmas\s*", "", name, flags=re.IGNORECASE)
    
    # Untuk Surabaya yang CamelCase ("KrembanganSelatan"), 
    # split jadi "Krembangan Selatan" supaya konsisten
    if wilayah == "Surabaya":
        # Insert space before capital letter (kecuali yang pertama)
        # Misal: "KrembanganSelatan" → "Krembangan Selatan"
        # Tapi "DrSoetomo" tetap problematic — skip kalau diawali huruf kecil setelah Dr
        name = re.sub(r"(?<!^)(?=[A-Z])", " ", name)
    
    return name.strip()


def make_puskesmas_id(wilayah: str, idx: int) -> str:
    """Generate puskesmas_id dengan format PKM_{WILAYAH}_{NNN}."""
    wilayah_codes = {"Bantul": "BTL", "Surabaya": "SBY", "Semarang": "SMG"}
    code = wilayah_codes.get(wilayah, wilayah[:3].upper())
    return f"PKM_{code}_{idx:03d}"


def make_review_id(puskesmas_id: str, idx: int, text: str) -> str:
    """Generate unique review_id yang stable (sama jika di-run ulang)."""
    # Hash dari kombinasi puskesmas_id + idx + 50 char pertama text
    text_snippet = (str(text)[:50] if pd.notna(text) else "")
    raw = f"{puskesmas_id}_{idx}_{text_snippet}"
    h = hashlib.md5(raw.encode("utf-8")).hexdigest()[:8]
    return f"{puskesmas_id}_R{idx:04d}_{h}"


def load_one_csv(filepath: Path, wilayah: str, puskesmas_id: str, puskesmas_name: str) -> pd.DataFrame:
    """Load satu CSV puskesmas dan standardisasi schema."""
    try:
        df = pd.read_csv(filepath, encoding="utf-8")
    except UnicodeDecodeError:
        # Fallback ke encoding lain
        try:
            df = pd.read_csv(filepath, encoding="latin-1")
            log(f"  ⚠ {filepath.name}: pakai encoding latin-1 (bukan utf-8)", "WARN")
        except Exception as e:
            log(f"  ✗ {filepath.name}: gagal baca file — {e}", "ERROR")
            return pd.DataFrame()
    except Exception as e:
        log(f"  ✗ {filepath.name}: gagal baca file — {e}", "ERROR")
        return pd.DataFrame()

    # Cek kolom
    actual_cols = set(df.columns)
    missing_cols = EXPECTED_COLUMNS - actual_cols
    extra_cols = actual_cols - EXPECTED_COLUMNS

    if missing_cols:
        log(f"  ⚠ {filepath.name}: kolom hilang {missing_cols}", "WARN")
    if extra_cols:
        log(f"  ℹ {filepath.name}: kolom extra {extra_cols} (akan diabaikan)", "INFO")

    # Standardisasi: pakai .get() supaya tidak error kalau kolom hilang
    n_rows = len(df)
    standardized = pd.DataFrame({
        "review_id": [make_review_id(puskesmas_id, i, df["text"].iloc[i] if "text" in df.columns and i < len(df) else "") 
                      for i in range(n_rows)],
        "puskesmas_id": [puskesmas_id] * n_rows,
        "puskesmas_name": [puskesmas_name] * n_rows,
        "puskesmas_title": df["title"] if "title" in df.columns else [None] * n_rows,
        "wilayah": [wilayah] * n_rows,
        "rating": pd.to_numeric(df["stars"], errors="coerce") if "stars" in df.columns else [None] * n_rows,
        "review_text": df["text"] if "text" in df.columns else [None] * n_rows,
        "reviewer_name": df["name"] if "name" in df.columns else [None] * n_rows,
        "review_url": df["reviewUrl"] if "reviewUrl" in df.columns else [None] * n_rows,
        "puskesmas_url": df["url"] if "url" in df.columns else [None] * n_rows,
        "source_file": [filepath.name] * n_rows,
    })

    return standardized


def main():
    log("=" * 70)
    log(f"KONSOLIDASI MASTER DATASET — {datetime.now().isoformat()}")
    log("=" * 70)

    base_path = Path(BASE_DIR)
    if not base_path.exists():
        log(f"ERROR: Folder '{BASE_DIR}' tidak ditemukan", "ERROR")
        sys.exit(1)

    all_dfs = []
    puskesmas_idx = {w: 0 for w in WILAYAH_FOLDERS}

    for wilayah in WILAYAH_FOLDERS:
        wilayah_path = base_path / wilayah
        if not wilayah_path.exists():
            log(f"⚠ Folder '{wilayah_path}' tidak ada, skip", "WARN")
            continue

        log(f"\n— Memproses wilayah: {wilayah} —")
        csv_files = sorted(wilayah_path.glob("*.csv"))
        log(f"  Ditemukan {len(csv_files)} file CSV")

        for filepath in csv_files:
            puskesmas_idx[wilayah] += 1
            puskesmas_id = make_puskesmas_id(wilayah, puskesmas_idx[wilayah])
            puskesmas_name = extract_puskesmas_name(filepath.name, wilayah)

            df = load_one_csv(filepath, wilayah, puskesmas_id, puskesmas_name)
            if not df.empty:
                all_dfs.append(df)
                log(f"  ✓ {filepath.name:50s} → {puskesmas_id} | {puskesmas_name:30s} | {len(df):5d} reviews")

    if not all_dfs:
        log("ERROR: Tidak ada data berhasil di-load", "ERROR")
        sys.exit(1)

    # ── Gabungkan ──
    log(f"\n— Menggabungkan {len(all_dfs)} dataframe —")
    master = pd.concat(all_dfs, ignore_index=True)
    log(f"  Total rows mentah: {len(master):,}")

    # # ── Deduplication ──
    # log("\n— Deduplication —")
    # n_before = len(master)
    # # Drop berdasarkan kombinasi puskesmas_id + review_text (jaga-jaga ada double scrape)
    # master = master.drop_duplicates(subset=["puskesmas_id", "review_text"], keep="first")
    # n_after = len(master)
    # if n_before > n_after:
    #     log(f"  Drop {n_before - n_after} duplicate exact text", "INFO")
    # else:
    #     log(f"  Tidak ada duplicate exact", "INFO")

    # ── Quality flags ──
    log("\n— Adding quality flags —")
    master["text_length"] = master["review_text"].astype(str).str.len()
    master["is_empty_text"] = master["review_text"].isna() | (master["text_length"] == 0)
    master["is_very_short"] = master["text_length"] < 20
    master["has_rating"] = master["rating"].notna()
    log(f"  Empty text: {master['is_empty_text'].sum()}")
    log(f"  Very short (<20 char): {master['is_very_short'].sum()}")
    log(f"  Missing rating: {(~master['has_rating']).sum()}")

    # ── Save master file ──
    master.to_csv(OUTPUT_REVIEWS, index=False, encoding="utf-8")
    log(f"\n✓ Master dataset tersimpan: {OUTPUT_REVIEWS} ({len(master):,} rows)")

    # ── Generate summary per puskesmas ──
    log("\n— Membuat ringkasan per puskesmas —")
    summary = master.groupby(["puskesmas_id", "wilayah", "puskesmas_name", "puskesmas_title"]).agg(
        n_reviews=("review_id", "count"),
        n_empty=("is_empty_text", "sum"),
        n_very_short=("is_very_short", "sum"),
        n_with_rating=("has_rating", "sum"),
        rating_mean=("rating", "mean"),
        rating_median=("rating", "median"),
        rating_std=("rating", "std"),
        text_length_mean=("text_length", "mean"),
        text_length_median=("text_length", "median"),
    ).round(2).reset_index()

    # Sort by wilayah lalu puskesmas_id
    summary = summary.sort_values(["wilayah", "puskesmas_id"]).reset_index(drop=True)
    summary.to_csv(OUTPUT_SUMMARY, index=False, encoding="utf-8")
    log(f"✓ Summary per puskesmas: {OUTPUT_SUMMARY} ({len(summary)} puskesmas)")

    # ── Ringkasan akhir ──
    log("\n" + "=" * 70)
    log("RINGKASAN")
    log("=" * 70)
    log(f"Total puskesmas    : {len(summary)}")
    log(f"Total reviews      : {len(master):,}")
    log(f"\nPer wilayah:")
    for w in WILAYAH_FOLDERS:
        sub = summary[summary["wilayah"] == w]
        sub_reviews = master[master["wilayah"] == w]
        if len(sub) > 0:
            log(f"  {w:10s}: {len(sub):3d} puskesmas, {len(sub_reviews):,} reviews "
                f"(rata-rata {sub['n_reviews'].mean():.0f}/puskesmas)")

    log(f"\nDistribusi rating global:")
    if master["rating"].notna().any():
        for r in sorted(master["rating"].dropna().unique()):
            n = (master["rating"] == r).sum()
            pct = n / master["rating"].notna().sum() * 100
            log(f"  Rating {int(r)}: {n:6,} ({pct:5.1f}%)")

    log(f"\nDistribusi panjang teks:")
    log(f"  Median  : {master['text_length'].median():.0f} karakter")
    log(f"  Mean    : {master['text_length'].mean():.0f} karakter")
    log(f"  Max     : {master['text_length'].max():.0f} karakter")
    log(f"  >100 chr: {(master['text_length'] > 100).sum():,} ({(master['text_length'] > 100).mean()*100:.1f}%)")
    log(f"  >300 chr: {(master['text_length'] > 300).sum():,} ({(master['text_length'] > 300).mean()*100:.1f}%)")

    # ── Save log ──
    with open(OUTPUT_LOG, "w", encoding="utf-8") as f:
        f.write("\n".join(log_messages))
    log(f"\n✓ Log: {OUTPUT_LOG}")


if __name__ == "__main__":
    main()