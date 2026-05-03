import streamlit as st
import pandas as pd
import psycopg2.extras
from utils import get_db_connection, registrar_log

def show():
    st.markdown('<h1 style="text-align: center;">👥 Gestión de Pacientes</h1>', unsafe_allow_html=True)
    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["📋 Directorio de Pacientes", "➕ Nuevo Registro", "⚙️ Mantenimiento"])

    with tab1:
        st.markdown("### 📋 Directorio de Pacientes")
        with get_db_connection() as conn:
            df = pd.read_sql("SELECT id_paciente, nombre_completo, documento_identidad, id_externo_hce, fecha_nacimiento, genero, contacto, created_at FROM pacientes ORDER BY created_at DESC", conn)
        
        if not df.empty:
            # Estilizar el dataframe
            st.dataframe(
                df.rename(columns={
                    'id_paciente': 'ID',
                    'nombre_completo': 'Nombre',
                    'documento_identidad': 'Documento',
                    'id_externo_hce': 'ID HCE',
                    'fecha_nacimiento': 'Nacimiento',
                    'genero': 'Género',
                    'contacto': 'Contacto',
                    'created_at': 'Fecha Registro'
                }), 
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("ℹ️ No hay pacientes registrados actualmente.")

    with tab2:
        st.markdown("### ➕ Registrar Nuevo Paciente")
        with st.form("form_gestion_pacientes", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                nombre = st.text_input("Nombre completo")
                documento = st.text_input("Documento de identidad")
                fecha_nac = st.date_input("Fecha de nacimiento")
            with c2:
                id_externo = st.text_input("ID Externo HCE (Opcional)")
                genero = st.selectbox("Género", ["Masculino", "Femenino", "Otro"])
                contacto = st.text_input("Contacto (Tel/Email)")
            
            direccion = st.text_area("Dirección completa")
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.form_submit_button("💾 Guardar Información del Paciente"):
                if nombre:
                    try:
                        with get_db_connection() as conn:
                            with conn.cursor() as cur:
                                cur.execute("""
                                    INSERT INTO pacientes (nombre_completo, documento_identidad, id_externo_hce, fecha_nacimiento, genero, contacto, direccion)
                                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                                """, (nombre, documento, id_externo, fecha_nac, genero, contacto, direccion))
                                conn.commit()
                        st.success(f"✅ Paciente **{nombre}** registrado exitosamente.")
                        registrar_log(st.session_state.user['id_usuario'], "gestión_paciente", f"Registro manual: {nombre}")
                        st.balloons()
                    except Exception as e:
                        st.error(f"❌ Error al registrar: {e}")
                else:
                    st.warning("⚠️ El nombre es un campo obligatorio.")

    with tab3:
        st.markdown("### ⚙️ Mantenimiento de Datos")
        with get_db_connection() as conn:
            pacientes_df = pd.read_sql("SELECT id_paciente, nombre_completo FROM pacientes ORDER BY nombre_completo", conn)
        
        if not pacientes_df.empty:
            paciente_opciones = {row['nombre_completo']: row['id_paciente'] for _, row in pacientes_df.iterrows()}
            seleccion = st.selectbox("Seleccione el paciente para editar o eliminar", options=list(paciente_opciones.keys()))
            id_p = paciente_opciones[seleccion]

            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                    cur.execute("SELECT * FROM pacientes WHERE id_paciente = %s", (id_p,))
                    p_data = cur.fetchone()

            if p_data:
                with st.form("edit_form"):
                    st.markdown(f"#### Editando a: {p_data['nombre_completo']}")
                    ec1, ec2 = st.columns(2)
                    with ec1:
                        new_nombre = st.text_input("Nombre completo", value=p_data['nombre_completo'])
                        new_documento = st.text_input("Documento de identidad", value=p_data['documento_identidad'] or "")
                        new_fecha = st.date_input("Fecha de nacimiento", value=p_data['fecha_nacimiento'])
                    with ec2:
                        new_hce = st.text_input("ID Externo HCE", value=p_data['id_externo_hce'] or "")
                        new_genero = st.selectbox("Género", ["Masculino", "Femenino", "Otro"], 
                                                 index=["Masculino", "Femenino", "Otro"].index(p_data['genero']) if p_data['genero'] in ["Masculino", "Femenino", "Otro"] else 0)
                        new_contacto = st.text_input("Contacto", value=p_data['contacto'] or "")
                    
                    new_direccion = st.text_area("Dirección", value=p_data['direccion'] or "")
                    
                    st.markdown("---")
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.form_submit_button("🔄 Actualizar Datos"):
                            with get_db_connection() as conn:
                                with conn.cursor() as cur:
                                    cur.execute("""
                                        UPDATE pacientes SET nombre_completo=%s, documento_identidad=%s, id_externo_hce=%s, fecha_nacimiento=%s, genero=%s, contacto=%s, direccion=%s
                                        WHERE id_paciente=%s
                                    """, (new_nombre, new_documento, new_hce, new_fecha, new_genero, new_contacto, new_direccion, id_p))
                                    conn.commit()
                            st.success("✅ Datos actualizados correctamente.")
                            st.experimental_rerun()
                    
                    with col_btn2:
                        confirmar = st.checkbox("⚠️ Confirmar eliminación definitiva")
                        if st.form_submit_button("🗑️ Eliminar Paciente") and confirmar:
                            with get_db_connection() as conn:
                                with conn.cursor() as cur:
                                    cur.execute("DELETE FROM pacientes WHERE id_paciente=%s", (id_p,))
                                    conn.commit()
                            st.error("🗑️ Registro eliminado.")
                            st.experimental_rerun()
        else:
            st.info("ℹ️ No hay registros de pacientes para gestionar.")
