# api_extractor_module.py

import streamlit as st
import requests
from supabase import Client

@st.cache_data(ttl=3600)
def get_supabase_tables(_supabase: Client):
    result = _supabase.rpc("get_public_tables").execute()
    return sorted([row["table_name"] for row in result.data]) if result.data else []

@st.cache_data(ttl=300)
def get_table_columns_with_details(_supabase: Client, table_name: str):
    result = _supabase.rpc("get_columns_with_details", {"t_name": table_name}).execute()
    return result.data or []

@st.cache_data(ttl=300)
def get_enum_values(_supabase: Client, table_name: str, column_name: str):
    result = _supabase.rpc("get_enum_values", {"schema_name": "public", "table_name": table_name, "column_name": column_name}).execute()
    return [row["enum_value"] for row in result.data] if result.data else []

@st.cache_data(ttl=300)
def is_enum_column(_supabase: Client, table_name: str, column_name: str):
    try:
        result = _supabase.rpc("check_column_is_enum", {"schema_name": "public", "table_name": table_name, "column_name": column_name}).execute()
        return result.data[0].get('is_enum', False) if result.data else False
    except:
        return False

def get_unique_api_values(field_name, sample_data):
    values = {str(item[field_name]) for item in sample_data if field_name in item and item[field_name] is not None}
    return sorted(list(values))

def display_api_extractor(supabase: Client):
    """Menampilkan seluruh komponen untuk ekstraksi data dari API."""
    
    st.header("1. Masukkan URL API Eksternal")
    api_url = st.text_input("URL API:", placeholder="https://api.example.com/users", key="api_url_input")

    if st.button("Ambil Sampel Data"):
        if api_url:
            try:
                r = requests.get(api_url, params={"limit": 10})
                r.raise_for_status()
                data = r.json()
                if isinstance(data, dict):
                    data = next((v for v in data.values() if isinstance(v, list)), data)
                
                if isinstance(data, list) and data:
                    st.session_state.sample_data = data
                    st.session_state.sample_fields = list(data[0].keys())
                    st.success("Sampel data berhasil diambil.")
                    with st.expander("Lihat Sampel Data Pertama"):
                        st.json(data[0])
                else:
                    st.error("Format data dari API tidak valid atau kosong. Harap pastikan respons berisi list/array JSON.")
            except Exception as e:
                st.error(f"Gagal mengambil data dari API: {e}")
        else:
            st.warning("Harap masukkan URL API terlebih dahulu.")

    if "sample_fields" in st.session_state and st.session_state.sample_fields:
        st.header("2. Mapping Field API ke Data Warehouse")
        
        tables = get_supabase_tables(supabase)
        selected_table = st.selectbox("Pilih Tabel Supabase:", tables, key="select_table")
    
        if selected_table:
            columns_details = get_table_columns_with_details(supabase, selected_table)
            column_names = [col['column_name'] for col in columns_details]
            required_columns = {col['column_name'] for col in columns_details if col['is_nullable'] == 'NO'}
            
            mapping = {}
            
            st.write("### Mapping Field API ke Kolom Database")
            st.info("Kolom dengan tanda (*) wajib diisi (NOT NULL). Lacak progres Anda di dasbor bawah.")
            
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
                if col and col != '-- JANGAN MAP --':
                    mapping[field] = col
                
                
                st.divider()
    
            st.subheader("📊 Dasbor Progres Pemetaan")
    
            mapped_columns = set(mapping.values())
            
            tab_summary, tab_required, tab_all = st.tabs(["📊 Ringkasan", "⭐️ Checklist Wajib", "📋 Checklist Semua Kolom"])
    
            with tab_summary:
                st.markdown("#### Ringkasan Progres")
                
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
                            status_icon = "✅" if col_name in mapped_columns else "❌"
                            required_marker = "(*)" if col_name in required_columns else ""
                            
                        st.markdown(f"{status_icon} `{col_name}` {required_marker}")
                    col_index += 1
            
            st.divider()

    

            all_required_mapped = required_columns.issubset(mapped_columns)
            
            if st.button("💾 Simpan Mapping", disabled=not all_required_mapped):

                st.success("Mapping berhasil disimpan!") 
            
            if not all_required_mapped:
                st.error("Tombol 'Simpan Mapping' akan aktif setelah semua kolom wajib (yang ditandai ❌ pada tab Checklist Wajib) di-map.")

    if "sample_fields" in st.session_state and st.session_state.sample_data and mapping:
        st.header("3. Preview Transformasi Data")

        preview_rows = []
        for item in st.session_state.sample_data[:3]:  
            row = {}
            for src_field, dest_col in mapping.items():
                original_value = item.get(src_field)


                row[dest_col] = original_value

            preview_rows.append(row)

        if preview_rows:
            st.write("**Preview data yang akan dikirim:**")
            st.json(preview_rows)

    if "sample_fields" in st.session_state and st.session_state.sample_data and mapping:
        st.header("4. Kirim Data ke Supabase")

        if st.button("🚀 Inject Data"):
            rows = []
            errors = []

            for i, item in enumerate(st.session_state.sample_data):
                row = {}
                try:
                    for src_field, dest_col in mapping.items():
                        original_value = item.get(src_field)

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

                    else:
                        st.error("Gagal mengirim data.")
                except Exception as e:
                    st.error(f"Error saat mengirim data: {str(e)}")