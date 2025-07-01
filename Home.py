import streamlit as st

# Mengatur konfigurasi halaman agar lebih lebar dan menarik
st.set_page_config(
    page_title="Beranda - SIDAMA",
    page_icon="🎓",
    layout='wide'
)

# Custom CSS untuk styling yang lebih menarik
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* Global styling */
    .stApp {
        font-family: 'Inter', sans-serif;
    }
    
    /* Header styling */
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        margin: -1rem -1rem 2rem -1rem;
        color: white;
        border-radius: 0 0 20px 20px;
    }
    
    .main-header h1 {
        font-size: 3rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .main-header p {
        font-size: 1.2rem;
        font-weight: 400;
        opacity: 0.95;
        margin-bottom: 0;
    }
    
    /* Feature cards */
    .feature-card {
        background: linear-gradient(145deg, #ffffff 0%, #f8f9ff 100%);
        padding: 2rem;
        border-radius: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        border: 1px solid rgba(255,255,255,0.2);
        transition: all 0.3s ease;
        height: 100%;
        min-height: 280px;
        position: relative;
        overflow: hidden;
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 20px 40px rgba(0,0,0,0.15);
    }
    
    .feature-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #ff6b6b, #4ecdc4, #45b7d1);
        border-radius: 20px 20px 0 0;
    }
    
    .feature-card h3 {
        font-size: 1.4rem;
        font-weight: 600;
        margin-bottom: 1rem;
        color: #2c3e50;
        text-align: center;
    }
    
    .feature-card p {
        font-size: 1rem;
        line-height: 1.6;
        color: #34495e;
        text-align: center;
        margin-bottom: 0;
    }
    
    /* Specific card colors */
    .card-analysis::before {
        background: linear-gradient(90deg, #ff6b6b, #ff8e8e);
    }
    
    .card-warning::before {
        background: linear-gradient(90deg, #ffa726, #ffcc02);
    }
    
    .card-scholarship::before {
        background: linear-gradient(90deg, #4ecdc4, #44a08d);
    }
    
    /* Stats section */
    .stats-container {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 2rem;
        border-radius: 20px;
        margin: 2rem 0;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }
    
    .stat-item {
        text-align: center;
        padding: 1rem;
    }
    
    .stat-number {
        font-size: 2.5rem;
        font-weight: 700;
        color: #667eea;
        display: block;
    }
    
    .stat-label {
        font-size: 1rem;
        color: #34495e;
        font-weight: 500;
    }
    
    /* Call to action */
    .cta-section {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 20px;
        text-align: center;
        color: white;
        margin: 2rem 0;
    }
    
    .cta-section h3 {
        font-size: 1.5rem;
        margin-bottom: 1rem;
        font-weight: 600;
    }
    
    .cta-section p {
        font-size: 1.1rem;
        opacity: 0.9;
        margin-bottom: 0;
    }
    
    /* Icon styling */
    .feature-icon {
        font-size: 3rem;
        display: block;
        margin-bottom: 1rem;
        text-align: center;
    }
    
    /* Responsive adjustments */
    @media (max-width: 768px) {
        .main-header h1 {
            font-size: 2rem;
        }
        .main-header p {
            font-size: 1rem;
        }
        .feature-card {
            min-height: 250px;
        }
    }
</style>
""", unsafe_allow_html=True)

# --- Header Section ---
st.markdown("""
<div class="main-header">
    <h1>🎓 SIDAMA</h1>
    <p>Platform Analitik Cerdas untuk Kesuksesan Akademik Mahasiswa</p>
</div>
""", unsafe_allow_html=True)

# --- Penjelasan Singkat ---
st.markdown("""
<div style="text-align: center; padding: 1rem 0 2rem 0;">
    <h2 style="color: #3a5ba0; font-weight: 600; margin-bottom: 1rem;">Transformasi Data Menjadi Insight Berharga</h2>
    <p style="font-size: 1.1rem; color: #34495e; max-width: 800px; margin: 0 auto; line-height: 1.6;">
        <strong>SIDAMA (Sistem Data Mahasiswa)</strong> mengubah data mentah akademik menjadi <strong>wawasan actionable</strong> 
        yang membantu universitas secara proaktif mendukung perjalanan studi setiap mahasiswa menuju kesuksesan.
    </p>
</div>
""", unsafe_allow_html=True)

# --- Statistics Section ---
col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)


st.markdown("<br>", unsafe_allow_html=True)

# --- Fitur Unggulan ---
st.markdown("<h2 style='text-align: center; color: #3a5ba0; font-weight: 600; margin-bottom: 2rem;'>Fitur Unggulan Kami</h2>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3, gap="large")

with col1:
    st.markdown("""
    <div class="feature-card card-analysis">
        <div class="feature-icon">🎯</div>
        <h3>Analisis Pola Studi</h3>
        <p>
            Deteksi potensi <strong>keterlambatan studi</strong> dengan menganalisis tren pengambilan SKS per semester. 
            Berikan bimbingan akademik yang lebih <strong>proaktif dan tepat sasaran</strong> dengan algoritma machine learning terdepan.
        </p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-card card-warning">
        <div class="feature-icon">⚠️</div>
        <h3>Sistem Peringatan Dini</h3>
        <p>
            Identifikasi mahasiswa <strong>berisiko penurunan performa</strong> atau drop-out secara otomatis. 
            Dapatkan <strong>rekomendasi intervensi real-time</strong> untuk dosen wali dengan tingkat akurasi hingga 98%.
        </p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="feature-card card-scholarship">
        <div class="feature-icon">💰</div>
        <h3>Evaluasi Efektivitas Beasiswa</h3>
        <p>
            Ukur <strong>dampak nyata beasiswa</strong> terhadap prestasi dan retensi mahasiswa. 
            Pastikan bantuan tersalurkan kepada pihak yang <strong>paling membutuhkan dan berdampak</strong> maksimal.
        </p>
    </div>
    """, unsafe_allow_html=True)

# --- Additional Features Row ---
st.markdown("<br><br>", unsafe_allow_html=True)

col4, col5 = st.columns(2, gap="large")

with col4:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">📊</div>
        <h3>Dashboard Interaktif</h3>
        <p>
            Visualisasi data yang intuitif dan real-time untuk memudahkan pengambilan keputusan strategis 
            oleh pihak akademik dan manajemen universitas.
        </p>
    </div>
    """, unsafe_allow_html=True)

with col5:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">🤖</div>
        <h3>Ekstraksi Data yang Fleksibel</h3>
        <p>
            Pilih metode ekstraksi data: <strong>unggah file Excel</strong> atau <strong>API eksternal</strong>. 
            Integrasi mudah dengan sistem yang sudah ada untuk memaksimalkan potensi data akademik Anda.
        </p>
    </div>
    """, unsafe_allow_html=True)

# --- Call to Action ---
st.markdown("""
<div class="cta-section">
    <h3>Siap Memulai Perjalanan Analitik Anda?</h3>
    <p>Gunakan menu navigasi di sebelah kiri untuk mengakses fitur-fitur yang tersedia dan mulai transformasi digital institusi Anda!</p>
</div>
""", unsafe_allow_html=True)

# --- Footer ---
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("""
<div style="text-align: center; padding: 2rem 0; color: #7f8c8d; border-top: 1px solid #ecf0f1; margin-top: 2rem;">
    <p>© 2025 SIDAMA - Sistem Data Mahasiswa </p>
</div>
""", unsafe_allow_html=True)