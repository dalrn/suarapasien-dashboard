"""
SuaraPasien — Beranda. BACKBONE.

Entry script (otomatis jadi halaman pertama). Tujuan: sambutan + gambaran besar
sebelum pengguna masuk ke halaman lain.

Versi terisi sebelumnya diarsipkan di _archive/app_FILLED.py
Sumber data: dataset_stats() (jumlah puskesmas & wilayah)
"""
import streamlit as st
from lib.theme import setup
# nanti dipakai saat diisi: DIM_INFO, DIM_ORDER (lib.theme) · dataset_stats (lib.data)

setup("Beranda")

# ── Hero ─────────────────────────────────────────────────────────────────
# Judul "SuaraPasien" + 1 paragraf: apa ini & untuk siapa (Dinkes / kepala puskesmas),
# posisinya sebagai pelengkap akreditasi.
st.info("**[Hero]** — judul SuaraPasien + deskripsi singkat tujuan. *(belum diisi)*")

# ── Gambaran data ────────────────────────────────────────────────────────
# 4 angka kunci: ulasan terkumpul (69.031) · ulasan 1–2★ dianalisis (8.641) ·
# jumlah puskesmas · jumlah wilayah.
st.info("**[Gambaran data]** — 4 statistik ringkas (ulasan, puskesmas, wilayah). *(belum diisi)*")

# ── Cara kerjanya ────────────────────────────────────────────────────────
# 3 langkah: 1 Dengar (kumpulkan ulasan) · 2 Kelompokkan (pilah ke SERVQUAL) ·
# 3 Tampilkan (profil, topik, peta).
st.info("**[Cara kerjanya]** — 3 langkah ringkas. *(belum diisi)*")

# ── Kerangka SERVQUAL ────────────────────────────────────────────────────
# 5 kartu dimensi (term + label ramah) dari DIM_INFO/DIM_ORDER.
st.info("**[Kerangka SERVQUAL]** — 5 dimensi (Responsiveness … Tangibles). *(belum diisi)*")

# ── Navigasi & catatan ───────────────────────────────────────────────────
# Arahkan ke sidebar (Profil / Topik / Peringkat / Peta Mutu) + catatan keterbatasan data.
st.info("**[Navigasi & catatan]** — petunjuk sidebar + disclaimer sumber data. *(belum diisi)*")
