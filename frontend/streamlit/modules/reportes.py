import streamlit as st
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from utils import get_db_connection
from datetime import datetime

from reportlab.lib.units import inch

import requests

def show():
    st.title("Generar Reportes PDF")
    
    # --- SECCIÓN DE ENVÍO A DOCTOR ---
    st.markdown("### 👨‍⚕️ Notificar al Doctor")
    if st.button("📤 Enviar Reporte de Hoy al Doctor", use_container_width=True):
        with get_db_connection() as conn:
            query = """
                SELECT nombre, urgencia, diagnostico
                FROM (
                    SELECT DISTINCT ON (t.id_paciente) 
                        p.nombre_completo as nombre, 
                        t.nivel_urgencia as urgencia, 
                        LEFT(t.conducta_sugerida, 50) as diagnostico,
                        t.fecha_hora
                    FROM triajes t
                    JOIN pacientes p ON t.id_paciente = p.id_paciente
                    WHERE t.fecha_hora::date = CURRENT_DATE
                    ORDER BY t.id_paciente, t.fecha_hora DESC
                ) as ultimos_triajes
                ORDER BY CASE 
                    WHEN urgencia = 'crítico' THEN 1
                    WHEN urgencia = 'alto' THEN 2
                    WHEN urgencia = 'moderado' THEN 3
                    ELSE 4 END
            """
            df_hoy = pd.read_sql(query, conn)
            
        if not df_hoy.empty:
            lista_pacientes = df_hoy.to_dict('records')
            try:
                # Webhook para el reporte grupal al doctor
                response = requests.post(
                    "http://n8n:5678/webhook/reporte-doctor",
                    json={
                        "doctor_id": "DR_GENERAL",
                        "fecha": datetime.now().strftime('%d/%m/%Y'),
                        "pacientes": lista_pacientes
                    },
                    timeout=10
                )
                if response.status_code in [200, 201]:
                    st.success(f"✅ Reporte enviado con éxito ({len(lista_pacientes)} pacientes)")
                else:
                    st.error("❌ Error al contactar con el servicio de n8n")
            except Exception as e:
                st.error(f"❌ Error de conexión: {e}")
        else:
            st.warning("⚠️ No hay triajes registrados el día de hoy para reportar.")
    
    st.markdown("---")
    st.markdown("### 📄 Exportar PDF")
    tipo = st.radio("Tipo de reporte", ["Operacional", "Gestión", "Paciente Individual"])
    
    id_paciente_sel = None
    if tipo == "Paciente Individual":
        with get_db_connection() as conn:
            pacientes_df = pd.read_sql("SELECT id_paciente, nombre_completo, documento_identidad FROM pacientes ORDER BY nombre_completo", conn)
        if not pacientes_df.empty:
            id_paciente_sel = st.selectbox("Seleccione Paciente", 
                                          options=pacientes_df['id_paciente'].tolist(),
                                          format_func=lambda x: f"{pacientes_df[pacientes_df['id_paciente']==x]['nombre_completo'].values[0]} ({pacientes_df[pacientes_df['id_paciente']==x]['documento_identidad'].values[0]})")
        else:
            st.warning("No hay pacientes registrados.")
            return

    fecha_inicio = st.date_input("Fecha inicio", datetime.today())
    fecha_fin = st.date_input("Fecha fin", datetime.today())
    
    # Ajustar fecha_fin para incluir todo el día
    fecha_fin_completa = datetime.combine(fecha_fin, datetime.max.time())

    if st.button("Generar PDF"):
        with get_db_connection() as conn:
            if tipo == "Operacional":
                query = """
                    SELECT p.nombre_completo as Paciente, t.nivel_urgencia as Urgencia, 
                           t.presion_arterial_sist || '/' || t.presion_arterial_diast as PA,
                           t.frecuencia_cardiaca as FC, t.temperatura as Temp, t.saturacion_oxigeno as Sat,
                           LEFT(t.conducta_sugerida, 30) as Conducta, t.fecha_hora::date as Fecha
                    FROM triajes t
                    JOIN pacientes p ON t.id_paciente = p.id_paciente
                    WHERE t.fecha_hora BETWEEN %s AND %s
                    ORDER BY t.fecha_hora
                """
                df = pd.read_sql(query, conn, params=(fecha_inicio, fecha_fin_completa))
                titulo = f"Reporte Operacional ({fecha_inicio} al {fecha_fin})"
            elif tipo == "Paciente Individual":
                query = """
                    SELECT t.fecha_hora as Fecha, t.nivel_urgencia as Urgencia,
                           t.presion_arterial_sist || '/' || t.presion_arterial_diast as PA,
                           t.frecuencia_cardiaca as FC, t.temperatura as Temp, t.saturacion_oxigeno as Sat,
                           t.sintomas as Sintomas
                    FROM triajes t
                    WHERE t.id_paciente = %s AND t.fecha_hora BETWEEN %s AND %s
                    ORDER BY t.fecha_hora DESC
                """
                df = pd.read_sql(query, conn, params=(id_paciente_sel, fecha_inicio, fecha_fin_completa))
                nombre_p = pacientes_df[pacientes_df['id_paciente']==id_paciente_sel]['nombre_completo'].values[0]
                titulo = f"Historial de Triajes - {nombre_p}"
            else:
                query = """
                    SELECT DATE(t.fecha_hora) AS fecha, COUNT(*) AS total,
                           SUM(CASE WHEN nivel_urgencia = 'crítico' THEN 1 ELSE 0 END) AS CRI,
                           SUM(CASE WHEN nivel_urgencia = 'alto' THEN 1 ELSE 0 END) AS ALT,
                           SUM(CASE WHEN nivel_urgencia = 'moderado' THEN 1 ELSE 0 END) AS MOD,
                           SUM(CASE WHEN nivel_urgencia = 'bajo' THEN 1 ELSE 0 END) AS BAJ
                    FROM triajes t
                    WHERE t.fecha_hora BETWEEN %s AND %s
                    GROUP BY fecha
                    ORDER BY fecha
                """
                df = pd.read_sql(query, conn, params=(fecha_inicio, fecha_fin_completa))
                titulo = f"Reporte de Gestión ({fecha_inicio} al {fecha_fin})"

        # Crear PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=0.5*inch, rightMargin=0.5*inch)
        styles = getSampleStyleSheet()
        
        # Estilo para texto pequeño para evitar desbordamiento
        small_style = ParagraphStyle(name='Small', parent=styles['Normal'], fontSize=8, leading=10)
        title_style = ParagraphStyle(name='TitleSmall', parent=styles['Title'], fontSize=14)

        story = []
        story.append(Paragraph(titulo, title_style))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}", small_style))
        story.append(Spacer(1, 12))

        if not df.empty:
            # Preparar datos de la tabla con Paragraphs para ajuste de texto
            table_data = []
            header = [Paragraph(f"<b>{col}</b>", small_style) for col in df.columns]
            table_data.append(header)
            
            for _, row in df.iterrows():
                table_data.append([Paragraph(str(val), small_style) for val in row])

            # Ajustar anchos de columna automáticamente
            num_cols = len(df.columns)
            col_widths = [7.5*inch / num_cols] * num_cols
            
            table = Table(table_data, colWidths=col_widths)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('TOPPADDING', (0, 0), (-1, 0), 6),
            ]))
            story.append(table)
        else:
            story.append(Paragraph("No hay datos en el período seleccionado.", styles['Normal']))

        doc.build(story)
        buffer.seek(0)

        st.download_button(
            label="Descargar PDF",
            data=buffer,
            file_name=f"reporte_{tipo}_{fecha_inicio}_{fecha_fin}.pdf",
            mime="application/pdf"
        )
