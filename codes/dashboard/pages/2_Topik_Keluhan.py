from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from lib.theme import setup, DIM_INFO, DIM_ORDER, C_INK, C_SUB, C_FAINT


# Data

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs"


@st.cache_data
def load_findings() -> pd.DataFrame:
    return pd.read_csv(OUT / "findings_full.csv")


@st.cache_data
def load_residuals() -> pd.DataFrame:
    return pd.read_csv(OUT / "statistik" / "chi2_residual_terstandarisasi.csv")


@st.cache_data
def load_chi2() -> dict:
    return pd.read_csv(OUT / "statistik" / "chi2_ringkasan.csv").iloc[0].to_dict()


@st.cache_data
def load_lift() -> pd.DataFrame:
    return pd.read_csv(OUT / "statistik" / "co_occurrence_lift.csv")


findings = load_findings()
neg = findings[findings["polarity"] == "neg"]

DIM_COLOR = {
    "Empathy": "#E76F51",
    "Responsiveness": "#2A9D8F",
    "Reliability": "#457B9D",
    "Assurance": "#E9C46A",
    "Tangibles": "#F4A261",
    "Umum": "#6C757D",
}
DIM_LABEL = {k: v[0] for k, v in DIM_INFO.items()}
DIM_LABEL["Umum"] = "Keluhan umum"
DIM_PLOT_ORDER = DIM_ORDER + ["Umum"]
WILAYAH = ["Bantul", "Semarang", "Surabaya"]


# Setup + style
setup("Topik Keluhan")

st.markdown(
    f"""
<style>
  html, body, [data-testid="stAppViewContainer"] {{
      background-color: #eef1f4 !important;
  }}

  [data-testid="stPlotlyChart"] {{
      background-color: #ffffff !important;
      border-radius: 18px !important;
      padding: 0px !important;
      box-shadow: 0 1px 3px rgba(16,32,48,.07) !important;
      box-sizing: border-box !important;
      overflow: hidden !important;
  }}


  .kicker{{ font-size:12px; font-weight:600; letter-spacing:.07em; text-transform:uppercase;
            color:{C_FAINT}; margin:0 0 4px; }}
  .sec-title{{ font-size:24px; font-weight:700; color:{C_INK}; margin:0 0 4px; letter-spacing:-.01em; }}
  .sec-sub{{ font-size:13.5px; color:{C_SUB}; margin:0 0 16px; line-height:1.55; }}

  /* daftar isu peringkat — kartu putih scrollable setinggi bar chart */
  .issue-card{{ background:#fff; border-radius:18px; box-shadow:0 1px 3px rgba(16,32,48,.07);
                padding:6px 20px; height:340px; overflow-y:auto; }}
  .issue-card::-webkit-scrollbar{{ width:7px; }}
  .issue-card::-webkit-scrollbar-thumb{{ background:#d4dae2; border-radius:99px; }}
  
  /* We use this new class for the bottom pairs to match the white card look */
  .pair-card {{ background:#fff; border-radius:18px; box-shadow:0 1px 3px rgba(16,32,48,.07);
                height: 100%; padding-bottom: 24px; overflow:hidden; }}

  .issue{{ display:flex; align-items:center; gap:14px; padding:13px 2px;
           border-bottom:1px solid #eef1f4; }}
  .issue:last-child{{ border-bottom:none; }}
  .issue-rank{{ font-size:14px; font-weight:700; color:{C_FAINT}; width:22px; text-align:right; }}
  .issue-dot{{ width:9px; height:9px; border-radius:50%; flex-shrink:0; }}
  .issue-name{{ flex:1; font-size:14.5px; font-weight:600; color:{C_INK}; }}
  .issue-dim{{ font-size:12px; color:{C_FAINT}; }}
  .issue-n{{ font-size:15px; font-weight:700; color:{C_INK}; white-space:nowrap; }}
  .issue-n span{{ font-size:11px; font-weight:500; color:{C_FAINT}; }}

  /* kartu pasangan ko-okurensi */
  .pair{{ display:flex; flex-direction:column; align-items:center; justify-content:center;
          gap:2px; padding:22px 8px 6px; text-align:center; }}
  .pair-dim{{ font-size:14.5px; font-weight:700; letter-spacing:-.005em; line-height:1.3;
              max-width:100%; overflow-wrap:break-word; }}
  .pair-plus{{ font-size:12px; font-weight:600; color:{C_FAINT}; margin:1px 0; }}
  .pair-lift{{ text-align:center; padding-bottom:8px; padding-top:6px; }}
  .pair-lift b{{ font-size:15px; font-weight:700; color:{C_INK}; }}
  .pair-lift span{{ font-size:12.5px; color:{C_SUB}; }}
  
</style>
""",
    unsafe_allow_html=True,
)


def section_header(kicker, title, sub=""):
    st.markdown(
        f"<div class='kicker'>{kicker}</div><div class='sec-title'>{title}</div>"
        + (f"<div class='sec-sub'>{sub}</div>" if sub else "<div style='height:14px'></div>"),
        unsafe_allow_html=True,
    )



# Header
st.markdown("<div class='page-title'>Profil Keluhan Masyarakat</div>", unsafe_allow_html=True)
st.markdown(
    "<div class='page-sub'>Aspek pelayanan puskesmas yang paling sering dikeluhkan, dari ulasan "
    "bintang 1–2 di Google Maps.</div>",
    unsafe_allow_html=True,
)

head_l, head_r = st.columns([1, 0.6])
with head_l:
    selected = st.selectbox(
        "Wilayah",
        WILAYAH
    )

reg = neg[neg["wilayah"] == selected]
all_total = len(neg)

with head_r:
    m1, m2 = st.columns(2)
    m1.metric(
        f"Keluhan di {selected}",
        f"{len(reg):,}".replace(",", "."),
        help=f"Jumlah temuan keluhan dari ulasan bintang 1–2 di {selected}.",
    )
    m2.metric(
        "Keluhan di 3 wilayah",
        f"{all_total:,}".replace(",", "."),
        help="Total temuan keluhan di Bantul, Semarang, dan Surabaya.",
    )

st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)


# Dimensi dominan (chart) + Isu spesifik teratas (list)
col_chart, col_list = st.columns([1.15, 1], gap="large")

residuals = load_residuals().set_index("dimension").reindex(DIM_ORDER)

# Dimensi dominan
with col_chart:
    section_header(
        "Berdasarkan dimensi SERVQUAL",
        "Dimensi Keluhan Terbanyak",
        "Bagian layanan mana yang paling sering bermasalah",
    )

    dim_count = (
        reg.groupby("dimension").size()
        .reindex(DIM_PLOT_ORDER, fill_value=0)
        .rename("n").reset_index()
    )
    dim_count["pct"] = dim_count["n"] / dim_count["n"].sum() * 100
    dim_count["label"] = dim_count["dimension"].map(DIM_LABEL)
    dim_count = dim_count.sort_values("pct")

    fig = go.Figure(
        go.Bar(
            x=dim_count["pct"],
            y=dim_count["label"],
            orientation="h",
            width=0.55,
            marker=dict(color=[DIM_COLOR[d] for d in dim_count["dimension"]], cornerradius=6),
            text=[f"{p:.0f}%" for p in dim_count["pct"]],
            textposition="outside",
            textfont=dict(size=12.5, color=C_SUB),
            customdata=dim_count[["dimension", "n"]],
            hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]} keluhan · %{x:.1f}%<extra></extra>",
        )
    )
    fig.update_layout(
        height=320,
        margin=dict(l=20, r=44, t=40, b=40),
        bargap=0.45,
        xaxis=dict(visible=False, range=[0, dim_count["pct"].max() * 1.2]),
        yaxis=dict(title="", tickfont=dict(size=13, color=C_INK)),
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="Inter", color=C_SUB),
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# isu spesifik teratas
with col_list:
    section_header(
        "Keluhan paling sering disebut",
        "Isu Utama Puskesmas",
        "Keluhan spesifik dengan jumlah terbanyak di wilayah ini",
    )

    isu_top = (
        reg.groupby(["dimension", "isu_kanonik"]).size()
        .rename("n").reset_index()
        .sort_values("n", ascending=False)
        .head(20).reset_index(drop=True)
    )

    rows = ""
    for i, r in isu_top.iterrows():
        color = DIM_COLOR.get(r["dimension"], "#808080")
        rows += (
            f"<div class='issue'>"
            f"<div class='issue-rank'>{i + 1}</div>"
            f"<div class='issue-dot' style='background:{color}'></div>"
            f"<div class='issue-name'>{str(r['isu_kanonik']).title()}"
            f"<div class='issue-dim'>{DIM_LABEL[r['dimension']]}</div></div>"
            f"<div class='issue-n'>{int(r['n'])} <span>keluhan</span></div>"
            f"</div>"
        )
    st.markdown(f"<div class='issue-card'>{rows}</div>", unsafe_allow_html=True)

st.markdown("---")


# Pola antar wilayah (heatmap residual)
chi2 = load_chi2()
sig = chi2["p_value"] < 0.05
p_disp = "< 0,001" if chi2["p_value"] < 0.001 else f"= {chi2['p_value']:.3f}"
badge_bg, badge_fg = ("#fdecea", "#c0392b") if sig else ("#eef1f4", C_SUB)
badge = "Berbeda signifikan" if sig else "Tidak berbeda signifikan"

section_header(
    "Distribusi dimensi per wilayah",
    "Pola Keluhan Setiap Wilayah",
    "Seberapa menonjol tiap dimensi di sebuah wilayah, dibanding pola gabungan ketiga wilayah",
)

res = residuals[WILAYAH]
heat = px.imshow(
    res.values,
    x=[f"<b>{w}</b>" for w in WILAYAH],
    y=[DIM_LABEL[d] for d in res.index],
    color_continuous_scale=["#457B9D", "#eef1f4", "#d05a4e"],
    zmin=-5.5, zmax=5.5,
    text_auto=".1f",
    aspect="auto",
)
heat.update_traces(
    textfont=dict(size=14, family="Inter"),
    hovertemplate="<b>%{y}</b> · %{x}<br>residual = %{z:.2f}<extra></extra>",
    xgap=4, ygap=4,
)
heat.update_layout(
    height=340,
    margin=dict(l=20, r=120, t=40, b=40),
    xaxis=dict(side="top", tickfont=dict(size=14, color=C_INK)),
    yaxis=dict(tickfont=dict(size=13.5, color=C_INK)),
    font=dict(family="Inter"),
    coloraxis_colorbar=dict(
        title="",
        thickness=12,
        len=1.01,
        outlinewidth=0,
        tickvals=[-4.5, 0, 4.5],
        ticktext=["Lebih jarang", "Sesuai pola", "Lebih sering"],
        tickfont=dict(size=11.5, color=C_SUB),
    ),
)

st.plotly_chart(heat, use_container_width=True, config={"displayModeBar": False})

with st.expander("Detail uji statistik"):
    tbl_col, desc_col = st.columns([1, 2], gap="small")
    with tbl_col:
        st.markdown(
            f"""
| Statistik | Nilai |
|---|---|
| χ² | {chi2['chi2']:.2f} |
| df | {int(chi2['dof'])} |
| p-value | {p_disp} |
"""
        )
    with desc_col:
        st.markdown(
            f"""**Uji χ² independensi**

Distribusi dimensi keluhan **{'berbeda' if sig else 'tidak berbeda'} secara signifikan**
antar wilayah. Angka heatmap adalah *standardized residual*: |residual| > 2 menandai sel
yang menyimpang nyata dari pola gabungan."""
        )

st.markdown("---")


# Keluhan yang sering datang bersamaan

section_header(
    "Co-occurrence dalam satu ulasan",
    f"Keluhan yang sering datang bersamaan — {selected}",
    "Pasangan dimensi yang muncul dalam ulasan yang sama lebih sering daripada kebetulan, "
    "dihitung khusus untuk wilayah ini",
)

# Lift dihitung pada ulasan-keluhan di wilayah terpilih (reg).
_by_rev = reg.groupby("review_id")["dimension"].apply(set)
_p = {d: _by_rev.apply(lambda s: d in s).mean() for d in DIM_ORDER}
_pairs = []
for _i, _a in enumerate(DIM_ORDER):
    for _b in DIM_ORDER[_i + 1:]:
        _pboth = _by_rev.apply(lambda s: _a in s and _b in s).mean()
        _den = _p[_a] * _p[_b]
        if _den > 0:
            _pairs.append((_a, _b, _pboth / _den))
lift_df = (
    pd.DataFrame(_pairs, columns=["dimensi_A", "dimensi_B", "lift"])
    .query("lift > 1").sort_values("lift", ascending=False).reset_index(drop=True)
)

if len(lift_df):
    MAX_PER_ROW = 3
    rows = [lift_df.iloc[i:i + MAX_PER_ROW] for i in range(0, len(lift_df), MAX_PER_ROW)]
    for row_idx, row_df in enumerate(rows):
        if row_idx > 0:
            st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
        n_in_row = len(row_df)
        if n_in_row < MAX_PER_ROW:
            pad = (MAX_PER_ROW - n_in_row) / 2
            ratios = [pad] + [1] * n_in_row + [pad]
            slots = st.columns(ratios)
            pair_cols = slots[1:-1]
        else:
            pair_cols = st.columns(MAX_PER_ROW)
        for col, (_, r) in zip(pair_cols, row_df.iterrows()):
            ca, cb = DIM_COLOR[r["dimensi_A"]], DIM_COLOR[r["dimensi_B"]]
            with col:
                st.markdown(
                    f"<div class='pair-card'>"
                    f"<div class='pair'>"
                    f"<span class='pair-dim' style='color:{ca}'>{r['dimensi_A']}</span>"
                    f"<span class='pair-plus'>+</span>"
                    f"<span class='pair-dim' style='color:{cb}'>{r['dimensi_B']}</span>"
                    f"</div>"
                    f"<div class='pair-lift'><b>Lift = {r['lift']:.2f}×</b><br>"
                    f"<span>muncul bersama lebih sering daripada kebetulan</span></div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
else:
    st.markdown(
        f"<div style='background:#fff;border-radius:18px;box-shadow:0 1px 3px rgba(16,32,48,.07);"
        f"padding:26px 24px;text-align:center;color:{C_SUB};font-size:14px;line-height:1.6;'>"
        f"Di <b>{selected}</b>, tidak ada pasangan dimensi yang muncul bersamaan melebihi kebetulan — "
        f"keluhan cenderung <b>berdiri sendiri</b>, tidak datang satu paket.</div>",
        unsafe_allow_html=True,
    )

st.markdown("<div style='height:48px'></div>", unsafe_allow_html=True)
