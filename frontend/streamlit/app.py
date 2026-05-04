import streamlit as st
import sys
import os

# Añadir la raíz del proyecto al PYTHONPATH para encontrar el módulo 'ia'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from utils import verificar_usuario, registrar_log
import pandas as pd

st.set_page_config(page_title="Triaje IA", layout="wide")

# Estilos CSS personalizados para mejorar la estética
st.markdown("""
    <style>
    /* Ocultar el menú lateral automático de Streamlit */
    [data-testid="stSidebarNav"] {
        display: none;
    }
    
    .main {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        color: white;
    }
    
    /* Mejorar la barra lateral */
    [data-testid="stSidebar"] {
        background-color: #0f172a;
        border-right: 1px solid #1e293b;
        color: white;
    }

    [data-testid="stSidebar"] .stMarkdown p {
        color: #e2e8f0;
    }

    /* Estilo para los títulos en el fondo oscuro */
    .main h1, .main h2, .main h3 {
        color: #ffffff !important;
    }
    
    /* Botones personalizados */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        background-color: #2563eb;
        color: white;
        border: none;
        font-weight: 600;
        transition: all 0.2s;
    }
    .stButton>button:hover {
        background-color: #1d4ed8;
        border: none;
        color: white;
        transform: translateY(-1px);
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
    }
    
    /* Inputs y Selects */
    .stTextInput>div>div>input, .stSelectbox>div>div>div {
        border-radius: 8px;
    }
    
    /* Contenedores de métricas */
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
        border: 1px solid #e2e8f0;
        margin-bottom: 15px;
    }
    
    /* Títulos */
    h1, h2, h3 {
        color: #0f172a;
        font-weight: 700 !important;
    }
    
    /* Logout button specific */
    .logout-btn button {
        background-color: #ef4444 !important;
    }
    .logout-btn button:hover {
        background-color: #dc2626 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# Inicializar estado de sesión
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user' not in st.session_state:
    st.session_state.user = None

# Login
if not st.session_state.authenticated:
    st.title("Sistema de Triaje Asistido por IA")
    with st.form("login"):
        username = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        submitted = st.form_submit_button("Ingresar")
        if submitted:
            user = verificar_usuario(username, password)
            if user:
                st.session_state.authenticated = True
                st.session_state.user = user
                registrar_log(user['id_usuario'], "login", "Inicio de sesión exitoso")
                st.success("Acceso concedido")
                st.experimental_rerun()
            else:
                st.error("Usuario o contraseña incorrectos")
    st.stop()

# Sidebar con menú mejorado
st.sidebar.markdown(f"## 🏥 Triaje IA")
st.sidebar.caption("v1.3.0-PRO (Build 20260504)")
st.sidebar.markdown(f"**Bienvenido, {st.session_state.user['nombre_usuario']}**")
st.sidebar.markdown("---")

menu = st.sidebar.selectbox(
    "Navegación", 
    ["➕ Nuevo Triaje", "👥 Gestor de Pacientes", "📊 Dashboard Operacional", "📈 Dashboard Gestión", "📄 Reportes PDF"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔗 Enlaces Externos")
st.sidebar.markdown("[🚀 Dashboards React](http://localhost:3000)")

st.sidebar.markdown("---")
with st.sidebar.container():
    st.markdown('<div class="logout-btn">', unsafe_allow_html=True)
    if st.sidebar.button("🚪 Cerrar sesión"):
        registrar_log(st.session_state.user['id_usuario'], "logout", "Cierre de sesión")
        st.session_state.authenticated = False
        st.session_state.user = None
        st.experimental_rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# Navegación
if "Nuevo Triaje" in menu:
    from modules import nuevo_triaje
    nuevo_triaje.show()
elif "Gestor de Pacientes" in menu:
    from modules import gestion_pacientes
    gestion_pacientes.show()
elif "Dashboard Operacional" in menu:
    from modules.dashboard_operativo import show
    show()
elif "Dashboard Gestión" in menu:
    from modules.dashboard_gestion import show
    show()
elif "Reportes PDF" in menu:
    from modules import reportes
    reportes.show()
