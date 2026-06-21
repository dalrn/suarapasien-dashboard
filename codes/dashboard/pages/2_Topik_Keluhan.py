"""
Topik Keluhan se-Kabupaten — BACKBONE.

Tujuan halaman: pola keluhan di tingkat kabupaten (bukan per puskesmas) — mana
yang merata (perlu kebijakan dinas) vs lokal, dan bagaimana antar-wilayah.

Versi terisi sebelumnya diarsipkan di _archive/2_Topik_Keluhan_FILLED.py
Sumber data:
  - load_topik()            : persen keluhan & sebaran per dimensi, χ², lift
  - load_isu_kanonik()      : isu spesifik (hasil clustering) + jumlah ulasan
  - load_region_breakdown() : persen keluhan per dimensi per wilayah
"""
import streamlit as st
from lib.theme import setup
# nanti dipakai saat diisi: DIM_INFO, DIM_ORDER (lib.theme) ·
# load_topik, load_isu_kanonik, load_region_breakdown, dataset_stats (lib.data)

setup("Topik Keluhan")

st.markdown("<div class='page-title'>📊 Topik Keluhan se-Kabupaten</div>", unsafe_allow_html=True)
st.markdown("<div class='page-sub'>Mana keluhan yang merata di banyak puskesmas (perlu kebijakan "
            "dinas) dan mana yang lebih lokal — beserta pola antar-wilayah.</div>",
            unsafe_allow_html=True)

# ── 1. Seberapa luas tiap keluhan menyebar ───────────────────────────────
# Bar per dimensi: % ulasan-keluhan yang menyebut dimensi itu +
# "tersebar di N dari 127 puskesmas" + tag (perlu kebijakan dinas / lebih lokal).
st.info("**[1] Sebaran tiap dimensi** — bar % keluhan + jumlah puskesmas terdampak. *(belum diisi)*")

# ── 2. Keluhan paling umum se-kabupaten ──────────────────────────────────
# Daftar 10 isu spesifik teratas (hasil kanonikalisasi) + jumlah ulasan + tag dimensi.
st.info("**[2] Isu umum se-kabupaten** — top 10 isu spesifik + jumlah ulasan. *(belum diisi)*")

# ── 3. Apakah pola sama di tiap wilayah? ──────────────────────────────────
# Tabel dimensi × wilayah (% keluhan, dengan bar sel) +
# pernyataan hasil uji χ² (berbeda nyata / tidak) + tooltip penjelasan.
st.info("**[3] Pola antar-wilayah** — tabel dimensi×wilayah + uji χ². *(belum diisi)*")

# ── 4. Keluhan yang sering datang bersamaan ──────────────────────────────
# Narasi + daftar pasangan dimensi dengan lift > 1 (muncul bersamaan lebih sering
# dari kebetulan) → implikasi "benahi bersamaan".
st.info("**[4] Co-occurrence (lift)** — pasangan keluhan yang sering bersamaan. *(belum diisi)*")
