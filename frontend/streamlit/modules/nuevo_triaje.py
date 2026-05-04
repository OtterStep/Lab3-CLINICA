import streamlit as st
import pandas as pd
import requests
import json
from utils import get_db_connection, registrar_log, guardar_triaje, obtener_pacientes
from ia.modelo import obtener_recomendacion_ia
from datetime import datetime

def show():
    st.markdown('<h1 style="text-align: center;">➕ Nuevo Registro de Triaje</h1>', unsafe_allow_html=True)
    st.markdown("---")

    # Selección de paciente con diseño mejorado
    with st.container():
        col_opt1, col_opt2 = st.columns([1, 1])
        with col_opt1:
            opcion = st.radio("📍 Selección de paciente", ["Paciente existente", "Nuevo paciente"], horizontal=True)
        
    id_paciente = None

    if opcion == "Paciente existente":
        pacientes_df = obtener_pacientes()
        if not pacientes_df.empty:
            with st.expander("🔍 Buscar Paciente", expanded=True):
                # Mostrar también el documento de identidad para facilitar la búsqueda
                pacientes_df['display_name'] = pacientes_df['nombre_completo'] + " (" + pacientes_df['documento_identidad'].fillna("Sin Doc") + ")"
                paciente_seleccionado = st.selectbox("Seleccione el paciente de la lista", pacientes_df['display_name'].tolist())
                # Asegurar que el id_paciente sea un int estándar de Python, no numpy.int64
                id_paciente = int(pacientes_df[pacientes_df['display_name'] == paciente_seleccionado]['id_paciente'].iloc[0])
                
                # Antecedentes con mejor diseño
                try:
                    resp = requests.get(f"http://mock-hce:5001/pacientes/{id_paciente}/antecedentes")
                    if resp.status_code == 200:
                        st.markdown("#### 📜 Antecedentes Clínicos (HCE)")
                        st.json(resp.json())
                    else:
                        st.info("ℹ️ No se encontraron antecedentes previos.")
                except:
                    st.warning("⚠️ Conexión con HCE no disponible.")
        else:
            st.warning("⚠️ No hay pacientes registrados. Por favor, registre uno nuevo.")
    else:
        if 'id_nuevo_paciente' not in st.session_state:
            st.session_state.id_nuevo_paciente = None

        with st.form("nuevo_paciente", clear_on_submit=True):
            st.markdown("### 📝 Registro de Nuevo Paciente")
            c1, c2 = st.columns(2)
            with c1:
                nombre = st.text_input("Nombre completo")
                documento = st.text_input("Documento de identidad")
                fecha_nac = st.date_input("Fecha de nacimiento")
            with c2:
                genero = st.selectbox("Género", ["Masculino", "Femenino", "Otro"])
                contacto = st.text_input("Contacto (Teléfono/Email)")
                direccion = st.text_area("Dirección de residencia")
            
            submitted_paciente = st.form_submit_button("💾 Guardar Paciente")
            
            if submitted_paciente and nombre:
                with get_db_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            INSERT INTO pacientes (nombre_completo, documento_identidad, fecha_nacimiento, genero, contacto, direccion, id_externo_hce)
                            VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id_paciente
                        """, (nombre, documento, fecha_nac, genero, contacto, direccion, None))
                        st.session_state.id_nuevo_paciente = cur.fetchone()[0]
                        conn.commit()
                st.success(f"✅ Paciente {nombre} registrado con éxito.")
        
        id_paciente = st.session_state.id_nuevo_paciente

    if id_paciente:
        st.markdown(f"### 🩺 Evaluación Clínica")
        with st.form("triaje"):
            with st.container():
                st.markdown("#### 📊 Signos Vitales")
                col1, col2, col3 = st.columns(3)
                with col1:
                    presion_sist = st.number_input("P.A. Sistólica (mmHg)", min_value=0, max_value=300, help="Rango normal: 90-140")
                    presion_diast = st.number_input("P.A. Diastólica (mmHg)", min_value=0, max_value=200, help="Rango normal: 60-90")
                with col2:
                    frecuencia = st.number_input("Frecuencia Cardíaca (LPM)", min_value=0, max_value=300, help="Rango normal: 60-100")
                    temperatura = st.number_input("Temperatura (°C)", min_value=30.0, max_value=42.0, step=0.1, help="Rango normal: 36.0-37.5")
                with col3:
                    saturacion = st.number_input("Saturación O₂ (%)", min_value=0, max_value=100, help="Crítico si < 90%")
            
            st.markdown("#### 💬 Descripción de Síntomas")
            sintomas = st.text_area("Describa los síntomas principales reportados por el paciente", height=100)

            submitted = st.form_submit_button("🤖 Analizar con IA y Registrar Triaje")
            
            if submitted:
                # Validaciones médicas antes de IA
                errores_validacion = []
                if saturacion < 90:
                    errores_validacion.append("🚨 Saturación de oxígeno crítica (< 90%).")
                if presion_sist > 180 or presion_sist < 90:
                    st.warning("⚠️ Presión sistólica fuera de rangos normales.")
                if temperatura > 39 or temperatura < 35:
                    st.warning("⚠️ Temperatura corporal fuera de rangos normales.")

                if errores_validacion:
                    for err in errores_validacion:
                        st.error(err)
                    st.info("ℹ️ Proceda con precaución extrema. Se recomienda atención inmediata.")

                datos_triaje = {
                    'presion_arterial_sist': presion_sist,
                    'presion_arterial_diast': presion_diast,
                    'frecuencia_cardiaca': frecuencia,
                    'temperatura': temperatura,
                    'saturacion_oxigeno': saturacion,
                    'sintomas': sintomas
                }
                
                with st.spinner("🧠 La IA está analizando los datos..."):
                    recomendacion = obtener_recomendacion_ia(datos_triaje)
                
                # --- NOTIFICACIÓN INMEDIATA TRAS ANÁLISIS IA ---
                if recomendacion['nivel_urgencia'].lower() in ['alto', 'crítico']:
                    st.warning(f"⚠️ **ATENCIÓN:** El nivel de urgencia es {recomendacion['nivel_urgencia'].upper()}.")
                    
                    # Obtener lista de doctores con Chat ID
                    with get_db_connection() as conn:
                        doctores_df = pd.read_sql("SELECT nombre_usuario, telegram_chat_id FROM usuarios WHERE telegram_chat_id IS NOT NULL", conn)
                    
                    if not doctores_df.empty:
                        doctor_notif = st.selectbox("🏥 Seleccione Doctor para enviar ALERTA INMEDIATA", 
                                                   options=doctores_df['nombre_usuario'].tolist(),
                                                   key="doctor_alerta_sel")
                        chat_id_notif = doctores_df[doctores_df['nombre_usuario'] == doctor_notif]['telegram_chat_id'].iloc[0]
                        
                        if st.button("🚨 ENVIAR ALERTA AHORA", use_container_width=True):
                            with st.status("📡 Enviando alerta prioritaria...", expanded=True) as status:
                                try:
                                    # Obtener nombre del paciente para la notificación
                                    with get_db_connection() as conn:
                                        with conn.cursor() as cur:
                                            cur.execute("SELECT nombre_completo FROM pacientes WHERE id_paciente = %s", (id_paciente,))
                                            nombre_p_notif = cur.fetchone()[0]

                                    # Construcción del mensaje detallado solicitado
                                    mensaje_notif = f"🚨 *ALERTA DE TRIAJE {recomendacion['nivel_urgencia'].upper()}*\n\n"
                                    mensaje_notif += f"👤 *Paciente:* {nombre_p_notif} (ID: {id_paciente})\n"
                                    mensaje_notif += f"📝 *Síntomas:* {datos_triaje['sintomas'][:100]}...\n"
                                    mensaje_notif += f"🩺 *Signos:* PA {presion_sist}/{presion_diast}, FC {frecuencia}, Temp {temperatura}, Sat {saturacion}%\n"
                                    mensaje_notif += f"🩺 *Diagnóstico IA:* {recomendacion['diagnosticos_diferenciales']}\n\n"
                                    
                                    response = requests.post("http://n8n:5678/webhook/notificacion", 
                                                 json={
                                                     "chat_id": str(chat_id_notif), 
                                                     "mensaje": mensaje_notif,
                                                     "paciente_nombre": nombre_p_notif,
                                                     "signos_vitales": {
                                                         "pa": f"{presion_sist}/{presion_diast}",
                                                         "fc": int(frecuencia),
                                                         "temp": float(temperatura),
                                                         "sat": int(saturacion)
                                                     }
                                                 }, 
                                                 timeout=10)
                                    if response.status_code in [200, 201]:
                                        status.update(label=f"✅ Alerta enviada a {doctor_notif}", state="complete", expanded=False)
                                    else:
                                        status.update(label="❌ Error al enviar alerta", state="error")
                                except Exception as e:
                                    st.error(f"Error de conexión n8n: {e}")
                    else:
                        st.info("ℹ️ No hay doctores configurados para recibir alertas automáticas.")
                else:
                    st.success("✅ Triaje guardado correctamente. Nivel de urgencia estable.")

                # Guardar resultado en session_state para persistir
                st.session_state.recomendacion_ia = recomendacion
                st.session_state.datos_evaluacion = datos_triaje

        # Si ya hay una recomendación
        if 'recomendacion_ia' in st.session_state:
            recomendacion = st.session_state.recomendacion_ia
            datos_triaje = st.session_state.datos_evaluacion

            # Resultado del análisis
            st.markdown("---")
            st.markdown("### 🚩 Resultado del Análisis de Triaje")
            
            res_col1, res_col2 = st.columns([1, 2])
            
            color_urgencia = {
                "crítico": "red",
                "alto": "orange",
                "moderado": "blue",
                "bajo": "green"
            }.get(recomendacion['nivel_urgencia'].lower(), "gray")
            
            with res_col1:
                st.markdown(f"""
                    <div style="background-color: {color_urgencia}; padding: 20px; border-radius: 10px; color: white; text-align: center;">
                        <h2 style="color: white; margin: 0;">NIVEL IA</h2>
                        <h1 style="color: white; margin: 0; font-size: 2.5em;">{recomendacion['nivel_urgencia'].upper()}</h1>
                    </div>
                """, unsafe_allow_html=True)
            
            with res_col2:
                st.markdown(f"**💡 Conducta Sugerida:**\n{recomendacion['conducta_sugerida']}")
                st.markdown(f"**🔍 Diagnósticos Diferenciales:**\n{recomendacion['diagnosticos_diferenciales']}")
            
            st.markdown("---")
            st.markdown("### 👨‍⚕️ Validación Profesional")
            st.info("💡 Puede guardar el triaje con la urgencia sugerida o ajustarla si es necesario. Si tiene muchos pacientes, puede guardarlo tal cual y editarlo luego en el módulo de Gestión.")
            
            niveles_disponibles = ["bajo", "moderado", "alto", "crítico"]
            idx_default = niveles_disponibles.index(recomendacion['nivel_urgencia'].lower()) if recomendacion['nivel_urgencia'].lower() in niveles_disponibles else 1
            
            # Formulario final opcional para guardar/corregir
            nuevo_nivel = st.selectbox(
                "¿Desea ajustar el nivel de urgencia sugerido?",
                options=niveles_disponibles,
                index=idx_default,
                key="ajuste_nivel_final"
            )
            
            btn_col1, btn_col2 = st.columns([1, 2])
            with btn_col1:
                finalizar_btn = st.button("💾 GUARDAR REGISTRO FINAL", type="primary", use_container_width=True)

            if finalizar_btn:
                with st.status("🚀 Guardando triaje...", expanded=False) as status:
                    nivel_final = nuevo_nivel
                    ajustado = nuevo_nivel != recomendacion['nivel_urgencia'].lower()

                    # Guardar en BD
                    data_guardado = {
                        'id_paciente': id_paciente,
                        'id_usuario': st.session_state.user['id_usuario'],
                        'presion_arterial_sist': datos_triaje['presion_arterial_sist'],
                        'presion_arterial_diast': datos_triaje['presion_arterial_diast'],
                        'frecuencia_cardiaca': datos_triaje['frecuencia_cardiaca'],
                        'temperatura': datos_triaje['temperatura'],
                        'saturacion_oxigeno': datos_triaje['saturacion_oxigeno'],
                        'sintomas': datos_triaje['sintomas'],
                        'nivel_urgencia': nivel_final,
                        'nivel_urgencia_usuario': nuevo_nivel if ajustado else None,
                        'conducta_sugerida': recomendacion['conducta_sugerida'],
                        'resultado_ia': recomendacion
                    }
                    id_triaje = guardar_triaje(data_guardado)
                    
                    # Sincronización secundaria n8n
                    try:
                        requests.post("http://n8n:5678/webhook/triaje-creado", 
                                     json={"id_triaje": id_triaje, "nivel_urgencia": nivel_final}, timeout=5)
                    except: pass
                    
                    status.update(label="✅ Triaje guardado!", state="complete")

                st.success(f"✅ Triaje #{id_triaje} registrado con éxito.")
                st.balloons()
                if 'recomendacion_ia' in st.session_state:
                    del st.session_state.recomendacion_ia
                    del st.session_state.datos_evaluacion
            
            # Feedback del método
            metodo = recomendacion.get('metodo', 'DESCONOCIDO')
            if metodo == "GEMINI-AI":
                st.caption(f"✨ Análisis realizado por Google Gemini AI.")
            elif metodo == "MOCK":
                st.warning("⚠️ Análisis en modo simulación (Mock)")
