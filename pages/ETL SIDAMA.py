import streamlit as st
from supabase import create_client, Client
from utils.excel_uploader import display_excel_uploader
from utils.api_extractor import display_api_extractor
from utils.get_connection import init_supabase_connection

st.set_page_config(page_title="SIDAMA ETL", layout="wide")

supabase = init_supabase_connection()

def sign_in(email, password):
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        st.session_state['user'] = res.user
        st.session_state['session'] = res.session
        st.rerun()
    except Exception as e:
        st.error(f"Gagal login: {e}")

if 'user' not in st.session_state:
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

    st.info("Silakan login")
    
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            sign_in(email, password)
    
else:

    st.title("SIDAMA ETL")
    st.markdown("Pilih metode ekstraksi data yang Anda inginkan di bawah ini.")

    if not supabase:
        st.error("Koneksi ke Supabase gagal. Harap periksa konfigurasi secrets Anda.")
    else:
        if 'active_tab' not in st.session_state:
            st.session_state.active_tab = "Upload Excel"
        col1, col2 = st.columns(2)

        with col1:
            button_type = "primary" if st.session_state.active_tab == "Upload Excel" else "secondary"
            if st.button("Upload Excel", type=button_type, use_container_width=True):
                st.session_state.active_tab = "Upload Excel"
                st.rerun()

        with col2:
            button_type = "primary" if st.session_state.active_tab == "API Extractor" else "secondary"
            if st.button("API Extractor", type=button_type, use_container_width=True):
                st.session_state.active_tab = "API Extractor"
                st.rerun()

        st.markdown("---") 

        if st.button("Logout"):
            supabase.auth.sign_out()
            del st.session_state['user']
            if 'session' in st.session_state:
                del st.session_state['session']
            st.rerun()

        if st.session_state.active_tab == "Upload Excel":
            display_excel_uploader(supabase) 
        elif st.session_state.active_tab == "API Extractor":
            display_api_extractor(supabase)


        with st.sidebar:
            if st.session_state.active_tab == "Upload Excel":
                st.title("Panduan Upload Excel")
                st.markdown("""
                1. **Pilih Tabel Tujuan**
                   Pilih tabel di database Supabase yang ingin Anda isi dengan data dari file Excel.
                2. **Download Template**
                    Unduh template Excel yang sesuai dengan struktur tabel yang dipilih.
                3. **Unggah File Excel yang Telah Diisi**
                    Unggah file Excel yang telah diisi sesuai template.
                """)
                st.info("Pastikan format data di Excel sesuai dengan tipe data di database.")

            elif st.session_state.active_tab == "API Extractor":
                st.title("Panduan Ekstraksi API")
                st.markdown("""
                1. **Daftarkan API**
                   Masukkan alias dan URL API eksternal yang ingin diambil datanya.
                2. **Ambil Data**
                   Klik tombol untuk mengambil data dari semua API yang telah didaftarkan.
                3. **(Opsional) Atur Join**
                   Jika ada lebih dari satu API, definisikan aturan join antar data.
                4. **Mapping Field**
                   Petakan field dari API ke kolom tabel Supabase yang dipilih.
                5. **Preview & Kirim Data**
                   Lihat preview hasil transformasi, lalu kirim data ke Supabase.
                """)
                st.info("Pastikan semua kolom wajib telah di-map sebelum mengirim data.")

