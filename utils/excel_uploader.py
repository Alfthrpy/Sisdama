

import streamlit as st
import pandas as pd
from supabase import Client  
from io import BytesIO


@st.cache_data(ttl=3600)
def get_public_tables(_supabase: Client):
    """Mengambil semua nama tabel publik."""
    result = _supabase.rpc("get_public_tables").execute()
    return sorted([row["table_name"] for row in result.data]) if result.data else []

@st.cache_data(ttl=300) 
def get_table_columns_with_details(_supabase: Client, table_name: str):
    """Mengambil detail kolom dari Supabase."""
    result = _supabase.rpc("get_full_column_details", {"t_name": table_name}).execute()
    return result.data or []


@st.cache_data(ttl=300)
def get_enum_values(_supabase: Client, table_name: str, column_name: str):
    """Mengambil semua nilai yang mungkin untuk sebuah kolom ENUM."""
    result = _supabase.rpc("get_enum_values", {"schema_name": "public", "table_name": table_name, "column_name": column_name}).execute()
    return [row["enum_value"] for row in result.data] if result.data else []

def generate_excel_template(supabase: Client, table_name: str) -> bytes:
    """Membuat file Excel di memori dengan sheet data dan panduan."""

    columns_details = get_table_columns_with_details(supabase, table_name)
    if not columns_details:
        raise ValueError(f"Tidak dapat menemukan detail kolom untuk tabel '{table_name}'.")

    df_data = pd.DataFrame(columns=[col['column_name'] for col in columns_details])
    
    guide_data = []
    for col in columns_details:
        guide_data.append({
            "Nama Kolom": col['column_name'],
            "Wajib Diisi?": "YA" if col['is_nullable'] == 'NO' else "TIDAK",
            "Tipe Data": col['data_type'],
        })
    df_guide = pd.DataFrame(guide_data)

    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_data.to_excel(writer, sheet_name='Data Upload', index=False)
        df_guide.to_excel(writer, sheet_name='Panduan Pengisian', index=False)

        for sheet_name in writer.sheets:
            worksheet = writer.sheets[sheet_name]
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = (max_length + 2)
                worksheet.column_dimensions[column_letter].width = adjusted_width

    return output.getvalue()


def display_excel_uploader(supabase: Client):
    """
    Fungsi utama untuk menampilkan seluruh komponen uploader Excel.
    Menerima koneksi Supabase sebagai argumen.
    """
    st.title("📤 Pengunggah Data Excel Dinamis")
    st.markdown("Alat ini memungkinkan Anda mengunggah data ke tabel mana pun di database.")

    st.header("Langkah 1: Pilih Tabel Tujuan")
    tables = get_public_tables(supabase)
    if not tables:
        st.error("Tidak dapat mengambil daftar tabel dari database.")
        st.stop()

    selected_table = st.selectbox("Pilih tabel yang ingin Anda isi datanya:", options=tables, index=None, placeholder="Pilih sebuah tabel...")

    if selected_table:
        st.header(f"Langkah 2: Download Template untuk Tabel `{selected_table}`")
        excel_bytes = generate_excel_template(supabase, selected_table)
        if excel_bytes:
            st.download_button(
                label="Download Template Excel",
                data=excel_bytes,
                file_name=f"template_{selected_table}.xlsx",
                mime="application/vnd.ms-excel"
            )
        
        st.divider()

        st.header("Langkah 3: Unggah File yang Sudah Diisi")
        uploaded_file = st.file_uploader(
            f"Pilih file Excel (.xlsx) untuk tabel `{selected_table}`",
            type=['xlsx'],
            key=f"uploader_{selected_table}"
        )
        
        if uploaded_file:
            try:
                df = pd.read_excel(uploaded_file, sheet_name="Data Upload")
                columns_details = get_table_columns_with_details(supabase, selected_table)
                required_cols = [col['column_name'] for col in columns_details if not col['is_nullable']]
                missing_cols = [col for col in required_cols if col not in df.columns or df[col].isnull().any()]
                
                if missing_cols:
                    st.error(f"Validasi Gagal! Kolom berikut wajib diisi dan tidak boleh kosong: **{', '.join(missing_cols)}**.")
                else:
                    st.success("Validasi Awal Berhasil. Berikut adalah pratinjau data:")
                    st.dataframe(df.head(), use_container_width=True)
                    
                    if st.button(f"Kirim {len(df)} Baris Data ke Tabel `{selected_table}`"):
                        with st.spinner("Mengirim data..."):
                            data_to_insert = df.to_dict(orient='records')
                            try:
                                supabase.table(selected_table).insert(data_to_insert, returning="minimal").execute()
                                st.success(f"Berhasil! {len(df)} baris data telah diunggah.")
                                st.balloons()
                            except Exception as e:
                                st.error(f"Terjadi kesalahan saat menyimpan: {e}")
            except Exception as e:
                st.error(f"Gagal memproses file. Pastikan sheet 'Data Upload' ada. Detail: {e}")