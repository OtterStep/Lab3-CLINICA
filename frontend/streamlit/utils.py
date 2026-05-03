import os
import bcrypt
import psycopg2
import psycopg2.extras
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from datetime import datetime

# Cargar variables de entorno usando ruta absoluta relativa a este archivo
env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
load_dotenv(dotenv_path=env_path)

# Configuración de la base de datos desde variables de entorno
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'triaje_ia'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres')
}

def get_db_connection():
    """Retorna una conexión a PostgreSQL."""
    return psycopg2.connect(**DB_CONFIG)

def verificar_usuario(username, password):
    """Verifica credenciales contra la tabla usuarios."""
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute("SELECT id_usuario, nombre_usuario, contrasena_hash, rol FROM usuarios WHERE nombre_usuario = %s", (username,))
                user = cur.fetchone()
                if user:
                    stored_hash = user['contrasena_hash'].strip()
                    if isinstance(stored_hash, str):
                        stored_hash = stored_hash.encode('utf-8')
                    if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
                        return dict(user)
    except Exception as e:
        st.error(f"Error de base de datos: {e}")
    return None

def registrar_log(id_usuario, accion, detalles, id_triaje=None, ip_origen=''):
    """Registra una acción en logs_auditoria."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO logs_auditoria (id_usuario, id_triaje, accion, detalles, ip_origen)
                    VALUES (%s, %s, %s, %s, %s)
                """, (id_usuario, id_triaje, accion, detalles, ip_origen))
                conn.commit()
    except Exception as e:
        print(f"Error al registrar log: {e}")

def obtener_pacientes():
    """Retorna lista de pacientes para selectores."""
    with get_db_connection() as conn:
        return pd.read_sql("SELECT id_paciente, nombre_completo, documento_identidad, id_externo_hce FROM pacientes ORDER BY nombre_completo", conn)

def guardar_triaje(data):
    """Guarda un triaje y su resultado IA, retorna id_triaje."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Registrar fecha_hora_fin como el momento actual de guardado
            fecha_fin = datetime.now()
            
            cur.execute("""
                INSERT INTO triajes (id_paciente, id_usuario, presion_arterial_sist, presion_arterial_diast,
                                     frecuencia_cardiaca, temperatura, saturacion_oxigeno, sintomas,
                                     nivel_urgencia, nivel_urgencia_usuario, conducta_sugerida, fecha_hora_fin, estado_sincronizacion_hce)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'pendiente')
                RETURNING id_triaje
            """, (
                int(data['id_paciente']), int(data['id_usuario']),
                int(data.get('presion_arterial_sist')) if data.get('presion_arterial_sist') is not None else None,
                int(data.get('presion_arterial_diast')) if data.get('presion_arterial_diast') is not None else None,
                int(data.get('frecuencia_cardiaca')) if data.get('frecuencia_cardiaca') is not None else None,
                float(data.get('temperatura')) if data.get('temperatura') is not None else None,
                int(data.get('saturacion_oxigeno')) if data.get('saturacion_oxigeno') is not None else None,
                data.get('sintomas'),
                data.get('nivel_urgencia'), 
                data.get('nivel_urgencia_usuario'),
                data.get('conducta_sugerida'),
                fecha_fin
            ))
            id_triaje = cur.fetchone()[0]
            
            # Guardar resultado IA si existe
            if 'resultado_ia' in data:
                cur.execute("""
                    INSERT INTO resultados_ia (id_triaje, nivel_urgencia_ia, conducta_sugerida_ia, 
                                             diagnosticos_diferenciales, prompt_enviado, respuesta_raw)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (id_triaje, 
                      data['resultado_ia'].get('nivel_urgencia'), 
                      data['resultado_ia'].get('conducta_sugerida'),
                      data['resultado_ia'].get('diagnosticos_diferenciales'),
                      data['resultado_ia'].get('prompt_enviado'),
                      data['resultado_ia'].get('respuesta_raw')))
            
            conn.commit()
            return id_triaje
