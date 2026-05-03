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
                paciente_seleccionado = st.selectbox("Seleccione el paciente de la lista", pacientes_df['nombre_completo'].tolist())
                id_paciente = pacientes_df[pacientes_df['nombre_completo'] == paciente_seleccionado]['id_paciente'].iloc[0]
                
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
                            INSERT INTO pacientes (nombre_completo, fecha_nacimiento, genero, contacto, direccion)
                            VALUES (%s, %s, %s, %s, %s) RETURNING id_paciente
                        """, (nombre, fecha_nac, genero, contacto, direccion))
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
                    presion_sist = st.number_input("P.A. Sistólica (mmHg)", min_value=0, max_value=300, help="Presión alta")
                    presion_diast = st.number_input("P.A. Diastólica (mmHg)", min_value=0, max_value=200, help="Presión baja")
                with col2:
                    frecuencia = st.number_input("Frecuencia Cardíaca (LPM)", min_value=0, max_value=300)
                    temperatura = st.number_input("Temperatura (°C)", min_value=30.0, max_value=42.0, step=0.1)
                with col3:
                    saturacion = st.number_input("Saturación O₂ (%)", min_value=0, max_value=100)
            
            st.markdown("#### 💬 Descripción de Síntomas")
            sintomas = st.text_area("Describa los síntomas principales reportados por el paciente", height=100)

            submitted = st.form_submit_button("🤖 Analizar con IA y Registrar Triaje")
            
            if submitted:
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
                            <h2 style="color: white; margin: 0;">NIVEL</h2>
                            <h1 style="color: white; margin: 0; font-size: 2.5em;">{recomendacion['nivel_urgencia'].upper()}</h1>
                        </div>
                    """, unsafe_allow_html=True)
                
                with res_col2:
                    st.markdown(f"**💡 Conducta Sugerida:**\n{recomendacion['conducta_sugerida']}")
                    st.markdown(f"**🔍 Diagnósticos Diferenciales:**\n{recomendacion['diagnosticos_diferenciales']}")
                
                # Feedback del método
                metodo = recomendacion.get('metodo', 'DESCONOCIDO')
                if metodo == "GEMINI-AI":
                    st.caption("✨ Análisis realizado por Google Gemini AI")
                elif metodo == "MOCK":
                    st.warning("⚠️ Análisis en modo simulación (Mock)")
                
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
                    'nivel_urgencia': recomendacion['nivel_urgencia'],
                    'conducta_sugerida': recomendacion['conducta_sugerida'],
                    'resultado_ia': recomendacion
                }
                id_triaje = guardar_triaje(data_guardado)
                registrar_log(st.session_state.user['id_usuario'], "crear_triaje", f"Triaje ID {id_triaje} creado")

                # Webhook n8n
                try:
                    requests.post("http://localhost:5678/webhook/triaje-creado", 
                                 json={"id_triaje": id_triaje, "nivel_urgencia": recomendacion['nivel_urgencia']}, 
                                 timeout=1)
                except: pass

                st.success(f"✅ Registro de triaje #{id_triaje} guardado correctamente.")
                st.balloons()
