import streamlit as st
from supabase import create_client, Client
from utils.excel_uploader import display_excel_uploader
from utils.api_extractor import display_api_extractor

st.set_page_config(page_title="SIDAMA: Sistem Integrasi Data Mahasiswa", layout="wide")
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

st.title("SIDAMA Extractor")
st.markdown("Pilih metode ekstraksi data yang Anda inginkan di bawah ini.")

if not supabase:
    st.error("Koneksi ke Supabase gagal. Harap periksa konfigurasi secrets Anda.")
else:
    tab_excel, tab_api = st.tabs(["📤 Upload via Excel", "🔗 Ekstrak dari API"])

    with tab_excel:
        display_excel_uploader(supabase)

    with tab_api:
        display_api_extractor(supabase)