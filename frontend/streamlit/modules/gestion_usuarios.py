import streamlit as st
import pandas as pd
import bcrypt
import psycopg2.extras
from utils import get_db_connection, registrar_log

def show():
    st.markdown('<h1 style="text-align: center;">👨‍⚕️ Gestión de Médicos y Usuarios</h1>', unsafe_allow_html=True)
    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["👥 Lista de Usuarios", "➕ Registrar Médico/Usuario", "⚙️ Mantenimiento"])

    with tab1:
        st.markdown("### 📋 Personal Registrado")
        with get_db_connection() as conn:
            df = pd.read_sql("SELECT id_usuario, nombre_usuario, rol, email, telegram_chat_id, created_at FROM usuarios ORDER BY created_at DESC", conn)
        
        if not df.empty:
            st.dataframe(
                df.rename(columns={
                    'id_usuario': 'ID',
                    'nombre_usuario': 'Usuario',
                    'rol': 'Rol',
                    'email': 'Email',
                    'telegram_chat_id': 'Chat ID Telegram',
                    'created_at': 'Fecha Registro'
                }), 
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("ℹ️ No hay usuarios registrados.")

    with tab2:
        st.markdown("### ➕ Crear Nuevo Acceso")
        with st.form("form_nuevo_usuario", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                nuevo_username = st.text_input("Nombre de Usuario")
                nueva_pass = st.text_input("Contraseña", type="password")
                rol = st.selectbox("Rol del Usuario", ["medico", "administrador"])
            with c2:
                email = st.text_input("Correo Electrónico")
                chat_id = st.text_input("Telegram Chat ID (Para alertas)", help="Obtén tu ID hablando con @userinfobot en Telegram")
            
            if st.form_submit_button("💾 Guardar Usuario"):
                if nuevo_username and nueva_pass:
                    try:
                        # Hashear contraseña
                        hashed = bcrypt.hashpw(nueva_pass.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                        
                        with get_db_connection() as conn:
                            with conn.cursor() as cur:
                                cur.execute("""
                                    INSERT INTO usuarios (nombre_usuario, contrasena_hash, rol, email, telegram_chat_id)
                                    VALUES (%s, %s, %s, %s, %s)
                                """, (nuevo_username, hashed, rol, email, chat_id))
                                conn.commit()
                        st.success(f"✅ Usuario **{nuevo_username}** creado correctamente.")
                        registrar_log(st.session_state.user['id_usuario'], "gestión_usuario", f"Creación de usuario: {nuevo_username}")
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
                else:
                    st.warning("⚠️ Usuario y contraseña son obligatorios.")

    with tab3:
        st.markdown("### ⚙️ Editar / Eliminar Personal")
        with get_db_connection() as conn:
            usuarios_df = pd.read_sql("SELECT id_usuario, nombre_usuario FROM usuarios ORDER BY nombre_usuario", conn)
        
        if not usuarios_df.empty:
            u_opciones = {row['nombre_usuario']: row['id_usuario'] for _, row in usuarios_df.iterrows()}
            u_sel = st.selectbox("Seleccione Usuario", options=list(u_opciones.keys()))
            id_u = u_opciones[u_sel]

            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                    cur.execute("SELECT * FROM usuarios WHERE id_usuario = %s", (id_u,))
                    u_data = cur.fetchone()

            if u_data:
                with st.form("edit_user_form"):
                    st.markdown(f"#### Editando: {u_data['nombre_usuario']}")
                    ec1, ec2 = st.columns(2)
                    with ec1:
                        edit_username = st.text_input("Usuario", value=u_data['nombre_usuario'])
                        edit_rol = st.selectbox("Rol", ["medico", "administrador"], 
                                              index=["medico", "administrador"].index(u_data['rol']) if u_data['rol'] in ["medico", "administrador"] else 0)
                    with ec2:
                        edit_email = st.text_input("Email", value=u_data['email'] or "")
                        edit_chatid = st.text_input("Chat ID Telegram", value=u_data['telegram_chat_id'] or "")
                    
                    st.info("💡 Deje la contraseña en blanco si no desea cambiarla.")
                    edit_pass = st.text_input("Nueva Contraseña (Opcional)", type="password")
                    
                    st.markdown("---")
                    eb1, eb2 = st.columns(2)
                    with eb1:
                        if st.form_submit_button("🔄 Actualizar Datos"):
                            try:
                                with get_db_connection() as conn:
                                    with conn.cursor() as cur:
                                        if edit_pass:
                                            hashed = bcrypt.hashpw(edit_pass.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                                            cur.execute("""
                                                UPDATE usuarios SET nombre_usuario=%s, rol=%s, email=%s, telegram_chat_id=%s, contrasena_hash=%s
                                                WHERE id_usuario=%s
                                            """, (edit_username, edit_rol, edit_email, edit_chatid, hashed, id_u))
                                        else:
                                            cur.execute("""
                                                UPDATE usuarios SET nombre_usuario=%s, rol=%s, email=%s, telegram_chat_id=%s
                                                WHERE id_usuario=%s
                                            """, (edit_username, edit_rol, edit_email, edit_chatid, id_u))
                                        conn.commit()
                                st.success("✅ Usuario actualizado.")
                                st.experimental_rerun()
                            except Exception as e:
                                st.error(f"❌ Error: {e}")
                    
                    with eb2:
                        confirmar = st.checkbox("⚠️ Confirmar baja de usuario")
                        if st.form_submit_button("🗑️ Eliminar Usuario") and confirmar:
                            if id_u == st.session_state.user['id_usuario']:
                                st.error("❌ No puedes eliminar tu propio usuario mientras estás en sesión.")
                            else:
                                with get_db_connection() as conn:
                                    with conn.cursor() as cur:
                                        cur.execute("DELETE FROM usuarios WHERE id_usuario=%s", (id_u,))
                                        conn.commit()
                                st.error("🗑️ Usuario eliminado.")
                                st.experimental_rerun()
