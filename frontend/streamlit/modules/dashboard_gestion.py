import streamlit as st
import pandas as pd
import plotly.express as px
from utils import get_db_connection

def show():
    st.markdown('<h1 style="text-align: center;">📈 Dashboard de Gestión</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: gray;">Análisis de tendencias y métricas de desempeño</p>', unsafe_allow_html=True)
    st.markdown("---")

    with get_db_connection() as conn:
        # Métricas de alto nivel
        total_triajes = pd.read_sql("SELECT COUNT(*) FROM triajes", conn).iloc[0,0]
        total_pacientes = pd.read_sql("SELECT COUNT(*) FROM pacientes", conn).iloc[0,0]
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Acumulado Triajes", total_triajes)
        m2.metric("Pacientes Únicos", total_pacientes)
        m3.metric("Promedio Diario", round(total_triajes/30, 1) if total_triajes > 0 else 0)

        st.markdown("---")

        col_left, col_right = st.columns(2)

        with col_left:
            st.markdown("#### 📅 Evolución Mensual")
            df_mensual = pd.read_sql("""
                SELECT DATE_TRUNC('month', fecha_hora) AS mes, COUNT(*) AS total_triajes
                FROM triajes
                GROUP BY mes
                ORDER BY mes
            """, conn)
            if not df_mensual.empty:
                fig_mes = px.area(df_mensual, x='mes', y='total_triajes', 
                                 labels={'total_triajes': 'Triajes', 'mes': 'Mes'},
                                 color_discrete_sequence=['#3b82f6'])
                fig_mes.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=300)
                st.plotly_chart(fig_mes, use_container_width=True)

        with col_right:
            st.markdown("#### ⚖️ Distribución Histórica")
            df_global_nivel = pd.read_sql("""
                SELECT nivel_urgencia, COUNT(*) AS total
                FROM triajes
                GROUP BY nivel_urgencia
            """, conn)
            if not df_global_nivel.empty:
                fig_pie = px.pie(df_global_nivel, values='total', names='nivel_urgencia',
                                color='nivel_urgencia',
                                color_discrete_map={
                                    'crítico': '#ef4444',
                                    'alto': '#f97316',
                                    'moderado': '#3b82f6',
                                    'bajo': '#22c55e'
                                },
                                hole=0.4)
                fig_pie.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=300)
                st.plotly_chart(fig_pie, use_container_width=True)

        st.markdown("---")
        
        c_bottom1, c_bottom2 = st.columns([1, 1.2])
        
        with c_bottom1:
            st.markdown("#### 🏆 Top 5 Pacientes Recurrentes")
            df_top_pacientes = pd.read_sql("""
                SELECT p.nombre_completo AS Paciente, COUNT(t.id_triaje) AS Visitas
                FROM pacientes p
                JOIN triajes t ON p.id_paciente = t.id_paciente
                GROUP BY p.id_paciente
                ORDER BY Visitas DESC
                LIMIT 5
            """, conn)
            st.dataframe(df_top_pacientes, use_container_width=True, hide_index=True)

        with c_bottom2:
            st.markdown("#### 👨‍⚕️ Actividad por Usuario")
            df_usuarios = pd.read_sql("""
                SELECT u.nombre_usuario AS usuario, COUNT(t.id_triaje) AS total
                FROM usuarios u
                LEFT JOIN triajes t ON u.id_usuario = t.id_usuario
                GROUP BY u.id_usuario, u.nombre_usuario
                ORDER BY total DESC
            """, conn)
            fig_bar = px.bar(df_usuarios, x='usuario', y='total', 
                            color='total', color_continuous_scale='Blues')
            fig_bar.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=300)
            st.plotly_chart(fig_bar, use_container_width=True)
