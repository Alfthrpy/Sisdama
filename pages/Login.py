import streamlit as st
from utils.get_connection import init_supabase_connection

# Inisialisasi koneksi Supabase
supabase = init_supabase_connection()

# Cek apakah sudah login
if st.session_state.get("authenticated", False):
    st.success("✅ Anda sudah login.")
    st.stop()

# Fungsi login
def sign_in(email, password):
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if res.user:
            # Simpan user dan session
            st.session_state['user'] = res.user
            st.session_state['session'] = res.session
            st.session_state['authenticated'] = True
            st.success("Login berhasil! Silakan pilih menu di sidebar.")
            st.rerun()
        else:
            st.error("Login gagal: User tidak ditemukan.")
    except Exception as e:
        st.error(f"❌ Login gagal: {e}")

# Tampilan form login
st.title("🔐 Login SIDAMA")
st.info("Silakan login menggunakan akun yang terdaftar.")

with st.form("login_form"):
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    submit = st.form_submit_button("Login")

    if submit:
        if email and password:
            sign_in(email, password)
        else:
            st.warning("Harap isi email dan password.")
