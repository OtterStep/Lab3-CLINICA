import streamlit as st
import pandas as pd
import plotly.express as px
from utils import get_db_connection

def show():
    st.markdown('<h1 style="text-align: center;">📊 Dashboard Operacional</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: gray;">Monitoreo en tiempo real de la atención de triaje</p>', unsafe_allow_html=True)
    st.markdown("---")

    with get_db_connection() as conn:
        # Triajes del día
        df_triajes_hoy = pd.read_sql("""
            SELECT t.id_triaje, p.nombre_completo AS paciente, t.nivel_urgencia, t.fecha_hora,
                   t.presion_arterial_sist, t.presion_arterial_diast, t.frecuencia_cardiaca,
                   t.temperatura, t.saturacion_oxigeno
            FROM triajes t
            JOIN pacientes p ON t.id_paciente = p.id_paciente
            WHERE t.fecha_hora::date = CURRENT_DATE
            ORDER BY t.fecha_hora DESC
        """, conn)

        # Métricas principales
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Triajes Hoy", len(df_triajes_hoy))
        with col2:
            urgentes = len(df_triajes_hoy[df_triajes_hoy['nivel_urgencia'].isin(['crítico', 'alto'])])
            st.metric("Casos Urgentes", urgentes, delta=urgentes, delta_color="inverse")
        with col3:
            st.metric("Temp. Promedio", f"{df_triajes_hoy['temperatura'].mean():.1f} °C" if not df_triajes_hoy.empty else "N/A")
        with col4:
            st.metric("Saturación O₂ Prom.", f"{df_triajes_hoy['saturacion_oxigeno'].mean():.1f} %" if not df_triajes_hoy.empty else "N/A")

        st.markdown("---")
        
        c1, c2 = st.columns([1.5, 1])
        with c1:
            st.markdown("#### 🕒 Últimos Triajes Registrados")
            st.dataframe(
                df_triajes_hoy[['id_triaje', 'paciente', 'nivel_urgencia', 'fecha_hora']], 
                use_container_width=True,
                hide_index=True
            )
        
        with c2:
            st.markdown("#### 📈 Distribución por Prioridad")
            if not df_triajes_hoy.empty:
                df_niveles = df_triajes_hoy.groupby('nivel_urgencia').size().reset_index(name='cantidad')
                fig = px.pie(df_niveles, values='cantidad', names='nivel_urgencia', 
                            color='nivel_urgencia',
                            color_discrete_map={
                                'crítico': '#ef4444',
                                'alto': '#f97316',
                                'moderado': '#3b82f6',
                                'bajo': '#22c55e'
                            },
                            hole=0.4)
                fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No hay datos suficientes para mostrar la distribución.")
