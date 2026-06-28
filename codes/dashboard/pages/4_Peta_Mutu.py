"""Halaman Peta Mutu — Peta Intelijen Spasial Kualitas Faskes."""
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import numpy as np
from pathlib import Path

from lib.theme import setup, DIM_ORDER
from lib.data import load_gmaps_meta, load_profiles

# Setup Halaman
setup("Peta Mutu")

# ==========================================
# 0. DATA INGESTION PIPELINE (REKAYASA ULANG UNTUK PETA DINAMIS)
# ==========================================
@st.cache_data
def load_and_sync_data():
    ROOT_DIR = Path(__file__).resolve().parents[2] 
    OUT_DIR = ROOT_DIR / "outputs"
    
    # 1. Load data LLM (Tingkat Keluhan)
    path_llm = OUT_DIR / "statistik" / "skor_per_puskesmas.csv"
    df_llm = pd.read_csv(path_llm)
    df_llm = df_llm.rename(columns={'id_puskesmas': 'puskesmas_id'})
    
    # 1A. Hitung Total Keluhan Keseluruhan (Rata-rata dari semua dimensi)
    df_overall = df_llm.groupby('puskesmas_id')['intensitas_shrunk'].mean().reset_index()
    df_overall['pct_keluhan_total'] = df_overall['intensitas_shrunk'] * 100
    
    # 1B. Cari Dimensi Dominan (Dimensi dengan nilai keluhan tertinggi per faskes)
    idx_max = df_llm.groupby('puskesmas_id')['intensitas_shrunk'].idxmax()
    df_dominant = df_llm.loc[idx_max, ['puskesmas_id', 'dimensi']].rename(columns={'dimensi': 'dimensi_dominan'})
    
    # 1C. Pivot Data agar tiap dimensi punya kolom persentasenya sendiri
    df_pivot = df_llm.pivot(index='puskesmas_id', columns='dimensi', values='intensitas_shrunk').fillna(0).reset_index()
    for col in df_pivot.columns:
        if col != 'puskesmas_id':
            df_pivot[col] = df_pivot[col] * 100
            
    # Gabungkan semua data agregasi
    df_agg = df_overall[['puskesmas_id', 'pct_keluhan_total']].merge(df_dominant, on='puskesmas_id', how='left')
    df_agg = df_agg.merge(df_pivot, on='puskesmas_id', how='left')

    # 2. Load koordinat spasial
    DASHBOARD_DIR = Path(__file__).resolve().parents[1]
    path_meta = DASHBOARD_DIR / "gmaps_meta_dashboard_FINAL.csv"
    df_meta = pd.read_csv(path_meta)
    
    # 3. Load Rating Keseluruhan dari Library
    gmaps_meta_asli = load_gmaps_meta()
    df_meta['avg_rating'] = df_meta['puskesmas_id'].map(lambda x: gmaps_meta_asli.get(x, {}).get('avg', 0))
    df_meta['jumlah_ulasan'] = df_meta['puskesmas_id'].map(lambda x: gmaps_meta_asli.get(x, {}).get('total', 0))
    
    # 4. Gabungkan Data Spasial + Data LLM
    df_final = pd.merge(df_meta, df_agg, on='puskesmas_id', how='inner')
    return df_final

df = load_and_sync_data()
profiles = load_profiles()

by_region = {}
for pid, p in profiles.items():
    by_region.setdefault(p["wilayah"], []).append(pid)

# Master Warna Dimensi SERVQUAL
WARNA_DIMENSI = {
    "Responsiveness": "#2A9D8F",  # Toska
    "Reliability": "#457B9D",     # Biru Baja
    "Empathy": "#E76F51",         # Terakota
    "Assurance": "#E9C46A",       # Kuning Pasir
    "Tangibles": "#F4A261",       # Oranye
    "Umum": "#94a3b8"             # Abu-abu
}

# ==========================================
# CUSTOM CSS
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    .reportview-container, .main, div, span, p { font-family: 'Inter', sans-serif; }
    .page-title { font-size: 28px; font-weight: 700; color: #1e293b; letter-spacing: -0.02em; margin-bottom: 5px; }
    .page-sub { font-size: 14.5px; color: #64748b; line-height: 1.6; margin-bottom: 25px; }
    .control-panel { background: #f8fafc; border: 1px solid #e2e8f0; padding: 15px 20px; border-radius: 12px; margin-bottom: 20px; }
    .legend-box { display:flex; justify-content:center; gap:15px; flex-wrap:wrap; margin-top:15px; font-size:13px; color:#475569; padding: 10px; background: #ffffff; border-radius: 8px; border: 1px solid #e2e8f0;}
    .legend-item { display:flex; align-items:center; gap:6px; }
    .legend-dot { width:12px; height:12px; border-radius:50%; display:inline-block; }
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='page-title'>🗺️ Peta Mutu Puskesmas</div>", unsafe_allow_html=True)
st.markdown("<div class='page-sub'>Pemetaan spasial interaktif untuk mendeteksi sebaran titik kritis permasalahan layanan secara geografis.</div>", unsafe_allow_html=True)

# ==========================================
# 1. PANEL KONTROL & FILTERING
# ==========================================
c1, c2 = st.columns(2)
with c1:
    region_options = ["Semua Wilayah"] + sorted(by_region.keys())
    selected_region = st.selectbox("Filter Wilayah", region_options)

with c2:
    mode_warna = st.selectbox(
        "Mode Analisis Peta",
        [
            "Intensitas Keluhan Keseluruhan", 
            "Dimensi Keluhan Dominan", 
            "Fokus Dimensi Spesifik"
        ],
        help="Pilih metrik apa yang akan direpresentasikan oleh warna titik faskes di peta."
    )

selected_dim = None
if mode_warna == "Fokus Dimensi Spesifik":
    # Cari dimensi apa saja yang ada di dataframe
    dim_tersedia = [col for col in DIM_ORDER if col in df.columns]
    selected_dim = st.selectbox("Pilih Dimensi yang Ingin Disorot:", dim_tersedia)

# Filter Data
if selected_region != "Semua Wilayah":
    df_filtered = df[df['wilayah'] == selected_region]
else:
    df_filtered = df.copy()

# ==========================================
# 2. LOGIKA PEWARNAAN & RENDER PETA
# ==========================================
if not df_filtered.empty:
    
    # Setup Titik Tengah Peta
    map_center_lat = df_filtered['latitude'].mean()
    map_center_lon = df_filtered['longitude'].mean()
    zoom_level = 8 if selected_region == "Semua Wilayah" else 11 

    m = folium.Map(location=[map_center_lat, map_center_lon], zoom_start=zoom_level, tiles="CartoDB positron")

    # Fungsi penentu warna titik
    def get_intensity_color(val):
        if val < 20: return '#2f9e6f'   # Hijau (Aman)
        elif val <= 35: return '#f59e0b' # Kuning (Waspada)
        else: return '#d05a4e'          # Merah (Kritis)

    for idx, row in df_filtered.iterrows():
        if pd.notna(row['latitude']) and pd.notna(row['longitude']):
            
            # Tentukan warna marker berdasarkan mode yang dipilih
            if mode_warna == "Intensitas Keluhan Keseluruhan":
                val = row['pct_keluhan_total']
                marker_color = get_intensity_color(val)
                metric_label = "Tingkat Keluhan Keseluruhan"
                metric_val = f"{val:.1f}%"
                
            elif mode_warna == "Dimensi Keluhan Dominan":
                dom = row['dimensi_dominan']
                marker_color = WARNA_DIMENSI.get(dom, '#64748b')
                metric_label = "Masalah Paling Dominan"
                metric_val = f"<b>{dom}</b>"
                
            elif mode_warna == "Fokus Dimensi Spesifik":
                val = row[selected_dim] if pd.notna(row[selected_dim]) else 0
                marker_color = get_intensity_color(val)
                metric_label = f"Tingkat Keluhan '{selected_dim}'"
                metric_val = f"{val:.1f}%"

            # Setup Pop-up Interaktif
            popup_html = f"""
            <div style='font-family: sans-serif; width: 220px;'>
                <h4 style='margin:0 0 5px 0; color:#1e293b;'>{row['puskesmas_title']}</h4>
                <span style='color:#64748b; font-size:11px;'>{row['wilayah']}</span><br><br>
                Rating Google: <b>{row['avg_rating']}</b> ({row['jumlah_ulasan']} Ulasan)<br>
                {metric_label}: <b>{metric_val}</b>
            </div>
            """
            
            folium.CircleMarker(
                location=[row['latitude'], row['longitude']],
                radius=np.log1p(row['jumlah_ulasan']) * 3.0, # Radius tetap menunjukkan volume ulasan
                color=marker_color,
                fill=True,
                fill_color=marker_color,
                fill_opacity=0.8,
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=f"{row['puskesmas_title']}"
            ).add_to(m)

    st_folium(m, width="100%", height=550)

    # ==========================================
    # 3. RENDER LEGEND DINAMIS
    # ==========================================
    if mode_warna in ["Intensitas Keluhan Keseluruhan", "Fokus Dimensi Spesifik"]:
        legend_html = """
        <div class='legend-box'>
            <div class='legend-item'><span class='legend-dot' style='background:#2f9e6f;'></span><span><b>Aman</b> (&lt; 20% Keluhan)</span></div>
            <div class='legend-item'><span class='legend-dot' style='background:#f59e0b;'></span><span><b>Waspada</b> (20% - 35%)</span></div>
            <div class='legend-item'><span class='legend-dot' style='background:#d05a4e;'></span><span><b>Kritis</b> (&gt; 35% Keluhan)</span></div>
            <div style='width: 100%; text-align: center; font-size: 11px; margin-top: 5px;'><i>*Ukuran lingkaran merepresentasikan total jumlah ulasan.</i></div>
        </div>
        """
    else:
        # Generate Legend untuk Dimensi
        legend_items = ""
        for dim, hex_color in WARNA_DIMENSI.items():
            if dim in df_filtered['dimensi_dominan'].unique(): # Tampilkan hanya yang ada di map
                legend_items += f"<div class='legend-item'><span class='legend-dot' style='background:{hex_color};'></span><span>{dim}</span></div>"
        
        legend_html = f"""
        <div class='legend-box'>
            {legend_items}
            <div style='width: 100%; text-align: center; font-size: 11px; margin-top: 5px;'><i>*Warna menunjukkan titik lemah pelayanan terparah pada faskes terkait.</i></div>
        </div>
        """
        
    st.markdown(legend_html, unsafe_allow_html=True)

else:
    st.warning("Data kosong untuk filter terpilih.")