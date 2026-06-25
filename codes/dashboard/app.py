"""
SuaraPasien — Beranda. BACKBONE.

Entry script (otomatis jadi halaman pertama). Tujuan: sambutan + gambaran besar
sebelum pengguna masuk ke halaman lain.

Sumber data: dataset_stats() (jumlah puskesmas & wilayah)
"""
import streamlit as st
from lib.theme import setup
# nanti dipakai saat diisi: DIM_INFO, DIM_ORDER (lib.theme), dataset_stats (lib.data)

setup("Beranda")

# Hero
# Judul "SuaraPasien" + 1 paragraf: apa ini
# posisinya sebagai pelengkap akreditasi.
st.info("**[Hero]** — judul SuaraPasien + deskripsi singkat tujuan. *(belum diisi)*")

# Gambaran data

# Cara kerjanya
# 3 langkah: 1 Dengar (kumpulkan ulasan) · 2 Kelompokkan (pilah ke SERVQUAL) ·
# 3 Tampilkan (profil, topik, peta).

# Kerangka SERVQUAL
# 5 kartu dimensi (term + label ramah) dari DIM_INFO/DIM_ORDER.

# Navigasi & catatan
# Arahkan ke sidebar (Profil / Topik / Peringkat / Peta Mutu) + catatan keterbatasan data.