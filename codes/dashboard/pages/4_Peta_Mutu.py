"""Halaman Peta Mutu — Scatter kuadran dinamis + pemetaan spasial adaptif Folium."""
import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
import numpy as np

from lib.theme import setup
from lib.data import load_profiles, load_gmaps_meta, compute_rankings

# 1. Inisialisasi halaman sesuai standarisasi framework temanmu
setup("Peta Mutu")

st.markdown("<div class='page-title'>🗺️ Peta Mutu Puskesmas</div>", unsafe_allow_html=True)
st.markdown("<div class='page-sub'>Mendeteksi disparitas kuantitatif antara rating bintang Google Maps "
            "dengan tingkat keluhan aktual teks hasil pemodelan statistik.</div>", unsafe_allow_html=True)

# ==========================================
# 0. DATA INGESTION PIPELINE
# ==========================================
@st.cache_data
def load_and_sync_data():
    # Load metadata koordinat yang sudah kita tambal manual
    df_meta = pd.read_csv("gmaps_meta_dashboard_FINAL.csv")
    
    # Load data hasil inferensi statistik
    df_llm = pd.read_csv("../outputs/statistik/skor_per_puskesmas.csv")
    df_llm = df_llm.rename(columns={'id_puskesmas': 'puskesmas_id'})
    
    # Agregasi keluhan teks global (mengambil rata-rata intensitas_shrunk dari 5 dimensi)
    df_agg = df_llm.groupby('puskesmas_id').agg(
        pct_keluhan=('intensitas_shrunk', lambda x: x.mean() * 100)
    ).reset_index()
    
    # Gabungkan menjadi satu single dataframe utama
    df_final = pd.merge(df_meta, df_agg, on='puskesmas_id', how='inner')
    return df_final

df = load_and_sync_data()

# Load profiles dari lib untuk sinkronisasi dropdown bertingkat
profiles = load_profiles()

# Grouping ID Puskesmas berdasarkan wilayah administratifnya
by_region = {}
for pid, p in profiles.items():
    by_region.setdefault(p["wilayah"], []).append(pid)

# ==========================================
# 1. ON-PAGE CASCADING CONTROLS (REVISI FILTER)
# ==========================================
st.markdown("<br>", unsafe_allow_html=True)
c1, c2 = st.columns([1, 1.4])

# Filter 1: Pemilihan Wilayah Global
region_opts = ["Semua Wilayah"] + sorted(by_region.keys())
selected_region = c1.selectbox("Wilayah Administratif", region_opts)

# Filter 2: Dropdown Bertingkat (Opsi Puskesmas menyesuaikan Wilayah terpilih)
if selected_region == "Semua Wilayah":
    pkm_opts = [("all", "Semua Puskesmas")] + [
        (pid, profiles[pid]["nama"]) for pid in sorted(profiles.keys(), key=lambda x: profiles[x]["nama"])
    ]
else:
    pkm_opts = [("all", f"Semua Puskesmas di {selected_region}")] + [
        (pid, profiles[pid]["nama"]) for pid in sorted(by_region[selected_region], key=lambda x: profiles[x]["nama"])
    ]

selected_pid, selected_pkm_name = c2.selectbox(
    "Sorot Puskesmas Spesifik", 
    options=pkm_opts, 
    format_func=lambda x: x[1]
)

# Filtering Dataframe berdasarkan input dropdown bertingkat
df_filtered = df.copy()
if selected_region != "Semua Wilayah":
    df_filtered = df_filtered[df_filtered['wilayah'] == selected_region]

if selected_pid != "all":
    df_filtered = df_filtered[df_filtered['puskesmas_id'] == selected_pid]

# ==========================================
# 2. SCATTER PLOT 4 KUADRAN (PLOTLY)
# ==========================================
st.markdown("<br>", unsafe_allow_html=True)
st.subheader("📊 Kuadran Performa Mutu")

if not df_filtered.empty:
    # Garis pembatas kuadran menggunakan median dari data global wilayah aktif
    median_rating = df_filtered['avg_rating'].median()
    median_keluhan = df_filtered['pct_keluhan'].median()

    fig = px.scatter(
        df_filtered, 
        x='avg_rating', 
        y='pct_keluhan', 
        size='jumlah_ulasan', 
        color='wilayah',
        hover_name='puskesmas_title',
        hover_data={'avg_rating': True, 'pct_keluhan': ':.1f', 'jumlah_ulasan': True, 'wilayah': False},
        labels={
            'avg_rating': 'Rata-rata Bintang Google Maps', 
            'pct_keluhan': 'Tingkat Keluhan Aktual - Bayes Shrunk (%)',
            'jumlah_ulasan': 'Volume Ulasan'
        },
        size_max=40, # Diperbesar sedikit biar bubble-nya makin mantap
        opacity=0.75,
        color_discrete_sequence=px.colors.qualitative.Safe
    )

    # Injeksi Garis Median Pembatas (Posisi teks dipindah ke 'bottom right' agar aman)
    fig.add_hline(y=median_keluhan, line_dash="dash", line_color="rgba(128,128,128,0.6)", 
                  annotation_text=f"Median Keluhan ({median_keluhan:.1f}%)", annotation_position="bottom right")
    fig.add_vline(x=median_rating, line_dash="dash", line_color="rgba(128,128,128,0.6)", 
                  annotation_text=f"Median Bintang ({median_rating:.1f})", annotation_position="bottom right")

    # Anotasi Karakteristik Kuadran (Dipaku ke pojok kanvas menggunakan xref & yref 'paper')
    fig.add_annotation(x=0.99, y=0.02, xref="paper", yref="paper", text="🌟 Benar-benar baik", showarrow=False, font=dict(color="green", size=12), xanchor="right", yanchor="bottom")
    fig.add_annotation(x=0.99, y=0.98, xref="paper", yref="paper", text="⚠️ MENYESATKAN (Sinyal)", showarrow=False, font=dict(color="red", size=12), xanchor="right", yanchor="top")
    fig.add_annotation(x=0.01, y=0.02, xref="paper", yref="paper", text="⚪ Sepi data / Netral", showarrow=False, font=dict(color="gray", size=12), xanchor="left", yanchor="bottom")
    fig.add_annotation(x=0.01, y=0.98, xref="paper", yref="paper", text="❌ Konsisten buruk", showarrow=False, font=dict(color="darkred", size=12), xanchor="left", yanchor="top")

    # Kunci Sumbu X agar rentangnya statis (skala 0.8 sampai 5.2)
    # Ini bikin visualisasi anomali rating jadi lebih masuk akal dan gak terlalu mepet
    fig.update_xaxes(range=[0.8, 5.2])

    fig.update_layout(height=550, template="plotly_white", margin=dict(l=15, r=15, t=15, b=15))
    st.plotly_chart(fig, use_container_width=True)

# ==========================================
# 3. SPASIAL ADAPTIF MAPS (DENGAN KETERANGAN WARNA)
# ==========================================
st.markdown("---")
st.subheader("📍 Pemetaan Geografis Spasial")
st.caption("Klik pada titik faskes untuk melihat detail performa. Warna titik mengikuti posisi faskes pada kuadran di atas.")

if not df_filtered.empty:
    # 3A. INJEKSI KETERANGAN WARNA (LEGEND) PAKAI HTML
    legend_html = """
    <div style="display:flex; justify-content:center; gap:20px; flex-wrap:wrap; margin-bottom:15px; font-size:13px; color:#475569;">
        <div style="display:flex; align-items:center; gap:6px;">
            <span style="width:12px; height:12px; border-radius:50%; background-color:#2f9e6f; display:inline-block;"></span>
            <span><b>Hijau:</b> Benar-benar Baik</span>
        </div>
        <div style="display:flex; align-items:center; gap:6px;">
            <span style="width:12px; height:12px; border-radius:50%; background-color:#d05a4e; display:inline-block;"></span>
            <span><b>Merah:</b> Menyesatkan (Sinyal Bahaya)</span>
        </div>
        <div style="display:flex; align-items:center; gap:6px;">
            <span style="width:12px; height:12px; border-radius:50%; background-color:#7f5f57; display:inline-block;"></span>
            <span><b>Cokelat:</b> Konsisten Buruk</span>
        </div>
        <div style="display:flex; align-items:center; gap:6px;">
            <span style="width:12px; height:12px; border-radius:50%; background-color:#64748b; display:inline-block;"></span>
            <span><b>Abu-abu:</b> Netral / Sepi Data</span>
        </div>
    </div>
    """
    st.markdown(legend_html, unsafe_allow_html=True)

    # 3B. LOGIKA ADAPTIF ZOOM & MAP CENTER
    if selected_pid != "all":
        map_center_lat = df_filtered['latitude'].values[0]
        map_center_lon = df_filtered['longitude'].values[0]
        zoom_level = 15 
    else:
        map_center_lat = df_filtered['latitude'].mean()
        map_center_lon = df_filtered['longitude'].mean()
        if selected_region == "Semua Wilayah":
            zoom_level = 9  
        else:
            zoom_level = 11 

    m = folium.Map(location=[map_center_lat, map_center_lon], zoom_start=zoom_level, tiles="CartoDB positron")

    # 3C. RENDER TITIK PUSKESMAS
    for idx, row in df_filtered.iterrows():
        if pd.notna(row['latitude']) and pd.notna(row['longitude']):
            
            # Klasifikasi warna mengikuti kuadran secara absolut
            if row['avg_rating'] > median_rating and row['pct_keluhan'] > median_keluhan:
                marker_color = '#d05a4e'  # Merah
            elif row['avg_rating'] > median_rating and row['pct_keluhan'] <= median_keluhan:
                marker_color = '#2f9e6f'  # Hijau
            elif row['avg_rating'] <= median_rating and row['pct_keluhan'] > median_keluhan:
                marker_color = '#7f5f57'  # Cokelat
            else:
                marker_color = '#64748b'  # Abu-abu

            popup_html = f"""
            <div style='font-family: sans-serif; width: 200px;'>
                <h4 style='margin:0 0 5px 0; color:#1e293b;'>Puskesmas {row['puskesmas_title']}</h4>
                <span style='color:#64748b; font-size:11px;'>Wilayah: {row['wilayah']}</span><br><br>
                ⭐ Rating Bintang: <b>{row['avg_rating']}</b><br>
                🚨 Indeks Keluhan: <b>{row['pct_keluhan']:.1f}%</b><br>
                📝 Total Ulasan: <b>{row['jumlah_ulasan']} ulasan</b>
            </div>
            """
            
            folium.CircleMarker(
                location=[row['latitude'], row['longitude']],
                radius=np.log1p(row['jumlah_ulasan']) * 4.5,
                color=marker_color,
                fill=True,
                fill_color=marker_color,
                fill_opacity=0.8,
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=f"Puskesmas {row['puskesmas_title']}"
            ).add_to(m)

    st_folium(m, width="100%", height=500)
else:
    st.warning("Data kosong untuk filter terpilih.")