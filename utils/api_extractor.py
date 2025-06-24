# api_extractor_module.py

import streamlit as st
import requests
from supabase import Client
import pandas as pd

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

def execute_sequential_join_pipeline(api_data, join_rules):
    """
    Mengeksekusi serangkaian aturan join secara berurutan (A->B, B->C, ...).
    Hasil dari satu join akan menjadi input 'left' untuk join berikutnya.
    """
    if not join_rules:
        print("Error: Tidak ada aturan join yang didefinisikan.")
        return None

    # --- PERUBAHAN 1: Inisialisasi DataFrame hasil ---
    # Kita mulai dengan tabel 'kiri' dari aturan PERTAMA sebagai dasar.
    try:
        base_alias = join_rules[0]['left_api_alias']
        result_df = pd.DataFrame(api_data[base_alias])
    except KeyError:
        print(f"Error: Data untuk alias '{base_alias}' tidak ditemukan.")
        return None

    # Lakukan join secara sekuensial
    for i, rule in enumerate(join_rules):
        try:
            # Ambil tabel 'kanan' untuk join saat ini
            right_alias = rule['right_api_alias']
            right_df = pd.DataFrame(api_data[right_alias])
            
            # --- PERUBAHAN 2: Logika Join Inti ---
            # 'left' DataFrame sekarang adalah 'result_df' yang terus diperbarui.
            # 'left_on' adalah kunci dari 'result_df'.
            # 'right_on' adalah kunci dari 'right_df' yang baru.
            result_df = pd.merge(
                left=result_df,
                right=right_df,
                left_on=rule['left_on_key'],
                right_on=rule['right_on_key'],
                how=rule['join_type'].lower(),
                suffixes=('', f'_{right_alias}')
            )
        except KeyError as e:
            # Error jika kolom kunci join tidak ditemukan
            print(f"Error pada aturan join ke-{i+1}: Kolom kunci tidak ditemukan -> {e}")
            return None
        except Exception as e:
            # Error umum lainnya
            print(f"Error pada aturan join ke-{i+1} ({rule['left_api_alias']} -> {right_alias}): {e}")
            return None

    return result_df



def display_api_extractor(supabase: Client):
    """Menampilkan seluruh komponen untuk ekstraksi data dari API."""

    st.header("1. Masukkan URL API Eksternal")

    # Inisialisasi state
    if 'api_sources' not in st.session_state:
        st.session_state.api_sources = {} # {alias: url}
    if 'join_rules' not in st.session_state:
        st.session_state.join_rules = []
    if 'api_data' not in st.session_state:
        st.session_state.api_data = {} # {alias: data}

    # --- 1. Mengelola Sumber API ---
    with st.expander("1. Daftarkan Sumber API", expanded=True):
        with st.form("api_source_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            api_alias = col1.text_input("Nama Alias (tanpa spasi)", placeholder="mahasiswa")
            api_url = col2.text_input("URL API", placeholder="https://api.example.com/mahasiswa")
            if st.form_submit_button("➕ Tambah API"):
                if api_alias and api_url:
                    st.session_state.api_sources[api_alias] = api_url
                    st.success(f"API '{api_alias}' ditambahkan.")
                else:
                    st.warning("Alias dan URL tidak boleh kosong.")
        
        if st.session_state.api_sources:
            st.write("**API Terdaftar:**")
            st.json(st.session_state.api_sources)

    # --- 2. Ambil Data dari Semua API ---
    if st.session_state.api_sources:
        if st.button("Ambil Data dari Semua API Terdaftar"):
            st.session_state.api_data = {}
            with st.spinner("Mengambil data..."):
                for alias, url in st.session_state.api_sources.items():
                    try:
                        r = requests.get(url)
                        r.raise_for_status()
                        data = r.json()
                        if isinstance(data, dict):
                            data = next((v for v in data.values() if isinstance(v, list)), [])
                        st.session_state.api_data[alias] = data
                        st.success(f"Data untuk '{alias}' berhasil diambil.")
                    except Exception as e:
                        st.error(f"Gagal mengambil data untuk '{alias}': {e}")


    if st.session_state.api_data:
        num_sources = len(st.session_state.api_data)

        if num_sources == 1:
            st.info("💡 Mode Proses Tunggal terdeteksi. Data siap untuk di-map.")
            
            # Langsung siapkan data untuk mapping
            alias = list(st.session_state.api_data.keys())[0]
            single_api_data = st.session_state.api_data[alias]
            
            # Konversi ke format yang konsisten (DataFrame)
            df = pd.DataFrame(single_api_data)
            st.session_state.sample_data = df.to_dict('records')
            st.session_state.sample_fields = list(df.columns)

            st.dataframe(df.head())
            with st.expander("Lihat detail data pertama (JSON)"):
                st.json(st.session_state.sample_data[0])            
        elif num_sources > 1:
            st.info("💡 Mode Join Engine terdeteksi. Silakan definisikan aturan join.")
            with st.expander("2. Definisikan Aturan Join", expanded=True):
                aliases = list(st.session_state.api_sources.keys())
                with st.form("join_rule_form", clear_on_submit=True):
                    st.write("Buat Aturan Join Baru:")
                    cols = st.columns(5)
                    left_api = cols[0].selectbox("API Kiri", aliases, key="left_api")
                    left_key = cols[1].text_input("Key Kiri", placeholder="dosenId")
                    right_api = cols[2].selectbox("API Kanan", aliases, key="right_api")
                    right_key = cols[3].text_input("Key Kanan", placeholder="id")
                    join_type = cols[4].selectbox("Tipe Join", ["INNER", "LEFT", "RIGHT", "OUTER"])
    
                    if st.form_submit_button("🔗 Tambah Aturan Join"):
                        rule = {
                            "left_api_alias": left_api, "left_on_key": left_key,
                            "right_api_alias": right_api, "right_on_key": right_key,
                            "join_type": join_type
                        }
                        st.session_state.join_rules.append(rule)
                
                if st.session_state.join_rules:
                    st.write("**Daftar Aturan Join:**")
                    for i, rule in enumerate(st.session_state.join_rules):
                        st.code(f"{i+1}: {rule['left_api_alias']}.{rule['left_on_key']} {rule['join_type']} JOIN {rule['right_api_alias']}.{rule['right_on_key']}")

    if st.session_state.join_rules:
        if st.button("🚀 Eksekusi Rangkaian Join"):
            with st.spinner("Melakukan join..."):
                final_df = execute_sequential_join_pipeline(st.session_state.api_data, st.session_state.join_rules)

                if final_df is not None:
                    st.success("Join berhasil dieksekusi!")
                    st.session_state.sample_data = final_df.to_dict('records')
                    st.session_state.sample_fields = list(final_df.columns)
                    
                    st.dataframe(final_df.head())
                    with st.expander("Lihat detail hasil join pertama (JSON)"):
                        st.json(st.session_state.sample_data[0])

    mapping = st.session_state.get("mapping", {})
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