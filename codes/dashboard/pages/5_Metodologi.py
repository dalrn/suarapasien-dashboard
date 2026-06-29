"""Metodologi — BACKBONE. Transparansi alur kerja dan bukti keandalan model statistik."""
import streamlit as st
from lib.theme import setup

# Inisialisasi halaman
setup("Metodologi")

# ==========================================
# CUSTOM CSS KONSISTENSI VISUAL Framework
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    .reportview-container, .main, div, span, p {
        font-family: 'Inter', sans-serif;
    }
    
    .section-title {
        font-size: 21px;
        font-weight: 700;
        color: #16202b;
        margin: 35px 0 15px 0;
        letter-spacing: -0.01em;
        border-bottom: 2px solid #eef1f4;
        padding-bottom: 8px;
    }
    
    /* Kartu Alur Kerja */
    .flow-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 12px;
        box-shadow: 0 1px 3px rgba(16,32,48,.05);
        border-left: 4px solid #185FA5;
    }
    .flow-step {
        font-size: 11.5px;
        font-weight: 700;
        color: #185FA5;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 4px;
    }
    .flow-title {
        font-size: 15px;
        font-weight: 600;
        color: #16202b;
        margin-bottom: 6px;
    }
    .flow-desc {
        font-size: 13px;
        color: #475569;
        line-height: 1.5;
    }
    .flow-desc a {
        color: #185FA5;
        font-weight: 600;
        text-decoration: none;
        border-bottom: 1px dashed #aac4e0;
    }
    .flow-desc a:hover {
        border-bottom-style: solid;
    }

    /* Kartu Metrik Keandalan */
    .metric-box {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        height: 100%;
    }
    .metric-value {
        font-size: 32px;
        font-weight: 700;
        color: #0f766e;
        margin-bottom: 5px;
    }
    .metric-label {
        font-size: 13px;
        font-weight: 600;
        color: #334155;
    }
    .metric-desc {
        font-size: 11.5px;
        color: #64748b;
        margin-top: 8px;
        line-height: 1.4;
    }
    
    /* Keterbatasan Data */
    .note-box {
        background: #fff1f2;
        border-left: 4px solid #e11d48;
        padding: 20px 24px;
        border-radius: 0 14px 14px 0;
        margin-top: 20px;
    }
    .note-title {
        font-size: 14px;
        font-weight: 700;
        color: #be123c;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .note-content {
        font-size: 13px;
        color: #4c0519;
        line-height: 1.6;
    }
    .note-list {
        margin: 8px 0 0 18px;
        padding: 0;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='page-title'>Metodologi & Keandalan</div>", unsafe_allow_html=True)
st.markdown("<div class='page-sub'>Transparansi alur kerja data (dari ulasan mentah hingga penilaian analitik) serta bukti keandalan model statistik yang dapat dipertanggungjawabkan secara akademis.</div>", unsafe_allow_html=True)

# ==========================================
# 1. ALUR PENGERJAAN (PIPELINE)
# ==========================================
st.markdown("<div class='section-title'>1. Alur Pengerjaan (Data Pipeline)</div>", unsafe_allow_html=True)

st.markdown("""
<div class="flow-card">
    <div class="flow-step">Tahap 1 & 2</div>
    <div class="flow-title">Pengumpulan & Prapemrosesan Ulasan Google Maps</div>
    <div class="flow-desc">
        Menggunakan <a href="https://console.apify.com/actors/Xb8osYTtOjlsgI6k9" target="_blank" rel="noopener"><i>Apify Google Maps Reviews Scraper</i></a>, berhasil diekstraksi <b>69.031 observasi data</b> dari Bantul, Semarang, dan Surabaya.
        Data kemudian direduksi menjadi <b>8.641 ulasan</b> dengan melakukan pembersihan duplikat, penghapusan ulasan non-teks/emotikon, dan pemfilteran spesifik pada <b>rating bintang 1 dan 2</b> (fokus pada <i>complaint mining</i>).
    </div>
</div>

<div class="flow-card">
    <div class="flow-step">Tahap 3 & 4</div>
    <div class="flow-title">Pemecahan Teks (Chunking) & Ekstraksi ABSA</div>
    <div class="flow-desc">
        Ulasan panjang dipecah batas kalimat/paragraf (maks. 700 karakter) menghasilkan <b>9.113 potongan teks</b>. 
        Potongan teks diekstraksi menggunakan <i>Aspect-Based Sentiment Analysis</i> (ABSA) berbasis LLM Claude untuk memetakan: dimensi SERVQUAL, polaritas, sub-isu keluhan, dan kutipan spesifik (bersifat <i>multi-label</i>).
    </div>
</div>

<div class="flow-card">
    <div class="flow-step">Tahap 5</div>
    <div class="flow-title">Validasi Pelabelan (Gold Standard)</div>
    <div class="flow-desc">
        Dilakukan sampling 200 ulasan acak dengan <i>Square-root stratified allocation</i>. Ketiga peneliti melakukan anotasi manual secara buta (<i>blind</i>). 
        Konsistensi antar-anotator diukur, dan <i>Majority Vote</i> digunakan sebagai <i>Ground Truth</i> untuk mengkalibrasi dan mengevaluasi <i>prompt</i> LLM secara iteratif.
    </div>
</div>

<div class="flow-card">
    <div class="flow-step">Tahap 6 & 7</div>
    <div class="flow-title">Inferensi Statistik & Dashboarding</div>
    <div class="flow-desc">
        Pelabelan akhir diagregasi menjadi proporsi keluhan yang dikalibrasi menggunakan rentang interval konfidensi dan penyusutan Bayesian untuk kestabilan faskes bersampel kecil, dilanjutkan dengan pengujian dependensi antar-wilayah.
    </div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 2. KEANDALAN MODEL
# ==========================================
st.markdown("<div class='section-title'>2. Bukti Keandalan Model LLM</div>", unsafe_allow_html=True)

m1, m2, m3 = st.columns(3)
with m1:
    st.markdown("""
    <div class="metric-box">
        <div class="metric-value">κ = 0,74</div>
        <div class="metric-label">Konsistensi Anotator (Cohen's κ)</div>
        <div class="metric-desc">Tingkat kesepakatan murni antar 3 peneliti (di luar faktor kebetulan) dalam menentukan dimensi layanan.</div>
    </div>
    """, unsafe_allow_html=True)
with m2:
    st.markdown("""
    <div class="metric-box">
        <div class="metric-value">0,745 → 0,724</div>
        <div class="metric-label">Macro-F1 (Val vs Test)</div>
        <div class="metric-desc">Diuji pada 114 <i>test data</i> yang belum pernah dilihat model (CI95% [0,637 – 0,786]).</div>
    </div>
    """, unsafe_allow_html=True)
with m3:
    st.markdown("""
    <div class="metric-box">
        <div class="metric-value">96,5%</div>
        <div class="metric-label">Akurasi Polaritas Sentimen</div>
        <div class="metric-desc">Model secara akurat mendeteksi nuansa negatif/keluhan yang bersembunyi di balik gaya bahasa informal.</div>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 3. METODE STATISTIK YANG DIPAKAI
# ==========================================
st.markdown("<div class='section-title'>3. Landasan Inferensi Statistik</div>", unsafe_allow_html=True)

st.markdown("""
<style>
    .stat-card {
        background: #ffffff;
        border-radius: 14px;
        padding: 18px 22px;
        margin-bottom: 14px;
        box-shadow: 0 1px 3px rgba(16,32,48,.05);
        border: 1px solid #eef1f4;
    }
    .stat-card-title {
        font-size: 14.5px;
        font-weight: 700;
        color: #16202b;
        margin-bottom: 8px;
    }
    .stat-desc {
        font-size: 13px;
        color: #475569;
        line-height: 1.6;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="stat-card">
    <div class="stat-card-title">Cohen's Kappa</div>
    <div class="stat-desc">Mengukur reliabilitas kesepakatan antar-anotator dalam menentukan dimensi
    SERVQUAL pada satu ulasan, dengan probabilitas kesepakatan karena kebetulan sudah dihilangkan
    dari skornya sehingga angka yang dihasilkan benar-benar merefleksikan konsistensi penilaian.</div>
</div>

<div class="stat-card">
    <div class="stat-card-title">Empirical Bayes Shrinkage</div>
    <div class="stat-desc">Puskesmas ber-ulasan sedikit (misal 2 ulasan, semua mengeluh → 100%)
    proporsinya ditarik (<i>shrink</i>) ke arah rata-rata kabupaten, sehingga tidak di-ranking
    berdasarkan kebetulan sampel kecil.</div>
</div>

<div class="stat-card">
    <div class="stat-card-title">Wilson Score Confidence Interval</div>
    <div class="stat-desc">Selang kepercayaan tingkat keluhan dihitung memakai Wilson Score Interval,
    jauh lebih stabil untuk proporsi ekstrem (dekat 0% atau 100%) dibanding interval standar,
    penting karena banyak puskesmas hanya memiliki sedikit ulasan.</div>
</div>

<div class="stat-card">
    <div class="stat-card-title">Uji Z Dua Proporsi</div>
    <div class="stat-desc">Membandingkan tingkat keluhan satu puskesmas dengan gabungan seluruh
    puskesmas lain (peer). Label "lebih sering dikeluhkan" hanya diberikan bila hasilnya signifikan
    secara statistik (p &lt; 0,05), bukan sekadar selisih angka mentah.</div>
</div>

<div class="stat-card">
    <div class="stat-card-title">KMeans Clustering dengan Semantic Embedding</div>
    <div class="stat-desc">Untuk menyatukan ribuan frasa keluhan jadi isu kanonik, tiap frasa diubah
    jadi <i>semantic embedding</i> lalu dikelompokkan dengan KMeans. Jumlah klaster optimal dipilih
    dari Silhouette Score tertinggi, sehingga klaster yang terbentuk benar-benar koheren secara makna.</div>
</div>

<div class="stat-card">
    <div class="stat-card-title">Association Rules Lift</div>
    <div class="stat-desc">Mengukur apakah dua keluhan (misal antrean lama &amp; petugas tidak ramah)
    muncul bersamaan dalam satu ulasan lebih sering daripada yang diharapkan secara kebetulan.
    Lift &gt; 1 berarti asosiasinya nyata dan kedua isu butuh solusi yang simultan.</div>
</div>

<div class="stat-card">
    <div class="stat-card-title">Uji Chi-Square Independensi</div>
    <div class="stat-desc">Menguji apakah distribusi dimensi keluhan bergantung pada wilayah geografis,
    dilanjutkan analisis standardized residual untuk menandai kombinasi wilayah×dimensi yang paling
    menyimpang dari pola gabungan.</div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 4. CATATAN KETERBATASAN DATA (REVISI FINAL)
# ==========================================
st.markdown("<div class='section-title'>4. Dekonstruksi Keterbatasan Data & Metodologi</div>", unsafe_allow_html=True)
st.caption("Sebagai bentuk transparansi ilmiah, berikut adalah penjabaran mendalam mengenai batasan ruang lingkup, model, dan sifat spasial dari dataset yang digunakan dalam penelitian ini:")

# Injeksi CSS khusus untuk membuat elemen kartu limitasi yang bebas, bersih, dan berjarak lega
st.markdown("""
<style>
    .limit-card {
        background: #ffffff;
        border-radius: 14px;
        padding: 22px 26px;
        margin-bottom: 18px;
        box-shadow: 0 1px 4px rgba(16,32,48,.05);
        border-left: 4px solid #f43f5e;
    }
    .limit-badge {
        display: inline-block;
        font-size: 11px;
        font-weight: 700;
        color: #e11d48;
        background: #fff1f2;
        padding: 3px 10px;
        border-radius: 6px;
        text-transform: uppercase;
        letter-spacing: 0.03em;
        margin-bottom: 8px;
    }
    .limit-title {
        font-size: 16px;
        font-weight: 700;
        color: #16202b;
        margin-bottom: 8px;
        letter-spacing: -0.01em;
    }
    .limit-desc {
        font-size: 13px;
        color: #475569;
        line-height: 1.65;
    }
    .limit-highlight {
        font-weight: 600;
        color: #b91c1c;
    }
</style>
""", unsafe_allow_html=True)

# Kartu 1: Sumber Data Tunggal
st.markdown("""
<div class="limit-card">
    <div class="limit-badge">Data Source Bias</div>
    <div class="limit-title">1. Keterbatasan Sumber Data Tunggal (Eksklusivitas Digital)</div>
    <div class="limit-desc">
        Platform ini dibangun <span class="limit-highlight">eksklusif menggunakan data publik dari ulasan Google Maps</span>. 
        Secara metodologis, pendekatan ini tidak melibatkan instrumen survei konvensional secara tatap muka (seperti Indeks Kepuasan Masyarakat formal). 
        Hal ini memicu adanya <i>self-selection bias</i>, di mana populasi data didominasi oleh pengguna yang lebih melek digital dan secara sukarela tergerak untuk menulis opini, sehingga berpotensi mengeksklusi suara dari kelompok demografi lansia atau masyarakat prasejahtera yang tidak menggunakan <b>smartphone</b>.
    </div>
</div>
""", unsafe_allow_html=True)

# Kartu 2: Representasi Wilayah
st.markdown("""
<div class="limit-card" style="border-left-color: #f59e0b;">
    <div class="limit-badge" style="color: #d97706; background: #fef3c7;">Geographical Restraint</div>
    <div class="limit-title">2. Batasan Representasi Wilayah Kriteria Klasifikasi</div>
    <div class="limit-desc">
        Cakupan wilayah analisis spasial dalam penelitian ini dibatasi pada tiga area utama, yaitu <span class="limit-highlight">Kabupaten Bantul, Kota Semarang, dan Kota Surabaya</span>. 
        Meskipun ketiga wilayah ini dipilih secara sengaja (<i>purposive sampling</i>) untuk mewakili tipologi karakteristik daerah berskala kecil, sedang, dan besar, hasil temuan analitik pada dashboard ini tidak dapat digeneralisasi secara mutlak sebagai representasi pelayanan kesehatan nasional, mengingat adanya disparitas regulasi faskes dan kapasitas fiskal daerah yang berbeda di luar objek riset.
    </div>
</div>
""", unsafe_allow_html=True)

# Kartu 3: Fokus Analisis (Rating 1 & 2)
st.markdown("""
<div class="limit-card" style="border-left-color: #6366f1;">
    <div class="limit-badge" style="color: #4f46e5; background: #e0e7ff;">Truncation Bias</div>
    <div class="limit-title">3. Fokus Analisis Spesifik Berbasis Negativity Bias</div>
    <div class="limit-desc">
        Sistem analisis sentimen terstruktur (ABSA) pada platform ini secara sengaja memotong populasi data dan <span class="limit-highlight">hanya mengekstraksi teks ulasan dengan rating rendah (bintang 1 dan 2)</span>. 
        Justifikasi riset ini mengacu pada konsep <i>complaint mining</i> guna mendeteksi titik kritis (<i>pain-point detection</i>) secara tajam. Dampak metodologisnya, dashboard ini <b>tidak menyajikan skor kepuasan global</b> atau performa keberhasilan pelayanan, melainkan murni memetakan pola dan anatribusi kegagalan operasional faskes yang butuh tindakan korektif segera.
    </div>
</div>
""", unsafe_allow_html=True)

# Kartu 4: Data Statis (Temporal)
st.markdown("""
<div class="limit-card" style="border-left-color: #0d9488; margin-bottom: 30px;">
    <div class="limit-badge" style="color: #0f766e; background: #ccfbf1;">Temporal Constraint</div>
    <div class="limit-title">4. Sifat Dataset Statis (Cross-Sectional Snapshot)</div>
    <div class="limit-desc">
        Data yang disajikan merupakan hasil penarikan batch statis (<i>snapshot data</i>) yang dikunci per tanggal <span class="limit-highlight"><b>17 Mei 2026</b></span>. 
        Konsekuensinya, dashboard ini tidak bersifat <i>real-time streaming</i> dan tidak merekam atau memperbarui ulasan-ulasan baru yang masuk ke Google Maps setelah tanggal cut-off tersebut. Segala bentuk perbaikan layanan atau perubahan operasional nyata yang telah dilakukan oleh Puskesmas terkait setelah periode penarikan data tidak akan terefleksi dalam visualisasi kuadran performa saat ini.
    </div>
</div>
""", unsafe_allow_html=True)