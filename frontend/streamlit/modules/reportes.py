import streamlit as st
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from utils import get_db_connection
from datetime import datetime

def show():
    st.title("Generar Reportes PDF")
    tipo = st.radio("Tipo de reporte", ["Operacional", "Gestión"])
    fecha_inicio = st.date_input("Fecha inicio", datetime.today())
    fecha_fin = st.date_input("Fecha fin", datetime.today())
    
    # Ajustar fecha_fin para incluir todo el día
    fecha_fin_completa = datetime.combine(fecha_fin, datetime.max.time())

    if st.button("Generar PDF"):
        with get_db_connection() as conn:
            if tipo == "Operacional":
                query = """
                    SELECT t.id_triaje, p.nombre_completo, t.nivel_urgencia, t.fecha_hora,
                           t.presion_arterial_sist, t.presion_arterial_diast, t.frecuencia_cardiaca,
                           t.temperatura, t.saturacion_oxigeno, t.conducta_sugerida
                    FROM triajes t
                    JOIN pacientes p ON t.id_paciente = p.id_paciente
                    WHERE t.fecha_hora BETWEEN %s AND %s
                    ORDER BY t.fecha_hora
                """
                df = pd.read_sql(query, conn, params=(fecha_inicio, fecha_fin_completa))
                titulo = f"Reporte Operacional de Triajes del {fecha_inicio} al {fecha_fin}"
            else:
                query = """
                    SELECT DATE(t.fecha_hora) AS fecha, COUNT(*) AS total_triajes,
                           SUM(CASE WHEN nivel_urgencia = 'crítico' THEN 1 ELSE 0 END) AS criticos,
                           SUM(CASE WHEN nivel_urgencia = 'alto' THEN 1 ELSE 0 END) AS altos,
                           SUM(CASE WHEN nivel_urgencia = 'moderado' THEN 1 ELSE 0 END) AS moderados,
                           SUM(CASE WHEN nivel_urgencia = 'bajo' THEN 1 ELSE 0 END) AS bajos
                    FROM triajes t
                    WHERE t.fecha_hora BETWEEN %s AND %s
                    GROUP BY fecha
                    ORDER BY fecha
                """
                df = pd.read_sql(query, conn, params=(fecha_inicio, fecha_fin_completa))
                titulo = f"Reporte de Gestión de Triajes del {fecha_inicio} al {fecha_fin}"

        # Crear PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # Título
        story.append(Paragraph(titulo, styles['Title']))
        story.append(Spacer(1, 12))

        # Fecha de generación
        story.append(Paragraph(f"Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
        story.append(Spacer(1, 12))

        # Tabla de datos
        if not df.empty:
            # Convertir a lista de listas para ReportLab
            data = [df.columns.tolist()] + df.values.tolist()
            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
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
