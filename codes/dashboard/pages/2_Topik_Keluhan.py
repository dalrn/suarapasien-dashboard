"""
Topik Keluhan se-Kabupaten

Tujuan halaman: pola keluhan di tingkat kabupaten (bukan per puskesmas): mana
yang merata (perlu kebijakan dinas) vs lokal, dan bagaimana antar-wilayah.

Sumber data:
  - load_topik()            : persen keluhan & sebaran per dimensi, χ², lift
  - load_isu_kanonik()      : isu spesifik (hasil clustering) + jumlah ulasan
  - load_region_breakdown() : persen keluhan per dimensi per wilayah
"""
import streamlit as st
import pandas as pd
import plotly.express as px

from lib.theme import (
    setup,
    DIM_INFO,
    DIM_ORDER,
)

from lib.data import (
    load_topik,
    load_isu_kanonik,
    load_region_breakdown,
    load_profiles,
    dataset_stats,
)

# ==============================
# Load Data
# ==============================
topik_df = load_topik()

isu_df = load_isu_kanonik()

region_df = load_region_breakdown()

stats = dataset_stats()

# ==============================
# LOAD FINDINGS
# ==============================

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs"

findings = pd.read_csv(
    OUT / "findings_full.csv"
)

# ==============================
# HEADER
# ==============================

setup("Topik Keluhan")

st.markdown(
    "<div class='page-title'>📣 Profil Keluhan Masyarakat</div>",
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class='page-sub'>
    Apa yang paling sering dikeluhkan warga pada layanan puskesmas di wilayah yang dipilih.
    </div>
    <br>
    """,
    unsafe_allow_html=True
)

# =====================================================
# Filter Wilayah
# =====================================================

profiles = load_profiles()

by_region = {}

for pid, p in profiles.items():
    by_region.setdefault(
        p["wilayah"],
        []
    ).append(pid)

c1 = st.columns([1])[0]

selected_region = c1.selectbox(
    "Wilayah",
    sorted(by_region.keys()),
    help="Pilih kabupaten/kota yang ingin dianalisis."
)

# =====================================================
# SECTION 1
# Dimensi Keluhan Dominan
# =====================================================

st.markdown("---")

st.subheader("📍 Dimensi Keluhan yang Paling Banyak Muncul")

st.caption(
    """
    Menunjukkan aspek pelayanan yang paling sering menjadi sumber keluhan
    masyarakat pada puskesmas di wilayah yang dipilih.
    """
)

section1_df = findings[
    (findings["wilayah"] == selected_region)
    & (findings["polarity"] == "neg")
].copy()

dimensi_count = (
    section1_df
    .groupby("dimension")
    .size()
    .reset_index(name="Jumlah")
)

total_keluhan = dimensi_count["Jumlah"].sum()

dimensi_count["Persentase"] = (
    dimensi_count["Jumlah"]
    / total_keluhan
    * 100
)

DIM_ORDER_EXT = [
    "Empathy",
    "Responsiveness",
    "Reliability",
    "Assurance",
    "Tangibles",
    "Umum"
]

all_dims = pd.DataFrame({
    "dimension": DIM_ORDER_EXT
})

region_chart = (
    all_dims
    .merge(
        dimensi_count,
        on="dimension",
        how="left"
    )
    .fillna(0)
)

warna = {
    "Empathy": "#E76F51",
    "Responsiveness": "#2A9D8F",
    "Reliability": "#457B9D",
    "Assurance": "#E9C46A",
    "Tangibles": "#F4A261",
    "Umum": "#6C757D"
}

region_chart = region_chart.sort_values(
    "Persentase",
    ascending=False
)

fig = px.bar(
    region_chart,
    x="Persentase",
    y="dimension",
    orientation="h",
    color="dimension",
    color_discrete_map=warna,
    text=region_chart["Persentase"].round(1)
)

fig.update_traces(
    texttemplate="%{text:.1f}%",
    textposition="outside",
    marker=dict(cornerradius=12)
)

fig.update_layout(
    showlegend=False,
    xaxis_title="Persentase Keluhan (%)",
    yaxis_title="",
    height=430,
    margin=dict(l=20, r=20, t=10, b=20)
)

st.plotly_chart(
    fig,
    use_container_width=True,
    config={"displayModeBar": False}
)
# 2. Keluhan paling umum se-kabupaten
# Daftar 10 isu spesifik teratas (hasil kanonikalisasi) + jumlah ulasan + tag dimensi.

# =====================================================
# SECTION 2
# Keluhan paling umum di wilayah terpilih
# =====================================================

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs"

findings = pd.read_csv(
    OUT / "findings_full.csv"
)

st.markdown("---")

st.subheader("📌 Keluhan yang Paling Banyak Dilaporkan")

st.caption(
    "Menampilkan 10 keluhan yang paling sering muncul berdasarkan ulasan masyarakat pada wilayah yang dipilih."
)

# =====================================================
# Ambil data wilayah terpilih
# =====================================================

isu_df = findings[
    (findings["wilayah"] == selected_region)
    & (findings["polarity"] == "neg")
]

isu_top = (
    isu_df
    .groupby(
        ["dimension", "sub_issue"],
        as_index=False
    )
    .size()
    .rename(
        columns={
            "dimension": "Dimensi",
            "sub_issue": "Sub Isu",
            "size": "Jumlah"
        }
    )
    .sort_values(
        "Jumlah",
        ascending=False
    )
    .head(10)
)

# =====================================================
# Warna Dimensi
# =====================================================

warna = {
    "Empathy": "#E76F51",
    "Responsiveness": "#2A9D8F",
    "Reliability": "#457B9D",
    "Assurance": "#E9C46A",
    "Tangibles": "#F4A261",
    "Umum": "#6C757D"
}

# =====================================================
# Layout
# =====================================================

left_df = isu_top.iloc[:5]
right_df = isu_top.iloc[5:]

left, right = st.columns(2)

# =====================================================
# Function
# =====================================================
def tampilkan(df, container):

    for _, row in df.iterrows():

        color = warna.get(row["Dimensi"], "#808080")

        container.markdown(
            f"""
<div style="
background:white;
border:1px solid #E5E7EB;
border-radius:12px;
padding:12px 16px;
margin-bottom:10px;
box-shadow:0 1px 2px rgba(0,0,0,.05);
">

<div style="
display:flex;
justify-content:space-between;
align-items:center;
gap:12px;
">

<div style="flex:1;">

<div style="
font-size:17px;
font-weight:700;
color:#1F2937;
line-height:1.25;
margin-bottom:6px;
">
{str(row["Sub Isu"]).title()}
</div>

<div style="
display:flex;
align-items:center;
gap:7px;
">

<div style="
width:10px;
height:10px;
border-radius:50%;
background:{color};
flex-shrink:0;
"></div>

<div style="
font-size:12px;
color:#6B7280;
font-weight:500;
">
{row["Dimensi"]}
</div>

</div>

</div>

<div style="
font-size:13px;
font-weight:600;
color:#6B7280;
white-space:nowrap;
">
{row["Jumlah"]} keluhan
</div>

</div>

</div>
""",
            unsafe_allow_html=True
        )

# =====================================================
# Tampilkan
# =====================================================

tampilkan(left_df, left)
tampilkan(right_df, right)

# 3. Apakah pola sama di tiap wilayah?
# Tabel dimensi × wilayah (% keluhan, dengan bar sel) +
# pernyataan hasil uji χ² (berbeda nyata / tidak) + tooltip penjelasan.

# =====================================================
# TAMPILAN PERBANDINGAN WILAYAH
# =====================================================
# SECTION 3
# Perbandingan Pola Keluhan Antar Wilayah
# =====================================================

st.markdown("<br>", unsafe_allow_html=True)
st.divider()
st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

st.subheader("📊Apakah Keluhan Masyarakat Sama di Setiap Wilayah?")

st.caption(
    """
    Menampilkan perbandingan dimensi keluhan yang paling dominan
    pada masing-masing wilayah.
    """
)

# ================================
# 1. SIAPKAN DATA
# ================================

from scipy.stats import chi2_contingency

neg = findings[findings["polarity"] == "neg"].copy()

wilayah_order = ["Bantul", "Semarang", "Surabaya"]

dimensi_order = [
    "Responsiveness",
    "Reliability",
    "Empathy",
    "Assurance",
    "Tangibles",
    "Umum",
]

warna = {
    "Empathy": "#E76F51",
    "Responsiveness": "#2A9D8F",
    "Reliability": "#457B9D",
    "Assurance": "#E9C46A",
    "Tangibles": "#F4A261",
    "Umum": "#6C757D"
}

freq = (
    neg.groupby(["dimension", "wilayah"])
       .size()
       .unstack(fill_value=0)
       .reindex(index=dimensi_order, columns=wilayah_order, fill_value=0)
)

persen = freq.astype(float)

for w in wilayah_order:
    total = freq[w].sum()
    persen[w] = (freq[w] / total * 100) if total > 0 else 0

chi2_val, p_val, dof, _ = chi2_contingency(freq)

# ================================
# CSS
# ================================

st.markdown(
"""
<style>

.compare-wrapper{
    margin-top:18px;
}

.compare-header,
.compare-row{
    display:grid;
    grid-template-columns:240px repeat(3,minmax(170px,1fr));
    column-gap:22px;
    align-items:center;
}

.compare-header{
    padding:0 10px 12px 10px;
    font-size:15px;
    font-weight:700;
    color:#6B7280;
    border-bottom:2px solid #E5E7EB;
    margin-bottom:8px;
}

.compare-header div:not(:first-child){
    text-align:center;
}

.compare-row{
    padding:16px 10px;
    border-bottom:1px solid #F3F4F6;
}

.compare-row:hover{
    background:#FAFAFA;
    border-radius:12px;
}

.dimensi{
    display:flex;
    align-items:center;
    gap:10px;
    font-size:16px;
    font-weight:600;
    color:#111827;
}

.dot{
    width:11px;
    height:11px;
    border-radius:50%;
    flex-shrink:0;
}

.cell{
    padding:0 6px;
}

.bar-bg{
    height:10px;
    background:#EEF2F7;
    border-radius:999px;
    overflow:hidden;
}

.bar{
    height:100%;
    border-radius:999px;
}

.value{
    margin-top:6px;
    font-size:13px;
    font-weight:600;
    text-align:right;
    color:#6B7280;
}

.result-box{
    margin-top:16px;
    padding:18px 20px;
    background:white;
    border:1px solid #E5E7EB;
    border-radius:16px;
    box-shadow:0 1px 3px rgba(0,0,0,.05);
}

.result-title{
    font-size:16px;
    font-weight:700;
    color:#111827;
    margin-bottom:8px;
}

.result-text{
    font-size:14px;
    line-height:1.7;
    color:#4B5563;
}

.result-stat{
    margin-top:10px;
    font-size:12px;
    color:#6B7280;
}

</style>
""",
unsafe_allow_html=True
)

# ================================
# BUILD TABLE
# ================================

rows_html = ""

for dim in dimensi_order:

    cells_html = ""

    for wilayah in wilayah_order:

        val = persen.loc[dim, wilayah]

        cells_html += (
            f'<div class="cell">'
            f'<div class="bar-bg">'
            f'<div class="bar" style="width:{val:.1f}%; background:{warna[dim]};"></div>'
            f'</div>'
            f'<div class="value">{val:.1f}%</div>'
            f'</div>'
        )

    rows_html += (
        f'<div class="compare-row">'
        f'<div class="dimensi">'
        f'<div class="dot" style="background:{warna[dim]};"></div>'
        f'{dim}'
        f'</div>'
        f'{cells_html}'
        f'</div>'
    )

html = (
    '<div class="compare-wrapper">'
    '<div class="compare-header">'
    '<div>Dimensi</div>'
    '<div>Bantul</div>'
    '<div>Semarang</div>'
    '<div>Surabaya</div>'
    '</div>'
    f'{rows_html}'
    '</div>'
)

st.markdown(html, unsafe_allow_html=True)

st.caption(
    """
    Setiap kolom wilayah berjumlah 100%.
    Nilai yang ditampilkan menunjukkan proporsi keluhan pada masing-masing dimensi,
    sehingga dapat digunakan untuk melihat keluhan yang paling dominan di setiap wilayah.
    """
)
# ================================
# HASIL UJI STATISTIK
# ================================

p_display = (
    "< 0,001"
    if p_val < 0.001
    else f"= {p_val:.3f}"
)

if p_val < 0.05:

    isi_temuan = (
        f"""
Melalui uji χ² independensi, ditemukan bahwa pola keluhan masyarakat
<b>berbeda secara signifikan antar wilayah</b>
(χ² = {chi2_val:.2f}; df = {dof}; p {p_display}). Dengan kata lain, setiap wilayah memiliki karakteristik permasalahan
layanan yang berbeda sehingga prioritas perbaikan dan pembinaan mutu
layanan puskesmas perlu disesuaikan dengan kondisi masing-masing wilayah.
"""
    )

else:

    isi_temuan = (
        f"""
Melalui uji χ² independensi, tidak ditemukan perbedaan yang signifikan
pada pola keluhan masyarakat antar wilayah
(χ² = {chi2_val:.2f}; df = {dof}; p {p_display}). Hal ini menunjukkan bahwa distribusi keluhan pada setiap wilayah relatif
serupa sehingga strategi peningkatan mutu layanan dapat dilakukan dengan
pendekatan yang lebih umum.
"""
    )

st.markdown(
    f"""
<div style="
background:white;
border:1px solid #E5E7EB;
text-align: justify;
border-radius:16px;
padding:20px 24px;
margin-top:16px;
box-shadow:0 1px 3px rgba(0,0,0,.05);
">

<div style="
font-size:18px;
text-align: justify;
font-weight:700;
color:#111827;
margin-bottom:12px;
">
Ringkasan Temuan
</div>

<div style="
font-size:14px;
text-align: justify;
line-height:1.8;
color:#374151;
">
{isi_temuan}
</div>

</div>
""",
    unsafe_allow_html=True
)


# =====================================================
# SECTION 4
# Keluhan yang Sering Datang Bersamaan
# =====================================================

st.markdown("---")

st.subheader("🔗 Keluhan yang Sering Datang Bersamaan")

st.markdown(
    """
    <div style="
        font-size:14px;
        color:#6B7280;
        line-height:1.8;
        text-align:justify;
        margin-bottom:16px;
    ">
    Menunjukkan pasangan dimensi keluhan yang cenderung muncul dalam ulasan yang sama.
    </div>
    """,
    unsafe_allow_html=True
)

# =====================================================
# LOAD DATA
# =====================================================

lift_df = pd.read_csv(
    OUT / "statistik" / "co_occurrence_lift.csv"
)

lift_df = (
    lift_df[lift_df["lift"] > 1]
    .sort_values("lift", ascending=False)
    .reset_index(drop=True)
)

# =====================================================
# WARNA DIMENSI
# =====================================================

warna = {
    "Empathy": "#E76F51",
    "Responsiveness": "#2A9D8F",
    "Reliability": "#457B9D",
    "Assurance": "#E9C46A",
    "Tangibles": "#F4A261",
    "Umum": "#6C757D"
}

# =====================================================
# DAFTAR PASANGAN DIMENSI
# =====================================================
cards_html = ""
for _, row in lift_df.iterrows():
    color_a = warna.get(row["dimensi_A"], "#6C757D")
    color_b = warna.get(row["dimensi_B"], "#6C757D")

    tooltip_text = (
        f"{row['dimensi_A']} dan {row['dimensi_B']} sering disebut bersamaan dalam satu ulasan, "
        f"{row['lift']:.2f}x lebih sering dibanding jika kemunculannya acak/tidak saling terkait. "
        "Semakin tinggi nilainya, semakin kuat indikasi bahwa kedua aspek ini berasal dari "
        "akar masalah yang sama dan sebaiknya dibenahi bersamaan."
    )

    cards_html += (
        '<div style="background:white;border:1px solid #E5E7EB;border-radius:16px;'
        'padding:18px 24px;margin-bottom:12px;box-shadow:0 1px 3px rgba(0,0,0,.05);">'
        '<div style="display:flex;justify-content:space-between;align-items:center;">'
        '<div style="display:flex;align-items:center;gap:14px;flex-wrap:wrap;">'
        f'<span style="background:{color_a};color:white;padding:7px 16px;'
        f'border-radius:999px;font-size:13px;font-weight:600;">{row["dimensi_A"]}</span>'
        '<span style="font-size:22px;font-weight:700;color:#9CA3AF;">x</span>'
        f'<span style="background:{color_b};color:white;padding:7px 16px;'
        f'border-radius:999px;font-size:13px;font-weight:600;">{row["dimensi_B"]}</span>'
        '</div>'
        '<div style="text-align:right;display:flex;align-items:center;gap:6px;">'
        '<div>'
        '<div style="font-size:12px;color:#6B7280;margin-bottom:2px;">Lift</div>'
        f'<div style="font-size:28px;font-weight:700;color:#111827;line-height:1;">{row["lift"]:.2f}</div>'
        '</div>'
        f'<span title="{tooltip_text}" style="display:inline-block;cursor:help;'
        'color:#94a3b8;font-size:13px;border:1px solid #cbd5e1;border-radius:50%;'
        'width:18px;height:18px;text-align:center;line-height:17px;flex-shrink:0;">ⓘ</span>'
        '</div>'
        '</div>'
        '</div>'
    )

st.markdown(cards_html, unsafe_allow_html=True)

# =====================================================
# RINGKASAN TEMUAN
# =====================================================

if len(lift_df):

    top_pair = lift_df.iloc[0]

    st.markdown(
        f"""
<div style="
background:white;
border:1px solid #E5E7EB;
border-radius:16px;
text-align: justify;
padding:20px 24px;
margin-top:10px;
margin-bottom:18px;
box-shadow:0 1px 3px rgba(0,0,0,.05);
">

<div style="
font-size:18px;
text-align: justify;
font-weight:700;
color:#111827;
margin-bottom:12px;
">
Ringkasan Temuan
</div>

<div style="
font-size:14px;
text-align: justify;
line-height:1.8;
color:#374151;
">

Pasangan dimensi yang paling sering muncul bersamaan adalah
<b>{top_pair['dimensi_A']}</b> dan
<b>{top_pair['dimensi_B']}</b>
(lift = <b>{top_pair['lift']:.2f}</b>).

Hal ini menunjukkan bahwa keluhan pada kedua aspek tersebut
sering muncul dalam pengalaman pasien yang sama sehingga
upaya perbaikan dapat dipertimbangkan secara terpadu.

</div>

</div>
""",
        unsafe_allow_html=True
    )