"""
Peta Mutu — BACKBONE.

Tujuan halaman: memposisikan SEMUA puskesmas dalam satu ruang sekaligus, dan
menyorot ketidaksesuaian "bintang tinggi tapi banyak keluhan".

Sumber data:
  - load_gmaps_meta() : rating bintang & jumlah ulasan (sumbu X + ukuran titik)
  - compute_rankings()/load_profiles() : tingkat keluhan dari teks (sumbu Y)
"""
import streamlit as st
from lib.theme import setup
from lib.data import load_profiles, load_gmaps_meta, compute_rankings

setup("Peta Mutu")

st.markdown("<div class='page-title'>🗺️ Peta Mutu Puskesmas</div>", unsafe_allow_html=True)

# 1. Kontrol
# - multiselect Wilayah (filter titik)
# - "Warnai berdasarkan": Wilayah / tingkat keluhan
# - multiselect "Sorot puskesmas tertentu"

# 2. Scatter kuadran
# Plotly scatter:
#   x = rating bintang (1–5), y = % ulasan berkeluhan (tingkat keluhan teks)
#   ukuran titik = jumlah ulasan, warna = wilayah
#   garis median x & y (putus) → membagi 4 kuadran, tiap kuadran diberi label & warna latar:
#     kanan-bawah  : bintang tinggi + keluhan rendah  -> "Benar-benar baik"
#     kanan-atas   : bintang tinggi + keluhan tinggi  -> "MENYESATKAN (sinyal)"
#     kiri-bawah   : bintang rendah + keluhan rendah  -> "sepi data / netral"
#     kiri-atas    : bintang rendah + keluhan tinggi  -> "konsisten buruk"
#   hover -> nama, rating, % keluhan, jumlah ulasan; klik -> Profil

# 3. Puskesmas menonjol per kuadran

# 4. Observasi Naratif dari Data

# Catatan: peta GEOGRAFIS (Leaflet) butuh koordinat puskesmas yang belum tersedia
# (puskesmas_url hanya tautan pencarian). Bisa ditambah nanti bila koordinat digeocode.