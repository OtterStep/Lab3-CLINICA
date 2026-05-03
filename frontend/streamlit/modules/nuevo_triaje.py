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
                id_paciente = pacientes_df[pacientes_df['display_name'] == paciente_seleccionado]['id_paciente'].iloc[0]
                
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
                
                # Resultado del análisis
                st.markdown("---")
                st.markdown("### 🚩 Resultado del Análisis de Triaje")
                
                res_col1, res_col2 = st.columns([1, 2])
                
                # Definir color según nivel de urgencia
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
                
                # Permitir que el médico confirme o corrija el nivel
                st.markdown("---")
                st.markdown("### 👨‍⚕️ Validación Profesional")
                niveles_disponibles = ["bajo", "moderado", "alto", "crítico"]
                idx_default = niveles_disponibles.index(recomendacion['nivel_urgencia'].lower()) if recomendacion['nivel_urgencia'].lower() in niveles_disponibles else 1
                
                nuevo_nivel = st.selectbox(
                    "¿Desea ajustar el nivel de urgencia sugerido?",
                    options=niveles_disponibles,
                    index=idx_default,
                    help="Si cambia el nivel sugerido por la IA, quedará registrado como una decisión médica."
                )
                
                nivel_final = nuevo_nivel
                ajustado = nuevo_nivel != recomendacion['nivel_urgencia'].lower()

                # Guardar en BD
                data_guardado = {
                    'id_paciente': id_paciente,
                    'id_usuario': st.session_state.user['id_usuario'],
                    'presion_arterial_sist': presion_sist,
                    'presion_arterial_diast': presion_diast,
                    'frecuencia_cardiaca': frecuencia,
                    'temperatura': temperatura,
                    'saturacion_oxigeno': saturacion,
                    'sintomas': sintomas,
                    'nivel_urgencia': nivel_final,
                    'nivel_urgencia_usuario': nuevo_nivel if ajustado else None,
                    'conducta_sugerida': recomendacion['conducta_sugerida'],
                    'resultado_ia': recomendacion
                }
                id_triaje = guardar_triaje(data_guardado)
                
                # Registrar auditoría si hubo cambio manual
                if ajustado:
                    registrar_log(
                        st.session_state.user['id_usuario'], 
                        "ajuste_profesional_nivel", 
                        f"Nivel original IA: {recomendacion['nivel_urgencia']}. Ajustado por médico a: {nuevo_nivel}",
                        id_triaje=id_triaje
                    )
                else:
                    registrar_log(st.session_state.user['id_usuario'], "crear_triaje", f"Triaje ID {id_triaje} creado", id_triaje=id_triaje)

                # Feedback del método
                metodo = recomendacion.get('metodo', 'DESCONOCIDO')
                if metodo == "GEMINI-AI":
                    st.caption(f"✨ Análisis realizado por Google Gemini AI. Prompt ID: {id_triaje}")
                elif metodo == "MOCK":
                    st.warning("⚠️ Análisis en modo simulación (Mock)")

                # Webhook n8n
                try:
                    requests.post("http://localhost:5678/webhook/triaje-creado", 
                                 json={"id_triaje": id_triaje, "nivel_urgencia": recomendacion['nivel_urgencia']}, 
                                 timeout=1)
                except: pass

                st.success(f"✅ Registro de triaje #{id_triaje} guardado correctamente.")
                st.balloons()
