"""Pemuat data (ber-cache) untuk dashboard SuaraPasien."""
import json
from pathlib import Path
import pandas as pd
import streamlit as st

from lib.theme import DIM_ORDER

ROOT = Path(__file__).resolve().parents[2]      # .../codes
OUT = ROOT / "outputs"
DATA = ROOT.parent / "data"


@st.cache_data
def load_profiles() -> dict:
    return json.loads((OUT / "puskesmas_profiles.json").read_text(encoding="utf-8"))


@st.cache_data
def load_topik() -> dict:
    return json.loads((OUT / "topik_kabupaten.json").read_text(encoding="utf-8"))


@st.cache_data
def load_gmaps_meta() -> dict:
    """Per-puskesmas: rata-rata bintang, jumlah ulasan, distribusi bintang, URL Maps."""
    df = pd.read_csv(DATA / "reviews_all.csv",
                     usecols=["puskesmas_id", "rating", "puskesmas_url"])
    meta = {}
    for pid, g in df.groupby("puskesmas_id"):
        dist = g["rating"].value_counts().reindex([1, 2, 3, 4, 5], fill_value=0)
        url = g["puskesmas_url"].dropna()
        meta[pid] = {
            "avg": round(float(g["rating"].mean()), 2),
            "total": int(len(g)),
            "dist": {int(k): int(v) for k, v in dist.items()},
            "url": str(url.iloc[0]) if len(url) else "",
        }
    return meta


@st.cache_data
def load_isu_kanonik() -> pd.DataFrame:
    return pd.read_csv(OUT / "statistik" / "isu_kanonik_per_dimensi.csv")


@st.cache_data
def load_region_breakdown() -> dict:
    """
    Per wilayah: persen ulasan-keluhan yang menyebut tiap dimensi.
    Denominator = ulasan dengan >=1 keluhan di wilayah itu.
    """
    df = pd.read_csv(OUT / "findings_full.csv",
                     usecols=["review_id", "wilayah", "dimension", "polarity"])
    df = df[(df["polarity"] == "neg") & (df["dimension"].isin(DIM_ORDER))]
    out = {}
    for wil, g in df.groupby("wilayah"):
        total = g["review_id"].nunique()
        out[wil] = {dim: round(g[g["dimension"] == dim]["review_id"].nunique() / total * 100, 1)
                    for dim in DIM_ORDER}
    return out


@st.cache_data
def dataset_stats() -> dict:
    """Angka ringkas untuk Beranda."""
    prof = load_profiles()
    return {
        "n_puskesmas": len(prof),
        "n_wilayah": len({p["wilayah"] for p in prof.values()}),
    }


@st.cache_data
def compute_rankings() -> dict:
    """
    Konteks komparatif lintas-puskesmas (kunci agar dashboard terasa seperti alat):
      - per dimensi: rata-rata kabupaten + peringkat & persentil tiap puskesmas
      - keseluruhan: skor keluhan agregat + peringkat #X (1 = paling sedikit dikeluhkan)

    Persentil dim = fraksi puskesmas (yang cukup dinilai) dengan intensitas LEBIH RENDAH
    → "lebih sering dikeluhkan dari P% puskesmas lain".
    Peringkat & persentil hanya dihitung di antara puskesmas yang `cukup_dinilai`.
    """
    prof = load_profiles()

    # kumpulkan intensitas per dimensi (hanya yang cukup dinilai)
    per_dim: dict[str, list] = {d: [] for d in DIM_ORDER}
    for pid, p in prof.items():
        for d in DIM_ORDER:
            dd = p["dimensi"].get(d)
            if dd and dd.get("cukup_dinilai"):
                per_dim[d].append((pid, float(dd["intensitas_rate"])))

    dim_avg = {d: (sum(v for _, v in lst) / len(lst) if lst else 0.0) for d, lst in per_dim.items()}

    # peringkat & persentil per dimensi
    dim_rank: dict[str, dict] = {d: {} for d in DIM_ORDER}
    for d, lst in per_dim.items():
        n = len(lst)
        srt = sorted(lst, key=lambda x: x[1])           # naik: rendah → tinggi
        for idx, (pid, rate) in enumerate(srt):
            n_lower = sum(1 for _, r in lst if r < rate)
            dim_rank[d][pid] = {
                "rank": n - idx,                         # 1 = paling sering dikeluhkan
                "n": n,
                "pct_lebih_sering": round(n_lower / n * 100) if n else 0,
            }

    # skor keseluruhan = rata-rata intensitas antar dimensi yang cukup dinilai
    overall = {}
    for pid, p in prof.items():
        rates = [float(p["dimensi"][d]["intensitas_rate"])
                 for d in DIM_ORDER
                 if p["dimensi"].get(d) and p["dimensi"][d].get("cukup_dinilai")]
        overall[pid] = sum(rates) / len(rates) if rates else None

    rated = sorted([(pid, s) for pid, s in overall.items() if s is not None], key=lambda x: x[1])
    n_rated = len(rated)
    overall_rank = {}
    for idx, (pid, s) in enumerate(rated):
        overall_rank[pid] = {"rank": idx + 1, "n": n_rated, "skor": round(s, 3)}  # #1 = paling sedikit dikeluhkan

    return {"dim_avg": dim_avg, "dim_rank": dim_rank, "overall": overall_rank}
