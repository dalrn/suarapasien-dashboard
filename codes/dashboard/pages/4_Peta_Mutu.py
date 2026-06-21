"""
Peta Mutu — BACKBONE.

Tujuan halaman: memposisikan SEMUA puskesmas dalam satu ruang sekaligus, dan
menyorot ketidaksesuaian "bintang tinggi tapi banyak keluhan" (menggantikan tab
Sinyal pada mock-up). Ini visualisasi paling "hidup" — tesis inti proyek jadi
pola yang bisa dilihat & diklik.

Sumber data:
  - load_gmaps_meta() : rating bintang & jumlah ulasan (sumbu X + ukuran titik)
  - compute_rankings()/load_profiles() : tingkat keluhan dari teks (sumbu Y)
"""
import streamlit as st
from lib.theme import setup
from lib.data import load_profiles, load_gmaps_meta, compute_rankings

setup("Peta Mutu")

st.markdown("<div class='page-title'>🗺️ Peta Mutu Puskesmas</div>", unsafe_allow_html=True)
st.markdown("<div class='page-sub'>Setiap titik = satu puskesmas. Sumbu mendatar = rating bintang "
            "Google Maps, sumbu tegak = tingkat keluhan dari isi ulasan. Kuadran kanan-bawah = "
            "<b>bintang tinggi tapi banyak keluhan</b> — sinyal yang perlu diperhatikan.</div>",
            unsafe_allow_html=True)

# ── 1. Kontrol ───────────────────────────────────────────────────────────
# - multiselect Wilayah (filter titik)
# - "Warnai berdasarkan": Wilayah / tingkat keluhan
# - multiselect "Sorot puskesmas tertentu"
st.info("**[1] Kontrol** — filter wilayah · warnai berdasarkan · sorot puskesmas. *(belum diisi)*")

# ── 2. Scatter kuadran ───────────────────────────────────────────────────
# Plotly scatter:
#   x = rating bintang (1–5), y = % ulasan berkeluhan (tingkat keluhan teks)
#   ukuran titik = jumlah ulasan, warna = wilayah
#   garis median x & y (putus) → membagi 4 kuadran, tiap kuadran diberi label & warna latar:
#     kanan-bawah  : bintang tinggi + keluhan rendah  → "Benar-benar baik"
#     kanan-atas   : bintang tinggi + keluhan tinggi  → "MENYESATKAN (sinyal)"
#     kiri-bawah   : bintang rendah + keluhan rendah  → "sepi data / netral"
#     kiri-atas    : bintang rendah + keluhan tinggi  → "konsisten buruk"
#   hover → nama, rating, % keluhan, jumlah ulasan; klik → Profil
st.info("**[2] Scatter kuadran** — bintang vs keluhan, median + 4 kuadran berlabel (Plotly). *(belum diisi)*")

# ── 3. Puskesmas menonjol per kuadran ────────────────────────────────────
# 4 kolom (satu per kuadran), tiap kolom daftar puskesmas + angka kunci.
# Penekanan pada kuadran "MENYESATKAN" — daftar puskesmas bintang tinggi tapi banyak keluhan.
st.info("**[3] Menonjol per kuadran** — 4 kolom daftar puskesmas, fokus kuadran 'menyesatkan'. *(belum diisi)*")

# ── 4. Observasi dari Data ───────────────────────────────────────────────
# Kartu insight otomatis (mis. "12 puskesmas bintang ≥4 tapi >50% ulasan berkeluhan",
# "korelasi bintang vs keluhan teks lemah → bintang saja tidak cukup").
st.info("**[4] Observasi dari Data** — kartu insight naratif otomatis. *(belum diisi)*")

# Catatan: peta GEOGRAFIS (Leaflet) butuh koordinat puskesmas yang belum tersedia
# (puskesmas_url hanya tautan pencarian). Bisa ditambah nanti bila koordinat digeocode.
