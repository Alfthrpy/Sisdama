# app.py
import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px
from utils.auth import require_login
from utils.get_connection import init_supabase_connection
# --- KONFIGURASI SUPABASE ---
supabase = init_supabase_connection()

require_login()
# --- TITLE ---
st.set_page_config(page_title="Analisis Pola Studi", layout="wide")
st.title("📊 Analisis Pola Studi Mahasiswa")

# --- LOAD DATA ---
@st.cache_data
def load_data():
    response = supabase.rpc("get_ringkasan_studi").execute()
    return pd.DataFrame(response.data)

df = load_data()

# --- DYNAMIC YEAR FILTER ---
@st.cache_data
def get_unique_years():
    return sorted(df["tahun_masuk"].dropna().unique().tolist())

year = get_unique_years()

# --- FILTERS ---
with st.sidebar:
    st.header("Filter Mahasiswa")
    search = st.text_input("🔍 Nama atau NIM")
    tahun_masuk = st.selectbox("📅 Tahun Masuk", options=["Semua"] + year, index=0)
    show_only_delay = st.toggle("🚨 Hanya potensi keterlambatan", value=False)
    show_risiko = st.toggle("⚠️ Hanya peringatan dini (IPK rendah)", value=False)

# --- FILTERING ---
if search:
    df = df[df["nama_lengkap"].str.contains(search, case=False) | df["nim"].str.contains(search, case=False)]

if tahun_masuk != "Semua":
    df = df[df["tahun_masuk"] == tahun_masuk]

# --- GROUPING ---
sks_lulus = df.groupby("mahasiswa_id")["sks_lulus_semester"].sum().reset_index(name="total_sks")
semester_aktif = df.groupby("mahasiswa_id")["semester_id"].nunique().reset_index(name="semester_aktif")
ipk_terakhir = df.groupby("mahasiswa_id")["ipk"].last().reset_index(name="ipk_terakhir")
ips_terakhir = df.groupby("mahasiswa_id")["ips"].last().reset_index(name="ips_terakhir")

df_summary = df[["mahasiswa_id", "nama_lengkap", "nim", "program_studi", "tahun_masuk"]].drop_duplicates()
df_summary = df_summary.merge(sks_lulus, on="mahasiswa_id")\
                         .merge(semester_aktif, on="mahasiswa_id")\
                         .merge(ipk_terakhir, on="mahasiswa_id")\
                         .merge(ips_terakhir, on="mahasiswa_id")

# --- STATUS STUDI ---
def status_studi(row):
    if row["semester_aktif"] > 8 and row["total_sks"] < 144:
        return "Potensi Telat"
    elif row["total_sks"] / row["semester_aktif"] < 12:
        return "Underload"
    return "Aman"

df_summary["Status Studi"] = df_summary.apply(status_studi, axis=1)

# --- PERINGATAN DINI BERDASARKAN IPK ---
def peringatan_dini(ipk):
    if ipk < 2.5:
        return "⚠️ Risiko Tinggi Drop-Out"
    elif ipk < 3.0:
        return "⚠️ Butuh Intervensi Akademik"
    return "✅ Aman"

df_summary["Peringatan Dini"] = df_summary["ipk_terakhir"].apply(peringatan_dini)

df_summary["Rekomendasi"] = df_summary.apply(
    lambda row: "Konsultasi Dosen Wali" if row["Status Studi"] == "Potensi Telat" or "⚠️" in row["Peringatan Dini"] else "-",
    axis=1
)

if show_only_delay:
    df_summary = df_summary[df_summary["Status Studi"] == "Potensi Telat"]
if show_risiko:
    df_summary = df_summary[df_summary["Peringatan Dini"].str.contains("⚠️")] 

# --- TABEL UTAMA ---
st.subheader("📋 Daftar Mahasiswa")
st.dataframe(
    df_summary.rename(columns={
        "nama_lengkap": "Nama Mahasiswa",
        "nim": "NIM",
        "program_studi": "Prodi",
        "semester_aktif": "Semester Aktif",
        "total_sks": "Total SKS Lulus",
        "ipk_terakhir": "IPK Terakhir",
        "ips_terakhir": "IPS Terakhir"
    }),
    use_container_width=True,
    hide_index=True
)

# --- GRAFIK PER MAHASISWA ---
st.subheader("📈 Grafik Perkembangan Mahasiswa")

if not df_summary.empty:
    nama_terpilih = st.selectbox("Pilih Mahasiswa", df_summary["nama_lengkap"].unique())

    if nama_terpilih:
        df_selected = df_summary[df_summary["nama_lengkap"] == nama_terpilih]

        if not df_selected.empty:
            selected_id = df_selected["mahasiswa_id"].values[0]
            df_detail = df[df["mahasiswa_id"] == selected_id]

            if not df_detail.empty:
                df_detail = df_detail.sort_values("semester_id")
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("#### 📊 Grafik SKS Lulus")
                    fig_sks = px.bar(df_detail, x="nama_semester", y="sks_lulus_semester", title="SKS Lulus Tiap Semester")
                    st.plotly_chart(fig_sks, use_container_width=True)

                with col2:
                    st.markdown("#### 📈 Grafik IPK dan IPS")
                    fig_ipk = px.line(df_detail, x="nama_semester", y=["ipk", "ips"], markers=True, title="Perkembangan IPK & IPS")
                    st.plotly_chart(fig_ipk, use_container_width=True)
            else:
                st.info("📭 Tidak ada data untuk mahasiswa ini.")
        else:
            st.warning("❗ Mahasiswa tidak ditemukan.")
else:
    st.warning("⚠️ Tidak ada data mahasiswa yang dapat ditampilkan.")

# --- EKSPOR ---
csv = df_summary.to_csv(index=False).encode("utf-8")
st.download_button("📥 Ekspor ke Excel", data=csv, file_name="analisis_pola_studi.csv", mime="text/csv")
