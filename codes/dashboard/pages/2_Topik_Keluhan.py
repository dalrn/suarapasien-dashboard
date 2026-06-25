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
from lib.theme import setup
# nanti dipakai saat diisi: DIM_INFO, DIM_ORDER (lib.theme) ·
# load_topik, load_isu_kanonik, load_region_breakdown, dataset_stats (lib.data)

setup("Topik Keluhan")

st.markdown("<div class='page-title'>📊 Topik Keluhan se-Kabupaten</div>", unsafe_allow_html=True)

# 1. Seberapa luas tiap keluhan menyebar
# Bar per dimensi: % ulasan-keluhan yang menyebut dimensi itu +
# "tersebar di N dari 127 puskesmas" + tag (perlu kebijakan dinas / lebih lokal).

# 2. Keluhan paling umum se-kabupaten
# Daftar 10 isu spesifik teratas (hasil kanonikalisasi) + jumlah ulasan + tag dimensi.

# 3. Apakah pola sama di tiap wilayah?
# Tabel dimensi × wilayah (% keluhan, dengan bar sel) +
# pernyataan hasil uji χ² (berbeda nyata / tidak) + tooltip penjelasan.

#  4. Keluhan yang sering datang bersamaan
# Narasi + daftar pasangan dimensi dengan lift > 1 (muncul bersamaan lebih sering
# dari kebetulan) -> implikasi "benahi bersamaan".