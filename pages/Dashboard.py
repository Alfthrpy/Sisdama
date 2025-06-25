import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime
from supabase import create_client
import warnings
warnings.filterwarnings('ignore')
import plotly.io as pio
from io import BytesIO
from PyPDF2 import PdfMerger
from utils.get_connection import init_supabase_connection
from utils.auth import require_login


require_login()

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        padding: 1rem;
        background: linear-gradient(90deg, #e3f2fd, #f8f9fa);
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
    }
    
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #1f77b4;
    }
    
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        padding: 10px;
        margin: 10px 0;
    }
    
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 10px;
        margin: 10px 0;
    }
    
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 5px;
        padding: 10px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# ========================
# DATA LOADING & CACHING
# ========================

@st.cache_data(ttl=300)  
def load_data():
    try:
        supabase = init_supabase_connection()
        if not supabase:
            return None, None, None, None
            
        df_mhs = pd.DataFrame(supabase.table("mahasiswas").select("*").execute().data)
        df_status = pd.DataFrame(supabase.table("status_akademik_semesters").select("*").execute().data)
        df_bea = pd.DataFrame(supabase.table("penerimaan_beasiswas").select("*").execute().data)
        df_semester = pd.DataFrame(supabase.table("semesters").select("*").execute().data)
        
        # Data preprocessing
        if not df_status.empty and 'ipk' in df_status.columns:
            df_status['ipk'] = pd.to_numeric(df_status['ipk'], errors='coerce')
        if not df_mhs.empty and 'tahun_masuk' in df_mhs.columns:
            df_mhs['tahun_masuk'] = pd.to_numeric(df_mhs['tahun_masuk'], errors='coerce')
            
        return df_mhs, df_status, df_bea, df_semester
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None, None, None, None

# ========================
# UTILITY FUNCTIONS
# ========================
def safe_divide(a, b):
    return a / b if b != 0 else 0

def get_grade_category(ipk):
    if pd.isna(ipk):
        return "Tidak Ada Data"
    elif ipk >= 3.5:
        return "Cumlaude (≥3.5)"
    elif ipk >= 3.0:
        return "Sangat Baik (3.0-3.49)"
    elif ipk >= 2.5:
        return "Baik (2.5-2.99)"
    elif ipk >= 2.0:
        return "Cukup (2.0-2.49)"
    else:
        return "Kurang (<2.0)"

def create_gauge_chart(value, title, max_val=4.0, threshold_colors=None):
    if threshold_colors is None:
        threshold_colors = [
            {"range": [0, 2.0], "color": "#ff4444"},
            {"range": [2.0, 2.5], "color": "#ff8800"},
            {"range": [2.5, 3.0], "color": "#ffcc00"},
            {"range": [3.0, 3.5], "color": "#88cc00"},
            {"range": [3.5, 4.0], "color": "#00cc44"}
        ]
    
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = value,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': title},
        delta = {'reference': 3.0},
        gauge = {
            'axis': {'range': [None, max_val]},
            'bar': {'color': "#1f77b4"},
            'steps': [
                {'range': [0, 2.0], 'color': "#ffeeee"},
                {'range': [2.0, 2.5], 'color': "#fff4e6"},
                {'range': [2.5, 3.0], 'color': "#fffce6"},
                {'range': [3.0, 3.5], 'color': "#f0fff0"},
                {'range': [3.5, 4.0], 'color': "#e6ffe6"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 2.5
            }
        }
    ))
    fig.update_layout(height=300)
    return fig

def tampilkan_rekomendasi(
    kategori: str,
    prioritas: str,
    deskripsi: str,
    df_mahasiswa: pd.DataFrame,
    file_name: str,
    warna: str = "#dc3545"
):
    """
    Menampilkan rekomendasi tindakan dengan tabel detail mahasiswa dan tombol unduh.
    """
    if df_mahasiswa.empty:
        return

    st.markdown(f"""
    <div style="background-color: #f8f9fa; border-left: 6px solid {warna}; padding: 1rem; border-radius: 6px; margin-bottom: 1rem;">
        <strong style="font-size: 1.1rem;">{kategori}</strong><br>
        <b>Prioritas:</b> {prioritas}<br>
        <b>Detail:</b> {deskripsi}
    </div>
    """, unsafe_allow_html=True)

    with st.expander("📋 Lihat Daftar Mahasiswa"):
        display_cols = ['nama_lengkap', 'nim', 'jurusan', 'tahun_masuk', 'ipk', 'status_mahasiswa']
        show = [col for col in display_cols if col in df_mahasiswa.columns]

        st.dataframe(df_mahasiswa[show].sort_values(by='ipk'), use_container_width=True, hide_index=True)

        csv = df_mahasiswa[show].to_csv(index=False)
        st.download_button(
            label="📥 Unduh Daftar Mahasiswa",
            data=csv,
            file_name=file_name,
            mime="text/csv"
        )
    return

def save_charts_to_pdf(figures):
    buffer = BytesIO()
    merger = PdfMerger()
    
    for i, fig in enumerate(figures):
        temp_buffer = BytesIO()
        pio.write_image(fig, temp_buffer, format="pdf", engine="kaleido")
        temp_buffer.seek(0)
        merger.append(temp_buffer)

    merger.write(buffer)
    buffer.seek(0)
    return buffer


# ========================
# MAIN APPLICATION
# ========================
def main():
    # Load data with progress bar
    with st.spinner('Memuat data dari database...'):
        df_mhs, df_status, df_bea, df_semester = load_data()
    
    if df_mhs is None:
        st.error("Gagal memuat data. Periksa koneksi database.")
        return
    
    # Check if data is empty
    if df_mhs.empty:
        st.warning("Tidak ada data mahasiswa yang tersedia.")
        return
    
    # Data preparation
    if not df_status.empty:
        latest_status = df_status.sort_values("tanggal_evaluasi").drop_duplicates("mahasiswa_id", keep="last")
        df_joined = latest_status.merge(df_mhs, on="mahasiswa_id", how="left")
        if 'ipk' in df_joined.columns:
            df_joined["ipk"] = pd.to_numeric(df_joined["ipk"], errors='coerce')
    else:
        df_joined = df_mhs.copy()
        df_joined['ipk'] = np.nan
    
    # Add grade categories
    df_joined['kategori_ipk'] = df_joined['ipk'].apply(get_grade_category)
    
    # ========================
    # SIDEBAR FILTERS
    # ========================
    st.sidebar.title("🔍 Filter Data")
    
    # Reset filters button
    if st.sidebar.button("🔄 Reset Semua Filter"):
        st.rerun()
    
    # Program Studi filter
    available_prodi = df_mhs["jurusan"].dropna().unique() if "jurusan" in df_mhs.columns else []
    selected_prodi = st.sidebar.multiselect(
        "📚 Program Studi", 
        options=sorted(available_prodi),
        help="Pilih satu atau beberapa program studi"
    )
    
    # Tahun Masuk filter
    available_tahun = df_mhs["tahun_masuk"].dropna().unique() if "tahun_masuk" in df_mhs.columns else []
    if len(available_tahun) > 0:
        selected_tahun = st.sidebar.multiselect(
            "📅 Tahun Masuk", 
            options=sorted(available_tahun),
            help="Filter berdasarkan tahun masuk"
        )
    else:
        selected_tahun = []
    
    # Status Mahasiswa filter
    available_status = df_mhs["status_mahasiswa"].dropna().unique() if "status_mahasiswa" in df_mhs.columns else []
    selected_status = st.sidebar.multiselect(
        "👤 Status Mahasiswa", 
        options=sorted(available_status),
        help="Filter berdasarkan status aktif/tidak aktif"
    )
    
    # IPK Range filter
    valid_ipk = df_joined['ipk'].dropna()
    if not valid_ipk.empty:
        min_ipk, max_ipk = float(valid_ipk.min()), float(valid_ipk.max())
        ipk_range = st.sidebar.slider(
            "📊 Rentang IPK", 
            min_value=0.0, 
            max_value=4.0, 
            value=(max(0.0, min_ipk), min(4.0, max_ipk)), 
            step=0.01,
            help="Geser untuk mengatur rentang IPK"
        )
    else:
        ipk_range = (0.0, 4.0)
    
    # Apply filters
    filtered = df_joined.copy()
    if selected_prodi:
        filtered = filtered[filtered["jurusan"].isin(selected_prodi)]
    if selected_tahun:
        filtered = filtered[filtered["tahun_masuk"].isin(selected_tahun)]
    if selected_status:
        filtered = filtered[filtered["status_mahasiswa"].isin(selected_status)]
    if not filtered['ipk'].isna().all():
        filtered = filtered[filtered["ipk"].between(*ipk_range) | filtered["ipk"].isna()]
    
    # Show filter summary
    if any([selected_prodi, selected_tahun, selected_status]) or ipk_range != (0.0, 4.0):
        st.sidebar.markdown("### 📋 Filter Aktif:")
        if selected_prodi:
            st.sidebar.write(f"• Prodi: {', '.join(selected_prodi)}")
        if selected_tahun:
            st.sidebar.write(f"• Tahun: {', '.join(map(str, selected_tahun))}")
        if selected_status:
            st.sidebar.write(f"• Status: {', '.join(selected_status)}")
        if ipk_range != (0.0, 4.0):
            st.sidebar.write(f"• IPK: {ipk_range[0]:.2f} - {ipk_range[1]:.2f}")
        st.sidebar.write(f"**Total: {len(filtered)} mahasiswa**")
    
    # ========================
    # OVERVIEW METRICS
    # ========================
    st.subheader("📊 Overview Metrics")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        total_mhs = len(filtered)
        total_all = len(df_mhs)
        st.metric(
            "Total Mahasiswa", 
            total_mhs
        )
    
    with col2:
        valid_ipk = filtered['ipk'].dropna()
        avg_ipk = valid_ipk.mean() if not valid_ipk.empty else 0
        st.metric("Rata-rata IPK", f"{avg_ipk:.2f}")
    
    with col3:
        if not df_bea.empty:
            penerima_beasiswa = filtered["mahasiswa_id"].isin(df_bea["mahasiswa_id"]).sum()
            persentase_beasiswa = safe_divide(penerima_beasiswa, total_mhs) * 100
            st.metric(
                "Penerima Beasiswa", 
                penerima_beasiswa,
            )
        else:
            st.metric("Penerima Beasiswa", "N/A")
    
    with col4:
        aktif_count = filtered[filtered["status_mahasiswa"] == "Aktif"].shape[0] if "status_mahasiswa" in filtered.columns else 0
        aktif_persen = safe_divide(aktif_count, total_mhs) * 100
        st.metric(
            "Mahasiswa Aktif", 
            aktif_count,
        )
    
    with col5:
        ipk_tinggi = filtered[filtered['ipk'] >= 3.5].shape[0] if not filtered['ipk'].isna().all() else 0
        ipk_tinggi_persen = safe_divide(ipk_tinggi, total_mhs) * 100
        st.metric(
            "IPK ≥ 3.5", 
            ipk_tinggi
        )

    
    # ========================
    # ENHANCED VISUALIZATIONS
    # ========================
    st.subheader("📈 Analisis Visual")
    
    # Create tabs for different analysis
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Distribusi", "📈 Trend", "🏆 Ranking", "🔍 Analisis Lanjutan", "📋 Data Detail"
    ])
    
    with tab1:
        viz_col1, viz_col2 = st.columns(2)
        
        with viz_col1:
            # Distribusi Program Studi
            if "jurusan" in filtered.columns and not filtered.empty:
                jurusan_counts = filtered["jurusan"].value_counts().reset_index()
                jurusan_counts.columns = ["jurusan", "count"]
                
                fig_bar = px.bar(
                    jurusan_counts.head(3),
                    x="count", 
                    y="jurusan",
                    orientation='h',
                    title="📚 3 Program Studi dengan Mahasiswa Terbanyak",
                    labels={"jurusan": "", "count": "Jumlah Mahasiswa"},
                    color_discrete_sequence=["#4CAF50", "#8BC34A", "#CDDC39"]
                )
                fig_bar.update_layout(
                    height=400,
                    xaxis_title=None,
                    yaxis_title=None,
                    showlegend=False,
                    margin=dict(l=20, r=20, t=40, b=20)
                )
                st.plotly_chart(fig_bar, use_container_width=True)

        with viz_col2:
            # Distribusi IPK
            valid_ipk_data = filtered['ipk'].dropna()
            if not valid_ipk_data.empty:
                avg_ipk = valid_ipk_data.mean()
                fig_hist = px.histogram(
                    valid_ipk_data,
                    nbins=20,
                    title="📊 Sebaran IPK Mahasiswa",
                    labels={"value": "IPK", "count": "Jumlah Mahasiswa"},
                    color_discrete_sequence=["#2196F3"]
                )
                fig_hist.add_vline(
                    x=avg_ipk, 
                    line_dash="dash", 
                    line_color="red",
                    annotation_text=f"Rata-rata: {avg_ipk:.2f}",
                    annotation_position="top right"
                )
                fig_hist.update_layout(
                    height=400,
                    xaxis_title=None,
                    yaxis_title=None,
                    margin=dict(l=20, r=20, t=40, b=20)
                )
                st.plotly_chart(fig_hist, use_container_width=True)

        # Distribusi Kategori IPK
        if not filtered['kategori_ipk'].isna().all():
            kategori_counts = filtered['kategori_ipk'].value_counts()
            
            fig_pie = px.pie(
                values=kategori_counts.values,
                names=kategori_counts.index,
                title="🎓 Persentase Mahasiswa Berdasarkan Kategori IPK",
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_pie.update_traces(textinfo='percent+label', pull=[0.05]*len(kategori_counts))
            fig_pie.update_layout(
                height=400,
                showlegend=False,
                margin=dict(l=20, r=20, t=40, b=20)
            )
            st.plotly_chart(fig_pie, use_container_width=True)

    
    with tab2:
        st.markdown("### 📈 Trend Mahasiswa dan Performa Akademik")

        trend_col1, trend_col2 = st.columns(2)

        with trend_col1:
            # Trend penerimaan mahasiswa per tahun
            if "tahun_masuk" in df_mhs.columns:
                trend_masuk = df_mhs.groupby("tahun_masuk")["mahasiswa_id"].count().reset_index()
                trend_masuk.columns = ["tahun_masuk", "jumlah"]
                trend_masuk = trend_masuk.sort_values("tahun_masuk")

                fig_masuk = px.bar(
                    trend_masuk,
                    x="tahun_masuk",
                    y="jumlah",
                    title="🗓️ Jumlah Mahasiswa Masuk per Tahun",
                    labels={"tahun_masuk": "Tahun Masuk", "jumlah": "Jumlah Mahasiswa"},
                    text="jumlah",
                    color_discrete_sequence=["#1f77b4"]
                )
                fig_masuk.update_traces(textposition='outside')
                fig_masuk.update_layout(height=450)
                st.plotly_chart(fig_masuk, use_container_width=True)
            else:
                st.info("Data tahun masuk tidak tersedia.")

        with trend_col2:
            # Trend IPK rata-rata per semester
            if not df_status.empty and not df_semester.empty:
                ipk_per_sem = df_status.groupby("semester_id")["ipk"].mean().reset_index()
                ipk_per_sem = ipk_per_sem.merge(df_semester[['semester_id', 'nama_semester']], on="semester_id", how="left")
                ipk_per_sem = ipk_per_sem.dropna(subset=['ipk', 'nama_semester'])
                ipk_per_sem = ipk_per_sem.sort_values("nama_semester") 

                fig_ipk = px.line(
                    ipk_per_sem,
                    x="nama_semester",
                    y="ipk",
                    title="📊 Rata-rata IPK per Semester",
                    markers=True,
                    labels={"nama_semester": "Semester", "ipk": "Rata-rata IPK"},
                    text=ipk_per_sem["ipk"].round(2)
                )
                fig_ipk.update_traces(textposition="top center", line=dict(color="#2ca02c", width=3))
                fig_ipk.add_hline(
                    y=ipk_per_sem['ipk'].mean(),
                    line_dash="dot",
                    annotation_text=f"Rata-rata Keseluruhan: {ipk_per_sem['ipk'].mean():.2f}",
                    annotation_position="top left"
                )
                fig_ipk.update_layout(height=450)
                st.plotly_chart(fig_ipk, use_container_width=True)
            else:
                st.info("Data IPK per semester tidak tersedia.")


    
    with tab3:
        st.markdown("### 🏆 Ranking Program Studi")

        rank_col1, rank_col2 = st.columns(2)

        with rank_col1:
            # Top 3 program studi dengan rata-rata IPK tertinggi
            if "jurusan" in filtered.columns and 'ipk' in filtered.columns:
                prodi_stats = filtered.groupby("jurusan").agg({
                    'ipk': ['mean', 'count']
                }).round(3)
                prodi_stats.columns = ['avg_ipk', 'ipk_count']
                prodi_stats = prodi_stats.reset_index()
                prodi_stats = prodi_stats[prodi_stats['ipk_count'] >= 5] 
                prodi_stats = prodi_stats.sort_values('avg_ipk', ascending=False).head(3)

                if not prodi_stats.empty:
                    fig_ipk_rank = px.bar(
                        prodi_stats,
                        x='jurusan',
                        y='avg_ipk',
                        title='🏅 Top 3 Program Studi dengan Rata-rata IPK Tertinggi',
                        labels={'jurusan': 'Program Studi', 'avg_ipk': 'Rata-rata IPK'},
                        text='avg_ipk',
                        color_discrete_sequence=['#1f77b4']
                    )
                    fig_ipk_rank.update_traces(texttemplate='%{text:.2f}', textposition='outside')
                    fig_ipk_rank.update_layout(
                        xaxis_tickangle=-30,
                        yaxis_range=[0, 4],
                        height=500
                    )
                    st.plotly_chart(fig_ipk_rank, use_container_width=True)
                else:
                    st.info("Belum cukup data untuk menampilkan ranking IPK per prodi.")

        with rank_col2:
            if not df_bea.empty and "jurusan" in filtered.columns:
                df_bea_unique = df_bea.drop_duplicates(subset=["mahasiswa_id"])
                bea_filtered = filtered.copy()
                bea_filtered["penerima_beasiswa"] = bea_filtered["mahasiswa_id"].isin(df_bea_unique["mahasiswa_id"])
                bea_counts = bea_filtered.groupby("jurusan")["penerima_beasiswa"].sum().reset_index()
                bea_counts = bea_counts.sort_values("penerima_beasiswa", ascending=False).head(3)

                if not bea_counts.empty:
                    fig_bea_rank = px.bar(
                        bea_counts,
                        x="jurusan",
                        y="penerima_beasiswa",
                        title="🎖️ Top 3 Program Studi dengan Penerima Beasiswa Terbanyak",
                        labels={"jurusan": "Program Studi", "penerima_beasiswa": "Jumlah Penerima"},
                        text='penerima_beasiswa',
                        color_discrete_sequence=['#2ca02c']
                    )
                    fig_bea_rank.update_traces(texttemplate='%{text}', textposition='outside')
                    fig_bea_rank.update_layout(
                        xaxis_tickangle=-30,
                        height=500
                    )
                    st.plotly_chart(fig_bea_rank, use_container_width=True)
                else:
                    st.info("Tidak ada data penerima beasiswa yang bisa ditampilkan.")

    
    with tab4:
        st.markdown("### 🔍 Analisis Lanjutan Mahasiswa")

        analysis_col1, analysis_col2 = st.columns(2)

        # === A. Analisis Korelasi IPK dan Beasiswa (Bar Chart) ===
        with analysis_col1:
            if not df_bea.empty and 'ipk' in filtered.columns:
                filtered["dapat_beasiswa"] = filtered["mahasiswa_id"].isin(df_bea["mahasiswa_id"]).astype(int)
                avg_by_bea = filtered.groupby("dapat_beasiswa")["ipk"].mean().reset_index()
                avg_by_bea["Status"] = avg_by_bea["dapat_beasiswa"].map({1: "Ya", 0: "Tidak"})

                fig_corr_bar = px.bar(
                    avg_by_bea,
                    x="Status",
                    y="ipk",
                    text="ipk",
                    title="🎓 Rata-rata IPK Berdasarkan Status Beasiswa",
                    labels={"Status": "Penerima Beasiswa", "ipk": "Rata-rata IPK"},
                    color_discrete_sequence=["#1f77b4"]
                )
                fig_corr_bar.update_traces(texttemplate='%{text:.2f}', textposition='outside')
                fig_corr_bar.update_layout(height=400)
                st.plotly_chart(fig_corr_bar, use_container_width=True)

                # Korelasi numerik (dengan interpretasi)
                corr_val = filtered["ipk"].corr(filtered["dapat_beasiswa"])
                st.caption(f"**Koefisien Korelasi**: {corr_val:.3f}")
                if abs(corr_val) >= 0.5:
                    st.success("✅ Korelasi kuat: IPK dan beasiswa memiliki hubungan yang jelas.")
                elif abs(corr_val) >= 0.3:
                    st.warning("⚠️ Korelasi sedang: Ada kecenderungan hubungan antara IPK dan beasiswa.")
                else:
                    st.info("ℹ️ Korelasi lemah: Tidak ada hubungan signifikan antara IPK dan beasiswa.")

        # === B. Statistik Ringkasan IPK (Bar Chart) ===
        with analysis_col2:
            valid_ipk = filtered['ipk'].dropna()
            if not valid_ipk.empty:
                stat_summary = {
                    "Mean": valid_ipk.mean(),
                    "Median": valid_ipk.median(),
                    "Min": valid_ipk.min(),
                    "Max": valid_ipk.max(),
                    "Q1 (25%)": valid_ipk.quantile(0.25),
                    "Q3 (75%)": valid_ipk.quantile(0.75)
                }

                df_stat = pd.DataFrame(stat_summary.items(), columns=["Statistik", "Nilai"])
                fig_stat_bar = px.bar(
                    df_stat,
                    x="Statistik",
                    y="Nilai",
                    text="Nilai",
                    title="📊 Ringkasan Statistik IPK Mahasiswa",
                    color_discrete_sequence=["#2ca02c"]
                )
                fig_stat_bar.update_traces(texttemplate='%{text:.2f}', textposition='outside')
                fig_stat_bar.update_layout(height=400)
                st.plotly_chart(fig_stat_bar, use_container_width=True)

                st.caption("Statistik ringkasan memberikan gambaran sebaran performa akademik.")
            else:
                st.info("Tidak ada data IPK valid untuk dianalisis.")

    
    with tab5:
        # Data Detail Tab
        st.markdown("### 📋 Detail Data Mahasiswa")
        
        # Search functionality
        search_term = st.text_input("🔍 Cari mahasiswa (nama/NIM):", placeholder="Masukkan nama atau NIM...")
        
        # Prepare display data
        display_df = filtered.copy()
        
        if search_term:
            if 'nama_lengkap' in display_df.columns:
                mask = display_df['nama_lengkap'].str.contains(search_term, case=False, na=False)
                if 'nim' in display_df.columns:
                    mask |= display_df['nim'].str.contains(search_term, case=False, na=False)
                display_df = display_df[mask]
        
        # Add scholarship status
        if not df_bea.empty:
            display_df['status_beasiswa'] = display_df['mahasiswa_id'].isin(df_bea['mahasiswa_id']).map({True: '✅ Ya', False: '❌ Tidak'})
        
        # Select columns to display
        display_columns = []
        available_columns = display_df.columns.tolist()
        
        important_cols = ['nama_lengkap', 'nim', 'jurusan', 'tahun_masuk', 'status_mahasiswa', 'ipk', 'kategori_ipk', 'status_beasiswa']
        for col in important_cols:
            if col in available_columns:
                display_columns.append(col)
        
        if display_columns:
            st.dataframe(
                display_df[display_columns].head(100),
                use_container_width=True,
                hide_index=True
            )
            
            st.info(f"Menampilkan {min(len(display_df), 100)} dari {len(display_df)} mahasiswa")
        
        # Download options
        col_down1, col_down2 = st.columns(2)
        with col_down1:
            if st.button("📥 Download Data Terfilter (CSV)"):
                csv = display_df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"sidama_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        
        with col_down2:
            if st.button("📊 Download Laporan Excel"):
                # This would require additional implementation for Excel export
                st.info("Fitur ekspor Excel akan segera tersedia!")
    
    # ========================
    # INSIGHT OTOMATIS & REKOMENDASI TINDAKAN
    # ========================
    st.subheader("💡 Rekomendasi Tindakan")

    # Persiapan data
    valid_ipk = filtered['ipk'].dropna()
    rendah_ipk = filtered[filtered['ipk'] < 2.5] if 'ipk' in filtered.columns else pd.DataFrame()
    nonaktif = filtered[filtered['status_mahasiswa'] != "Aktif"] if 'status_mahasiswa' in filtered.columns else pd.DataFrame()
    belum_dapat_bea = pd.DataFrame()
    if not df_bea.empty and 'mahasiswa_id' in filtered.columns:
        ipk_3up = filtered[filtered["ipk"] >= 3.5] if 'ipk' in filtered.columns else pd.DataFrame()
        belum_dapat_bea = ipk_3up[~ipk_3up["mahasiswa_id"].isin(df_bea["mahasiswa_id"])]

    # Rekomendasi 1: Akademik
    tampilkan_rekomendasi(
        kategori="📕 Akademik: Bimbingan akademik intensif",
        prioritas="Tinggi",
        deskripsi=f"Dengan {len(rendah_ipk)} mahasiswa ber-IPK rendah, perlu program mentoring dan remedial.",
        df_mahasiswa=rendah_ipk,
        file_name="mahasiswa_ipk_rendah.csv",
        warna="#dc3545"
    )

    # Rekomendasi 2: Beasiswa
    tampilkan_rekomendasi(
        kategori="🎓 Beasiswa: Sosialisasi program beasiswa",
        prioritas="Sedang",
        deskripsi=f"Ada {len(belum_dapat_bea)} mahasiswa ber-IPK ≥ 3.0 yang belum menerima beasiswa.",
        df_mahasiswa=belum_dapat_bea,
        file_name="mahasiswa_belum_beasiswa.csv",
        warna="#ffc107"
    )

    # Rekomendasi 3: Retensi
    tampilkan_rekomendasi(
        kategori="🔁 Retensi: Program reengagement mahasiswa non-aktif",
        prioritas="Tinggi",
        deskripsi=f"Investigasi dan pendekatan kepada {len(nonaktif)} mahasiswa non-aktif diperlukan.",
        df_mahasiswa=nonaktif,
        file_name="mahasiswa_nonaktif.csv",
        warna="#dc3545"
    )

    # Rekomendasi 4: Early Warning Mahasiswa Potensi Terlambat
    # st.markdown("### ⏰ Mahasiswa Berpotensi Terlambat Lulus")

    # now = datetime.now()
    # threshold_year = now.year - 4
    # potensi_terlambat = filtered[
    #     (filtered['ipk'] < 2.5) & (filtered['tahun_masuk'] <= threshold_year)
    # ] if 'ipk' in filtered.columns and 'tahun_masuk' in filtered.columns else pd.DataFrame()

    # tampilkan_rekomendasi(
    #     kategori="⏰ Potensi Terlambat Lulus",
    #     prioritas="Tinggi",
    #     deskripsi=f"Terdapat {len(potensi_terlambat)} mahasiswa dengan IPK < 2.5 dan tahun masuk ≤ {threshold_year}.",
    #     df_mahasiswa=potensi_terlambat,
    #     file_name="mahasiswa_terlambat_lulus.csv",
    #     warna="#6f42c1"
    # )

    
    # ========================
    # EXPORT & REPORTING
    # ========================
    st.subheader("📤 Export & Pelaporan")

    export_col1, export_col2 = st.columns([1, 1])

    # === Kolom Ringkasan Eksekutif ===
    with export_col1:
        st.markdown("#### 📊 Ringkasan Eksekutif")
        if st.button("📝 Buat Ringkasan"):
            summary_data = {
                "Metrik": [
                    "Total Mahasiswa",
                    "Rata-rata IPK",
                    "Mahasiswa Aktif",
                    "Penerima Beasiswa",
                    "IPK ≥ 3.5",
                    "IPK < 2.5"
                ],
                "Nilai": [
                    len(filtered),
                    f"{valid_ipk.mean():.2f}" if not valid_ipk.empty else "Tidak tersedia",
                    f"{aktif_count} ({aktif_persen:.1f}%)" if 'aktif_count' in locals() else "Tidak tersedia",
                    f"{penerima_beasiswa} ({persentase_beasiswa:.1f}%)" if 'penerima_beasiswa' in locals() else "Tidak tersedia",
                    f"{ipk_tinggi} ({ipk_tinggi_persen:.1f}%)" if 'ipk_tinggi' in locals() else "Tidak tersedia",
                    f"{(valid_ipk < 2.5).sum()} ({((valid_ipk < 2.5).sum()/len(valid_ipk)*100):.1f}%)" if not valid_ipk.empty else "Tidak tersedia"
                ]
            }

            summary_df = pd.DataFrame(summary_data)
            st.success("✅ Ringkasan Eksekutif berhasil dibuat")
            st.dataframe(summary_df, use_container_width=True, hide_index=True)

            csv_summary = summary_df.to_csv(index=False)
            st.download_button(
                label="⬇️ Unduh Ringkasan (CSV)",
                data=csv_summary,
                file_name=f"executive_summary_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

    # === Kolom Ekspor Grafik ke PDF ===
    with export_col2:
        st.markdown("#### 📈 Ekspor Grafik")
        if st.button("🖨️ Simpan Grafik ke PDF"):
            st.info("⏳ Sedang menyiapkan file PDF...")

            figures = []
            if 'fig_bar' in locals(): figures.append(fig_bar)
            if 'fig_hist' in locals(): figures.append(fig_hist)
            if 'fig_pie' in locals(): figures.append(fig_pie)

            if figures:
                pdf_buffer = save_charts_to_pdf(figures)
                if pdf_buffer:
                    st.success("✅ Grafik berhasil diekspor ke PDF!")
                    st.download_button(
                        label="⬇️ Unduh PDF Grafik",
                        data=pdf_buffer,
                        file_name=f"grafik_mahasiswa_{datetime.now().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf"
                    )
            else:
                st.warning("⚠️ Tidak ada grafik yang tersedia untuk diekspor.")

    # ========================
    # FOOTER
    # ========================
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666; padding: 20px;'>
            <p>🎓 <strong>SIDAMA</strong> - Sistem Data Mahasiswa</p>
            <p>Dashboard ini diperbarui secara real-time berdasarkan data terbaru dari database</p>
            <p><small>Terakhir diperbarui: {}</small></p>
        </div>
        """.format(datetime.now().strftime("%d %B %Y, %H:%M:%S")),
        unsafe_allow_html=True
    )

# ========================
# RUN APPLICATION
# ========================
if __name__ == "__main__":
    main()
