"""SuaraPasien — Beranda. Entry script halaman utama penyambut dan gambaran umum data."""
import streamlit as st
from lib.theme import setup, DIM_INFO, DIM_ORDER
from lib.data import dataset_stats

# Inisialisasi halaman Beranda sesuai standar framework tim kalian
setup("Beranda")

# ==========================================
# CUSTOM CSS KONSISTENSI VISUAL Framework
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* Reset font global agar serasi dengan halaman profil */
    .reportview-container, .main, div, span, p {
        font-family: 'Inter', sans-serif;
    }
    
    /* Desain Elemen Hero */
    .hero-container {
        text-align: center;
        padding: 25px 10px 10px 10px;
    }
    .hero-title {
        font-size: 44px;
        font-weight: 700;
        color: #16202b;
        letter-spacing: -0.02em;
        margin-bottom: 8px;
    }
    .hero-sub {
        font-size: 15.5px;
        color: #64748b;
        max-width: 720px;
        margin: 0 auto;
        line-height: 1.6;
    }
    .hero-highlight {
        color: #d05a4e;
        font-weight: 600;
    }
    
    /* Kartu Metrik Ringkasan Data */
    .stat-card {
        background: #ffffff;
        border-radius: 14px;
        padding: 20px 15px;
        box-shadow: 0 1px 3px rgba(16,32,48,.07);
        text-align: center;
        border-bottom: 3.5px solid #185FA5;
    }
    .stat-val {
        font-size: 34px;
        font-weight: 700;
        color: #16202b;
        line-height: 1;
        margin-bottom: 4px;
    }
    .stat-lbl {
        font-size: 13px;
        color: #64748b;
        font-weight: 500;
    }
    
    /* Judul Sub-Section */
    .section-title {
        font-size: 19px;
        font-weight: 700;
        color: #16202b;
        margin: 35px 0 15px 0;
        letter-spacing: -0.01em;
    }
    
    /* Kartu Tiga Langkah Kerja */
    .step-card {
        background: #ffffff;
        border-radius: 14px;
        padding: 20px;
        box-shadow: 0 1px 3px rgba(16,32,48,.07);
        height: 100%;
        border-top: 3px solid #cbd5e1;
    }
    .step-num {
        font-size: 11.5px;
        font-weight: 700;
        color: #185FA5;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 5px;
    }
    .step-title {
        font-size: 15.5px;
        font-weight: 600;
        color: #16202b;
        margin-bottom: 8px;
    }
    .step-desc {
        font-size: 12.5px;
        color: #64748b;
        line-height: 1.55;
    }
    
    /* Kartu Dimensi SERVQUAL */
    .dim-card {
        background: #ffffff;
        border-radius: 14px;
        padding: 16px 22px;
        margin-bottom: 12px;
        box-shadow: 0 1px 3px rgba(16,32,48,.07);
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 15px;
    }
    .dim-term {
        font-size: 15.5px;
        font-weight: 700;
        color: #16202b;
        letter-spacing: -0.01em;
    }
    .dim-label {
        font-size: 13px;
        font-weight: 600;
        color: #475569;
        margin-top: 1px;
    }
    .dim-desc {
        font-size: 12px;
        color: #94a3b8;
        margin-top: 3px;
        line-height: 1.4;
    }
    .dim-badge {
        font-size: 11.5px;
        font-weight: 600;
        color: #185FA5;
        background: #eaf1f9;
        padding: 5px 12px;
        border-radius: 8px;
        white-space: nowrap;
    }
    
    /* Catatan Keterbatasan Data */
    .note-box {
        background: #f8fafc;
        border-left: 4px solid #cbd5e1;
        padding: 16px 20px;
        border-radius: 0 14px 14px 0;
        margin-top: 45px;
        font-size: 12.5px;
        color: #475569;
        line-height: 1.6;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 1. HERO SECTION
# ==========================================
hero_html = """
<div class="hero-container">
    <div class="hero-title">🩺 SuaraPasien</div>
    <div class="hero-sub">
        Platform Analisis Sentimen Terstruktur untuk Evaluasi Komprehensif Pelayanan Kesehatan Masyarakat. 
        Dirancang menggunakan pemodelan Natural Language Processing (NLP) berbasis aspek untuk mentransformasikan 
        ulasan publik menjadi instrumen <span class="hero-highlight">pelengkap akreditasi faskes</span> yang objektif dan real-time.
    </div>
</div>
"""
st.markdown(hero_html, unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# 2. GAMBARAN DATA (METRIK RINGKASAN)
# ==========================================
# Mengambil ringkasan statistik dataset secara aman (fleksibel jika return berupa dict/tuple)
stats = dataset_stats()
if isinstance(stats, dict):
    total_pkm = stats.get("n_puskesmas", stats.get("total_puskesmas", 0))
    total_wilayah = stats.get("n_wilayah", stats.get("total_wilayah", 0))
else:
    total_pkm, total_wilayah = stats

c1, c2 = st.columns(2)
with c1:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-val">{total_pkm}</div>
        <div class="stat-lbl">Puskesmas Teranalisis</div>
    </div>
    """, unsafe_allow_html=True)
with c2:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-val">{total_wilayah}</div>
        <div class="stat-lbl">Wilayah Administratif</div>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 3. CARA KERJA PIPELINE SYSTEM
# ==========================================
st.markdown("<div class='section-title'>⚙️ Bagaimana SuaraPasien Bekerja?</div>", unsafe_allow_html=True)

step1, step2, step3 = st.columns(3)
with step1:
    st.markdown("""
    <div class="step-card">
        <div class="step-num">Langkah 1</div>
        <div class="step-title">📥 Dengar</div>
        <div class="step-desc">Mengekstraksi narasi umpan balik publik secara masif langsung dari ulasan faskes di Google Maps tanpa batasan kuantitatif formal.</div>
    </div>
    """, unsafe_allow_html=True)

with step2:
    st.markdown("""
    <div class="step-card" style="border-top-color: #185FA5;">
        <div class="step-num">Langkah 2</div>
        <div class="step-title">🤖 Kelompokkan</div>
        <div class="step-desc">Menggunakan Large Language Model (LLM) tingkat lanjut untuk memilah teks keluhan mentah ke dalam klaster taksonomi mutu internasional.</div>
    </div>
    """, unsafe_allow_html=True)

with step3:
    st.markdown("""
    <div class="step-card" style="border-top-color: #2f9e6f;">
        <div class="step-num">Langkah 3</div>
        <div class="step-title">📊 Tampilkan</div>
        <div class="step-desc">Menyajikan profil performa faskes, peta klaster kuadran anomali mutu, hingga sebaran topik keluhan kritis untuk rekomendasi kebijakan.</div>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 4. KERANGKA KERJA SERVQUAL (DIMENSI MUTU)
# ==========================================
st.markdown("<div class='section-title'>📋 Dimensi Mutu yang Dievaluasi (SERVQUAL)</div>", unsafe_allow_html=True)

for key in DIM_ORDER:
    if key in DIM_INFO:
        label, desc, short = DIM_INFO[key]
        st.markdown(f"""
        <div class="dim-card">
            <div class="dim-left">
                <div class="dim-term">{key} <span style="font-weight:400; color:#64748b; font-size:13px;">({short})</span></div>
                <div class="dim-label">{label}</div>
                <div class="dim-desc">{desc}</div>
            </div>
            <div class="dim-badge">Dimensi Analisis</div>
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# 5. NAVIGASI SIDEBAR & KETERBATASAN DATA
# ==========================================
st.markdown(f"""
<div class="note-box">
    💡 <b>Petunjuk Navigasi:</b> Silakan gunakan panel menu di sebelah kiri layar untuk mengeksplorasi analisis mendalam secara interaktif: 
    <b>Profil Puskesmas</b> untuk analisis individu faskes, <b>Analisis Topik</b> untuk tren sebaran narasi, atau <b>Peta Mutu</b> untuk melihat anomali sebaran rating spasial.<br><br>
    ⚠️ <b>Catatan Keterbatasan Data:</b> Seluruh analisis dalam platform ini dibangun berdasarkan data umpan balik masyarakat yang tersedia secara digital pada platform Google Maps. 
    Instrumen ini ditujukan sebagai data sekunder objektif untuk melengkapi metode survei konvensional di lapangan.
</div>
""", unsafe_allow_html=True)