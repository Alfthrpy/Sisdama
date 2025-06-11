import streamlit as st
from supabase import create_client, Client
from utils.excel_uploader import display_excel_uploader
from utils.api_extractor import display_api_extractor

st.set_page_config(page_title="SIDAMA ETL", layout="wide")
@st.cache_resource
def init_supabase_connection():
    """Membuat dan mengembalikan koneksi Supabase."""
    try:
        supabase_url = st.secrets["SUPABASE_URL"]
        supabase_key = st.secrets["SUPABASE_KEY"]
        return create_client(supabase_url, supabase_key)
    except KeyError:
        return None

supabase = init_supabase_connection()

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

