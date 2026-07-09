"""SuaraPasien — Beranda. Entry script halaman utama penyambut dan gambaran umum data."""
import base64
from pathlib import Path

import pandas as pd
import streamlit as st
from lib.theme import setup, DIM_INFO, DIM_ORDER
from lib.data import dataset_stats, load_isu_kanonik

setup("Beranda")

_LOGO_PATH = Path(__file__).parent / "bubble_pulse.png"
_LOGO_B64 = base64.b64encode(_LOGO_PATH.read_bytes()).decode()

DIM_COLOR = {
    "Empathy": "#E76F51",
    "Responsiveness": "#2A9D8F",
    "Reliability": "#457B9D",
    "Assurance": "#E9C46A",
    "Tangibles": "#F4A261",
}

# ==========================================
# CUSTOM CSS
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    .reportview-container, .main, div, span, p {
        font-family: 'Inter', sans-serif;
    }

    .hero-container {
        text-align: center;
        padding: 20px 10px 6px 10px;
    }
    .hero-title {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 12px;
        font-size: 44px;
        font-weight: 700;
        color: #16202b;
        letter-spacing: -0.02em;
        margin-bottom: 8px;
    }
    .hero-title img {
        height: 48px;
        width: 48px;
        object-fit: contain;
    }
    .hero-sub {
        font-size: 15px;
        color: #64748b;
        max-width: 700px;
        margin: 0 auto;
        line-height: 1.6;
    }
    .hero-highlight {
        color: #d05a4e;
        font-weight: 600;
    }

    .stat-card {
        background: #ffffff;
        border-radius: 16px;
        padding: 20px 14px;
        box-shadow: 0 1px 3px rgba(16,32,48,.07);
        text-align: center;
        border-bottom: 3.5px solid #185FA5;
    }
    .stat-val {
        font-size: 32px;
        font-weight: 700;
        color: #16202b;
        line-height: 1;
        margin-bottom: 4px;
    }
    .stat-lbl {
        font-size: 12.5px;
        color: #64748b;
        font-weight: 500;
    }

    .section-title {
        font-size: 21px;
        font-weight: 700;
        color: #16202b;
        margin: 32px 0 4px 0;
        letter-spacing: -0.01em;
    }
    .section-sub {
        font-size: 13px;
        color: #64748b;
        margin: 0 0 16px 0;
        line-height: 1.5;
    }

    .step-card {
        background: #ffffff;
        border-radius: 14px;
        padding: 18px 18px;
        box-shadow: 0 1px 3px rgba(16,32,48,.07);
        height: 100%;
        border-top: 3px solid #cbd5e1;
    }
    .step-num {
        font-size: 11px;
        font-weight: 700;
        color: #185FA5;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 5px;
    }
    .step-title {
        font-size: 15px;
        font-weight: 600;
        color: #16202b;
        margin-bottom: 6px;
    }
    .step-desc {
        font-size: 12px;
        color: #64748b;
        line-height: 1.5;
    }

    /* kartu dimensi SERVQUAL — header berwarna + chip cluster */
    .sq-card {
        background: #ffffff;
        border-radius: 16px;
        padding: 18px 20px 16px;
        margin-bottom: 14px;
        box-shadow: 0 1px 3px rgba(16,32,48,.07);
        border-left: 5px solid var(--dim-color);
    }
    .sq-head {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        gap: 10px;
        margin-bottom: 2px;
    }
    .sq-term {
        font-size: 16px;
        font-weight: 700;
        color: var(--dim-color);
        letter-spacing: -0.01em;
    }
    .sq-label {
        font-size: 12.5px;
        font-weight: 500;
        color: #64748b;
    }
    .sq-pct {
        font-size: 13px;
        font-weight: 700;
        color: #16202b;
        white-space: nowrap;
    }
    .sq-pct span {
        font-size: 11px;
        font-weight: 500;
        color: #94a3b8;
    }
    .sq-chips {
        display: flex;
        flex-wrap: wrap;
        gap: 7px;
        margin-top: 12px;
    }
    .sq-chip {
        font-size: 11.5px;
        font-weight: 600;
        padding: 6px 12px;
        border-radius: 99px;
        background: color-mix(in srgb, var(--dim-color) 14%, white);
        color: var(--dim-color);
        white-space: nowrap;
    }
    .sq-chip b {
        font-weight: 700;
    }
    .sq-chip-more {
        background: #eef1f4;
        color: #64748b;
    }

    .note-box {
        background: #f8fafc;
        border-left: 4px solid #cbd5e1;
        padding: 18px 22px;
        border-radius: 0 14px 14px 0;
        margin-top: 10px;
    }
    .note-title {
        font-size: 13.5px;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .note-content {
        font-size: 12.5px;
        color: #475569;
        line-height: 1.6;
    }
    .note-list {
        margin: 8px 0 0 18px;
        padding: 0;
    }
    .note-box-warn {
        background: #fdf6ec;
        border-left: 4px solid #c98a2b;
    }
    .note-box-warn .note-title {
        color: #8a5a16;
    }
    .note-box-warn .note-content {
        color: #6b5436;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 1. HERO
# ==========================================
st.markdown(f"""
<div class="hero-container">
    <div class="hero-title"><img src="data:image/png;base64,{_LOGO_B64}" alt="SuaraPasien logo"> SuaraPasien</div>
    <div class="hero-sub">
        Platform analisis sentimen untuk pemantauan mutu puskesmas. Mengubah ulasan publik
        Google Maps menjadi <span class="hero-highlight">instrumen pelengkap evaluasi fasilitas kesehatan yang
        objektif dan faktual.</span>
    </div>
</div>
""", unsafe_allow_html=True)
st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

# ==========================================
# 2. STAT RINGKAS
# ==========================================
stats = dataset_stats()
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-val">{stats['n_puskesmas']}</div>
        <div class="stat-lbl">Puskesmas dianalisis</div>
    </div>
    """, unsafe_allow_html=True)
with c2:
    st.markdown(f"""
    <div class="stat-card" style="border-bottom-color:#0f766e;">
        <div class="stat-val">{stats['n_wilayah']}</div>
        <div class="stat-lbl">Wilayah terwakili</div>
    </div>
    """, unsafe_allow_html=True)
with c3:
    st.markdown(f"""
    <div class="stat-card" style="border-bottom-color:#d05a4e;">
        <div class="stat-val">8,641</div>
        <div class="stat-lbl">Ulasan keluhan dianalisis</div>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 3. PIPELINE
# ==========================================
st.markdown("<div class='section-title'>Bagaimana SuaraPasien bekerja?</div>", unsafe_allow_html=True)

step1, step2, step3 = st.columns(3)
with step1:
    st.markdown("""
    <div class="step-card">
        <div class="step-num">Langkah 1</div>
        <div class="step-title">Dengar</div>
        <div class="step-desc">Mengekstraksi narasi kritik, pengalaman, dan umpan balik masyarakat langsung dari ulasan puskesmas di Google Maps.</div>
    </div>
    """, unsafe_allow_html=True)
with step2:
    st.markdown("""
    <div class="step-card" style="border-top-color: #185FA5;">
        <div class="step-num">Langkah 2</div>
        <div class="step-title">Kelompokkan</div>
        <div class="step-desc">Memilah teks keluhan mentah ke klaster taksonomi mutu SERVQUAL dengan model bahasa, lalu menyatukan ribuan frasa menjadi isu umum.</div>
    </div>
    """, unsafe_allow_html=True)
with step3:
    st.markdown("""
    <div class="step-card" style="border-top-color: #2f9e6f;">
        <div class="step-num">Langkah 3</div>
        <div class="step-title">Tampilkan</div>
        <div class="step-desc">Menyajikan profil performa puskesmas, peta sebaran mutu, hingga titik kritis untuk rekomendasi kebijakan.</div>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 4. SERVQUAL — dimensi + isu kanonik teratas
# ==========================================
st.markdown("<div class='section-title'>Dimensi SERVQUAL</div>", unsafe_allow_html=True)
st.markdown(
    "<div class='section-sub'>Keluhan dipetakan ke lima dimensi dari framework <b> SERVICE QUALITY (SERVQUAL)</b>, lalu disatukan "
    "jadi beberapa isu utama per dimensi",
    unsafe_allow_html=True,
)

isu_df = load_isu_kanonik()
for key in DIM_ORDER:
    if key not in DIM_INFO:
        continue
    label, desc, _short = DIM_INFO[key]
    color = DIM_COLOR.get(key, "#185FA5")
    sub = isu_df[isu_df["dimensi"] == key].sort_values("n_ulasan", ascending=False)
    total = int(sub["n_ulasan"].sum())
    top = sub.head(4)
    rest = sub.iloc[4:]
    chips = "".join(
        f"<span class='sq-chip'>{r.isu_kanonik.title()} <b>{int(r.n_ulasan)}</b></span>"
        for r in top.itertuples()
    )
    if len(rest):
        n_rest_clusters = len(rest)
        n_rest_reviews = int(rest["n_ulasan"].sum())
        chips += (
            f"<span class='sq-chip sq-chip-more'><b>{n_rest_clusters}</b> isu lainnya "
            f"<b>{n_rest_reviews}</b></span>"
        )
    st.markdown(f"""
    <div class="sq-card" style="--dim-color:{color};">
        <div class="sq-head">
            <div><span class="sq-term">{key}</span> &nbsp;<span class="sq-label">{label}</span></div>
            <div class="sq-pct">{total:,} <span>keluhan</span></div>
        </div>
        <div class="sq-chips">{chips}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown(
    "<div style='font-size:12px;color:#94a3b8;margin-top:-2px;'>Lihat seluruh isu dan "
    "sebarannya di halaman <b>Topik Keluhan</b>.</div>",
    unsafe_allow_html=True,
)

# ==========================================
# 5. NAVIGASI & KETERBATASAN DATA
# ==========================================
st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

nav_col, lim_col = st.columns(2)
with nav_col:
    st.markdown("""
    <div class="note-box" style="border-left-color: #185FA5; height:100%;">
        <div class="note-title">🧭 Petunjuk eksplorasi</div>
        <div class="note-content">
            Gunakan menu navigasi di sisi kiri untuk analisis lebih dalam:
            <ul class="note-list">
                <li><b>Profil Puskesmas</b>: performa per fasilitas kesehatan.</li>
                <li><b>Topik Keluhan</b>: tren narasi keluhan paling dominan.</li>
                <li><b>Peta Mutu</b>: pemetaan spasial titik kritis.</li>
                <li><b>Metodologi</b>: detail pengolahan data dan statistik.</li>
            </ul>
        </div>
    </div>
    """, unsafe_allow_html=True)
with lim_col:
    st.markdown("""
    <div class="note-box note-box-warn" style="height:100%;">
        <div class="note-title">⚠️ Catatan keterbatasan data</div>
        <div class="note-content">
            <ul class="note-list">
                <li><b>Sumber data tunggal:</b> hanya ulasan <b>Google Maps</b>.</li>
                <li><b>Representasi wilayah:</b> Kabupaten Bantul, Kota Semarang, dan Kota Surabaya.</li>
                <li><b>Fokus analisis:</b> ulasan bintang 1–2 untuk menangkap sinyal ketidakpuasan.</li>
                <li><b>Data statis:</b> hasil pengumpulan per <b>17 Mei 2026</b>, tidak mengandung ulasan setelahnya.</li>
            </ul>
        </div>
    </div>
    """, unsafe_allow_html=True)
