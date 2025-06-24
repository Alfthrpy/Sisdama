import streamlit as st
import pandas as pd
from utils.auth import require_login
import plotly.express as px
from supabase import create_client
from io import BytesIO

# ------------------- Konfigurasi Halaman -------------------
require_login()
st.set_page_config(
    page_title="Dashboard Efektivitas Beasiswa",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------- CSS Styling (VERSI BARU) -------------------
st.markdown("""
    <style>
        /* Padding dan judul utama */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }

        h1 {
            font-size: 2.4rem;
            color: #2c3e50;
            margin-bottom: 0.2rem;
        }

        .stMarkdown > div > p {
            font-size: 1.1rem;
            color: #5f6c7b;
            margin-top: -10px;
        }

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
            border-bottom: 1px solid #dfe6ec;
        }

        .stTabs [data-baseweb="tab"] {
            padding: 10px 20px;
            border-radius: 6px 6px 0 0;
            color: #5c6573;
            font-weight: 600;
            background-color: #f8f9fb;
        }

        .stTabs [aria-selected="true"] {
            background-color: #ffffff;
            color: #1f77b4;
            border-bottom: 2px solid #1f77b4;
        }

        /* Metric (KPI) cards */
        [data-testid="stMetric"] {
            background-color: #ffffff;
            border: 1px solid #e0e3e8;
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.03);
        }

        [data-testid="stMetricLabel"] {
            font-size: 0.9rem;
            color: #6c7a89;
        }

        [data-testid="stMetricValue"] {
            font-size: 2.1rem;
            font-weight: bold;
            color: #2d3a4b;
        }

        /* Download Button */
        .stDownloadButton button {
            background-color: #1f77b4;
            color: white;
            font-weight: 600;
            border-radius: 6px;
            padding: 10px 20px;
            margin-top: 10px;
        }

        .stDownloadButton button:hover {
            background-color: #155a8a;
        }

        /* Tabel filter section */
        #tabel-penerima-beasiswa-dan-ekspor {
            background-color: #f7f9fb;
            border-radius: 10px;
            padding: 25px;
            margin-top: 30px;
            border: 1px solid #e0e4e8;
        }

        /* Grafik Container */
        .stPlotlyChart {
            padding: 10px;
            background-color: #fff;
            border-radius: 10px;
            border: 1px solid #e0e4e8;
            box-shadow: 0 1px 3px rgba(0,0,0,0.02);
        }
    </style>
""", unsafe_allow_html=True)

# ------------------- Fungsi Bantuan -------------------
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Data')
    return output.getvalue()

# ------------------- Koneksi Supabase -------------------
@st.cache_resource
def init_supabase_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase_connection()

# ------------------- Load dan Proses Data -------------------
@st.cache_data(ttl=3600)
def load_data():
    mahasiswa_df = pd.DataFrame(supabase.table("mahasiswas").select("*").execute().data)
    beasiswa_df = pd.DataFrame(supabase.table("beasiswas").select("*").execute().data)
    penerimaan_df = pd.DataFrame(supabase.table("penerimaan_beasiswas").select("*").execute().data)
    semester_df = pd.DataFrame(supabase.table("semesters").select("*").execute().data)
    status_df = pd.DataFrame(supabase.table("status_akademik_semesters").select("*").execute().data)
    partisipasi_df = pd.DataFrame(supabase.table("partisipasi_kegiatans").select("*").execute().data)
    kegiatan_df = pd.DataFrame(supabase.table("kegiatan_mahasiswas").select("*").execute().data)

    mahasiswa_df['status_beasiswa'] = mahasiswa_df['mahasiswa_id'].isin(penerimaan_df['mahasiswa_id']).map({True: 'Penerima', False: 'Non-Penerima'})

    df_analisis = status_df.merge(
        mahasiswa_df[['mahasiswa_id', 'nama_lengkap', 'status_mahasiswa', 'status_beasiswa']],
        on='mahasiswa_id', how='left'
    )
    df_analisis = df_analisis.merge(semester_df, on='semester_id', how='left')

    partisipasi_analisis = partisipasi_df.merge(
        mahasiswa_df[['mahasiswa_id', 'status_beasiswa']],
        on='mahasiswa_id', how='left'
    )

    df_beasiswa = penerimaan_df.merge(mahasiswa_df, on='mahasiswa_id', how='left')
    df_beasiswa = df_beasiswa.merge(beasiswa_df, on='beasiswa_id', how='left')
    if 'semester_penerimaan_id' in df_beasiswa.columns and 'semester_id' in semester_df.columns:
        df_beasiswa['semester_penerimaan_id'] = df_beasiswa['semester_penerimaan_id'].astype(str)
        semester_df['semester_id'] = semester_df['semester_id'].astype(str)

        df_beasiswa = df_beasiswa.merge(
            semester_df.rename(columns={'semester_id': 'semester_penerimaan_id'}),
            on='semester_penerimaan_id', how='left'
        )
    else:
        st.warning("Kolom 'semester_penerimaan_id' atau 'semester_id' tidak tersedia.")

    return df_analisis, partisipasi_analisis, df_beasiswa, kegiatan_df

# ------------------- Load Data -------------------
df_analisis, partisipasi_analisis, df_beasiswa, kegiatan_df = load_data()

# ------------------- UI Dashboard -------------------
st.markdown("""
    <h1 style='text-align: center; color: #2c3e50;'>SIDAMA</h1>
    <p style='text-align: center; font-size: 18px; color: #5f6c7b; margin-top: -10px;'>
        Platform Analitik Cerdas untuk Kesuksesan Akademik Mahasiswa
    </p>
""", unsafe_allow_html=True)



tab1, tab2, tab3 = st.tabs(["Kinerja Akademik", "Retensi Studi", "Kegiatan Mahasiswa"])

with tab1:
    st.subheader("Perbandingan IPK Mahasiswa")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Rata-rata IPK Penerima", f"{df_analisis[df_analisis['status_beasiswa']=='Penerima']['ipk'].mean():.2f}")
    with col2:
        st.metric("Rata-rata IPK Non-Penerima", f"{df_analisis[df_analisis['status_beasiswa']=='Non-Penerima']['ipk'].mean():.2f}")

    fig = px.box(df_analisis, x='status_beasiswa', y='ipk', color='status_beasiswa',
                 title='Distribusi IPK Berdasarkan Status Beasiswa',
                 labels={'status_beasiswa': 'Status Beasiswa', 'ipk': 'IPK'})
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Status Akademik Mahasiswa")
    if 'status_mahasiswa' in df_analisis.columns:
        status_counts = df_analisis.groupby(['status_beasiswa', 'status_mahasiswa']).size().reset_index(name='jumlah')
        fig = px.bar(status_counts, x='status_beasiswa', y='jumlah', color='status_mahasiswa',
                     barmode='group', title='Komposisi Status Akademik Mahasiswa')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Kolom 'status_mahasiswa' tidak tersedia.")

with tab3:
    st.subheader("Partisipasi Kegiatan Mahasiswa")
    kegiatan_per_mhs = partisipasi_analisis.groupby(['mahasiswa_id', 'status_beasiswa']).size().reset_index(name='jumlah_kegiatan')
    avg_kegiatan = kegiatan_per_mhs.groupby('status_beasiswa')['jumlah_kegiatan'].mean().reset_index()

    fig = px.bar(avg_kegiatan, x='status_beasiswa', y='jumlah_kegiatan', color='status_beasiswa',
                 title='Rata-rata Kegiatan yang Diikuti Mahasiswa',
                 labels={'jumlah_kegiatan': 'Jumlah Kegiatan'})
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Top Kegiatan Penerima Beasiswa")
    top_kegiatan = partisipasi_analisis[partisipasi_analisis['status_beasiswa']=='Penerima'].merge(
        kegiatan_df, on='kegiatan_id', how='left')
    populer = top_kegiatan['nama_kegiatan'].value_counts().head(10).reset_index()
    populer.columns = ['Nama Kegiatan', 'Jumlah Partisipasi']
    fig2 = px.bar(populer, x='Jumlah Partisipasi', y='Nama Kegiatan', orientation='h',
                   title='10 Kegiatan Terpopuler di Kalangan Penerima Beasiswa')
    st.plotly_chart(fig2, use_container_width=True)

# ------------------- Tabel Data & Ekspor -------------------
st.markdown("---")
st.subheader("Tabel Penerima Beasiswa dan Ekspor", anchor="tabel-penerima-beasiswa-dan-ekspor")

# Mengatur filter dalam kolom agar lebih rapi
filter_cols = st.columns(2)
with filter_cols[0]:
    if 'nama_beasiswa' in df_beasiswa.columns:
        beasiswa_filter = st.multiselect("Filter Nama Beasiswa", sorted(df_beasiswa['nama_beasiswa'].dropna().unique()), default=None)
    else:
        beasiswa_filter = []
with filter_cols[1]:
    if 'nama_semester' in df_beasiswa.columns:
        semester_filter = st.multiselect("Filter Semester", sorted(df_beasiswa['nama_semester'].dropna().unique()), default=None)
    else:
        semester_filter = []

# Logika filter data
filtered_df = df_beasiswa.copy()
if beasiswa_filter:
    filtered_df = filtered_df[filtered_df['nama_beasiswa'].isin(beasiswa_filter)]
if semester_filter:
    filtered_df = filtered_df[filtered_df['nama_semester'].isin(semester_filter)]

if not filtered_df.empty and beasiswa_filter: # Tampilkan hanya jika ada filter aktif
    cols_to_display = ['nama_lengkap', 'email', 'nama_beasiswa', 'nama_semester', 'tanggal_pemberian', 'jumlah_diterima']
    # Memastikan kolom ada sebelum ditampilkan
    tampil_df = filtered_df[[col for col in cols_to_display if col in filtered_df.columns]]
    st.dataframe(tampil_df, use_container_width=True, hide_index=True)

    excel_data = to_excel(tampil_df)
    st.download_button("📥 Unduh ke Excel", data=excel_data, file_name="penerima_beasiswa.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
else:
    st.info("Silakan pilih filter untuk menampilkan dan mengunduh data.")

# --- Footer ---
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("""
<div style="text-align: center; padding: 2rem 0; color: #7f8c8d; border-top: 1px solid #ecf0f1; margin-top: 2rem;">
    <p>© 2025 SIDAMA - Sistem Data Mahasiswa </p>
</div>
""", unsafe_allow_html=True)