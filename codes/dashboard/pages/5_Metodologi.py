"""
Metodologi — BACKBONE.

Tujuan halaman: transparansi alur kerja (dari ulasan mentah → penilaian) dan
bukti keandalan model. Penting untuk konteks lomba/esai statistika: menunjukkan
proses yang dapat dipertanggungjawabkan.

Sumber data (sebagian dari outputs/statistik/ & laporan validasi):
  - angka κ antar-anotator, F1 dev vs held-out (Langkah 5/7)
  - ringkasan statistik (Wilson CI, Bayesian shrinkage, χ², lift)
"""
import streamlit as st
from lib.theme import setup

setup("Metodologi")

st.markdown("<div class='page-title'>📋 Metodologi & Keandalan</div>", unsafe_allow_html=True)

# 1. Alur Pengerjaan
#   1 Pengumpulan ulasan Google Maps
#   2 Pembersihan & audit (buang kosong/duplikat)
#   3 Pemecahan teks (chunking) per kalimat
#   4 Ekstraksi ABSA berbasis LLM (dimensi + polaritas + sub-isu + kutipan)
#   5 Validasi pelabelan (gold standard, 3 anotator, Cohen's κ)
#   6 Agregasi: proporsi + Wilson CI + Bayesian shrinkage -> tingkat keluhan
#   7 Statistik: χ² antar-wilayah, lift co-occurrence, clustering isu
#   8 Dashboard

# 2. Keandalan Model
# - Cohen's κ antar-anotator (deteksi & polaritas) + interpretasinya
# - F1 dev vs held-out (bukti tidak overfit)
# - akurasi polaritas
# Tampilkan sebagai metric + 1-2 kalimat interpretasi.

# 3. Metode Statistik yang Dipakai 
# Daftar ringkas + penjelasan awam: proporsi + Wilson CI, empirical-Bayes
# shrinkage, uji χ² independensi, lift co-occurrence, clustering embedding.

# 4. Catatan & Keterbatasan
# - data hanya ulasan 1–2 bintang -> 'profil keluhan', bukan skor kepuasan
# - sumber Google Maps -> penulis ulasan belum tentu mewakili semua pasien
# - sebagian Semarang dilabeli manual (kuota API) -> kolom 'sumber'