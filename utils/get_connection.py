from supabase import create_client
import streamlit as st

@st.cache_resource
def init_supabase_connection():
    """Membuat dan mengembalikan koneksi Supabase."""
    try:
        supabase_url = st.secrets["SUPABASE_URL"]
        supabase_key = st.secrets["SUPABASE_KEY"]
        return create_client(supabase_url, supabase_key)
    except KeyError:
        return None