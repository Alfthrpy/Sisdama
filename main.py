import streamlit as st
import requests
from supabase import create_client, Client
import json

# --- Konfigurasi Supabase ---
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(layout="wide")
st.title("SIDAMA EXTRACTOR")

# --- Fungsi RPC ---
def get_supabase_tables():
    result = supabase.rpc("get_public_tables").execute()
    if result.data:
        return [row["table_name"] for row in result.data]
    return []

def get_table_columns_with_details(table_name):
    """Mengambil kolom beserta status nullable-nya."""
    result = supabase.rpc("get_columns_with_details", {"t_name": table_name}).execute()
    if result.data:
        return result.data
    return []

def get_enum_values(table_name, column_name):
    result = supabase.rpc("get_enum_values", {
        "schema_name": "public", 
        "table_name": table_name, 
        "column_name": column_name
    }).execute()
    if result.data:
        return [row["enum_value"] for row in result.data]
    return []

def is_enum_column(table_name, column_name):
    try:
        result = supabase.rpc("check_column_is_enum", {
            "schema_name": "public",
            "table_name": table_name,
            "column_name": column_name
        }).execute()
        if result.data and len(result.data) > 0:
            return result.data[0].get('is_enum', False)
        return False
    except:
        return False

def get_unique_api_values(field_name, sample_data):
    values = set()
    for item in sample_data:
        if field_name in item and item[field_name] is not None:
            values.add(str(item[field_name]))
    return sorted(list(values))

# --- Step 1: Input API ---
st.header("1. Masukkan URL API Eksternal")
api_url = st.text_input("URL API:", placeholder="https://api.example.com/users")
sample_button = st.button("Ambil Sampel Data")

if "sample_fields" not in st.session_state:
    st.session_state.sample_fields = []
    st.session_state.sample_data = []
    st.session_state.enum_mappings = {}

if sample_button and api_url:
    try:
        r = requests.get(api_url, params={"limit": 10})
        r.raise_for_status()
        data = r.json()
        if isinstance(data, dict):
            for val in data.values():
                if isinstance(val, list):
                    data = val
                    break
        if isinstance(data, list) and len(data) > 0:
            st.session_state.sample_data = data
            st.session_state.sample_fields = list(data[0].keys())
            st.success("Data berhasil diambil.")
            st.json(data[0])
        else:
            st.error("Format data tidak valid.")
    except Exception as e:
        st.error(f"Error: {e}")

# --- Step 2: Mapping ---
if st.session_state.sample_fields:
    st.header("2. Mapping Field API ke Data Warehouse")
    
    tables = get_supabase_tables()
    selected_table = st.selectbox("Pilih Tabel Supabase:", tables, key="select_table")

    if selected_table:
        columns_details = get_table_columns_with_details(selected_table)
        column_names = [col['column_name'] for col in columns_details]
        required_columns = {col['column_name'] for col in columns_details if col['is_nullable'] == 'NO'}
        
        mapping = {}
        enum_mappings = {} # Anda perlu menambahkan kembali logika enum di sini jika masih dipakai
        
        st.write("### Mapping Field API ke Kolom Database")
        st.info("Kolom dengan tanda (*) wajib diisi (NOT NULL). Lacak progres Anda di dasbor bawah.")
        
        # --- Bagian looping untuk mapping tidak berubah ---
        for field in st.session_state.sample_fields:
            st.write(f"**Field API: `{field}`**")
            
            sample_values = get_unique_api_values(field, st.session_state.sample_data)
            if sample_values:
                st.write(f"Contoh nilai: {', '.join(sample_values[:5])}")
            
            options = ["-- JANGAN MAP --"] + column_names
            def format_label(col_name):
                if col_name in required_columns:
                    return f"{col_name} (*)"
                return col_name
            
            col = st.selectbox(
                f"Map ke kolom:", 
                options,
                key=f"map_{field}",
                format_func=lambda x: format_label(x) if x != '-- JANGAN MAP --' else x
            )
            
            if col != "-- JANGAN MAP --":
                mapping[field] = col
                # Pastikan Anda memasukkan kembali logika enum mapping Anda di sini
                if is_enum_column(selected_table, col):
                    st.write(f"🔶 **Kolom `{col}` adalah ENUM**")
                    # ... sisa logika enum
            
            st.divider()

        # --- PERUBAHAN BARU: Dasbor Progres dengan Tabs ---
        st.subheader("📊 Dasbor Progres Pemetaan")

        # Kalkulasi progres
        mapped_columns = set(mapping.values())
        
        tab_summary, tab_required, tab_all = st.tabs(["📊 Ringkasan", "⭐️ Checklist Wajib", "📋 Checklist Semua Kolom"])

        with tab_summary:
            st.markdown("#### Ringkasan Progres")
            
            # 1. Progress untuk kolom WAJIB
            if required_columns:
                mapped_required = required_columns.intersection(mapped_columns)
                total_required = len(required_columns)
                num_mapped_required = len(mapped_required)
                progress_value_req = num_mapped_required / total_required
                progress_text_req = f"{num_mapped_required} dari {total_required} kolom wajib telah di-map."
                st.write("**Progres Kolom Wajib:**")
                st.progress(progress_value_req, text=progress_text_req)
            else:
                st.write("**Progres Kolom Wajib:**")
                st.success("✅ Tabel ini tidak memiliki kolom yang wajib diisi.")

            st.divider()

            # 2. Progress untuk SEMUA kolom
            total_columns = len(column_names)
            num_mapped_total = len(mapped_columns)
            progress_value_all = num_mapped_total / total_columns if total_columns > 0 else 0
            progress_text_all = f"{num_mapped_total} dari {total_columns} total kolom telah di-map."
            st.write("**Progres Semua Kolom:**")
            st.progress(progress_value_all, text=progress_text_all)

        with tab_required:
            st.markdown("#### Checklist Status Kolom Wajib")
            if not required_columns:
                st.info("Tidak ada kolom wajib di tabel ini.")
            else:
                cols = st.columns(3)
                col_index = 0
                for req_col in sorted(list(required_columns)):
                    with cols[col_index % 3]:
                        if req_col in mapped_columns:
                            st.markdown(f"✅ `{req_col}`")
                        else:
                            st.markdown(f"❌ `{req_col}`")
                    col_index += 1
        
        with tab_all:
                st.markdown("#### Checklist Status Semua Kolom")
                cols = st.columns(3)
                col_index = 0
                for col_name in sorted(column_names):
                    with cols[col_index % 3]:
                        # Tentukan status dan formatnya
                        status_icon = "✅" if col_name in mapped_columns else "❌"
                        required_marker = "(*)" if col_name in required_columns else ""
                        
                    st.markdown(f"{status_icon} `{col_name}` {required_marker}")
                col_index += 1
        
        st.divider()
        # --- AKHIR PERUBAHAN BARU ---

        # Logika tombol simpan tetap sama, hanya aktif jika SEMUA KOLOM WAJIB sudah di-map
        all_required_mapped = required_columns.issubset(mapped_columns)
        
        if st.button("💾 Simpan Mapping", disabled=not all_required_mapped):
            # ... (logika simpan mapping tidak berubah) ...
            st.success("Mapping berhasil disimpan!") # Ganti dengan logika asli Anda
        
        if not all_required_mapped:
            st.error("Tombol 'Simpan Mapping' akan aktif setelah semua kolom wajib (yang ditandai ❌ pada tab Checklist Wajib) di-map.")

if st.session_state.sample_data and mapping:
    st.header("3. Preview Transformasi Data")
    
    preview_rows = []
    for item in st.session_state.sample_data[:3]:  
        row = {}
        for src_field, dest_col in mapping.items():
            original_value = item.get(src_field)
            
            if src_field in st.session_state.enum_mappings:
                mapped_value = st.session_state.enum_mappings[src_field].get(
                    str(original_value), original_value
                )
                row[dest_col] = mapped_value
            else:
                row[dest_col] = original_value
                
        preview_rows.append(row)
    
    if preview_rows:
        st.write("**Preview data yang akan dikirim:**")
        st.json(preview_rows)

if st.session_state.sample_data and mapping:
    st.header("4. Kirim Data ke Supabase")

    if st.button("🚀 Inject Data"):
        rows = []
        errors = []
        
        for i, item in enumerate(st.session_state.sample_data):
            row = {}
            try:
                for src_field, dest_col in mapping.items():
                    original_value = item.get(src_field)
                    
                    # Terapkan enum mapping jika ada
                    if src_field in st.session_state.enum_mappings:
                        str_value = str(original_value) if original_value is not None else None
                        if str_value and str_value in st.session_state.enum_mappings[src_field]:
                            row[dest_col] = st.session_state.enum_mappings[src_field][str_value]
                        else:
                            # Jika tidak ada mapping, skip atau gunakan nilai default
                            row[dest_col] = None
                    else:
                        row[dest_col] = original_value
                
                rows.append(row)
            except Exception as e:
                errors.append(f"Error pada data ke-{i+1}: {str(e)}")
        
        if errors:
            st.error("Ada error dalam transformasi data:")
            for error in errors:
                st.write(f"⚠️ {error}")
        
        if rows:
            try:
                result = supabase.table(selected_table).insert(rows).execute()
                if result.data:
                    st.success(f"✅ Berhasil mengirim {len(result.data)} data ke tabel '{selected_table}'")
                    
                    # Tampilkan ringkasan enum mapping yang diterapkan
                    if st.session_state.enum_mappings:
                        st.write("**Enum mappings yang diterapkan:**")
                        for field, mappings in st.session_state.enum_mappings.items():
                            st.write(f"- Field `{field}`: {mappings}")
                else:
                    st.error("Gagal mengirim data.")
            except Exception as e:
                st.error(f"Error saat mengirim data: {str(e)}")

# --- Sidebar: Info ---
with st.sidebar:
    st.header("ℹ️ Info")
    st.write("""
    **Fitur:**
    - Deteksi otomatis kolom enum & wajib isi (*)
    - Mapping nilai API ke enum values
    - Peringatan jika kolom wajib tidak di-map
    - Preview transformasi data
    """)
    if st.session_state.enum_mappings:
        st.write("**Current Enum Mappings:**")
        st.json(st.session_state.enum_mappings)