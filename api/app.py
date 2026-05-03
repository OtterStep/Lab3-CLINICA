from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
import psycopg2.extras
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Cargar variables de entorno usando ruta absoluta relativa a este archivo
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=env_path)

app = Flask(__name__)
CORS(app)  # Permitir solicitudes desde React

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'triaje_ia'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres')
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

@app.route('/', methods=['GET'])
def index():
    """Ruta raíz para verificar que la API está corriendo."""
    return jsonify({
        'status': 'success',
        'message': 'API de Triaje Clínico Asistido por IA operativa',
        'version': '1.0.0',
        'endpoints_disponibles': [
            '/api/operativo/resumen',
            '/api/gestion/metricas',
            '/api/pacientes/top'
        ]
    })

@app.route('/api/operativo/resumen', methods=['GET'])
def resumen_operativo():
    """Métricas del día actual."""
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Total triajes hoy
            cur.execute("SELECT COUNT(*) as total FROM triajes WHERE fecha_hora::date = CURRENT_DATE")
            total = cur.fetchone()['total']
            # Distribución por nivel
            cur.execute("""
                SELECT nivel_urgencia, COUNT(*) as count
                FROM triajes
                WHERE fecha_hora::date = CURRENT_DATE
                GROUP BY nivel_urgencia
            """)
            niveles = cur.fetchall()
            # Tiempo promedio entre triajes (minutos) - ejemplo
            cur.execute("""
                SELECT AVG(EXTRACT(EPOCH FROM (fecha_hora - lag_fecha))/60) as avg_minutes
                FROM (
                    SELECT fecha_hora, LAG(fecha_hora) OVER (ORDER BY fecha_hora) as lag_fecha
                    FROM triajes
                    WHERE fecha_hora::date = CURRENT_DATE
                ) sub
                WHERE lag_fecha IS NOT NULL
            """)
            avg_time = cur.fetchone()['avg_minutes'] or 0
            # Síntomas más frecuentes (extraer de texto)
            cur.execute("""
                SELECT sintomas, COUNT(*) as count
                FROM triajes
                WHERE fecha_hora::date = CURRENT_DATE AND sintomas IS NOT NULL
                GROUP BY sintomas
                ORDER BY count DESC
                LIMIT 5
            """)
            sintomas_top = cur.fetchall()
            # Triajes por hora
            cur.execute("""
                SELECT EXTRACT(HOUR FROM fecha_hora) as hora, COUNT(*) as count
                FROM triajes
                WHERE fecha_hora::date = CURRENT_DATE
                GROUP BY hora
                ORDER BY hora
            """)
            por_hora = cur.fetchall()

    return jsonify({
        'total_triajes': total,
        'niveles': niveles,
        'tiempo_promedio_entre_triajes': round(avg_time, 2),
        'sintomas_top': sintomas_top,
        'triajes_por_hora': por_hora
    })

@app.route('/api/gestion/metricas', methods=['GET'])
def metricas_gestion():
    """Métricas agregadas de gestión."""
    periodo = request.args.get('periodo', 'mes')  # 'mes' o 'anio'
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            if periodo == 'mes':
                # Últimos 12 meses
                cur.execute("""
                    SELECT DATE_TRUNC('month', fecha_hora) as mes, COUNT(*) as total
                    FROM triajes
                    WHERE fecha_hora >= NOW() - INTERVAL '12 months'
                    GROUP BY mes
                    ORDER BY mes
                """)
                evolucion = cur.fetchall()
            else:
                cur.execute("""
                    SELECT EXTRACT(YEAR FROM fecha_hora) as anio, COUNT(*) as total
                    FROM triajes
                    GROUP BY anio
                    ORDER BY anio
                """)
                evolucion = cur.fetchall()

            # Triajes por usuario
            cur.execute("""
                SELECT u.nombre_usuario, COUNT(t.id_triaje) as total
                FROM usuarios u
                LEFT JOIN triajes t ON u.id_usuario = t.id_usuario
                GROUP BY u.id_usuario, u.nombre_usuario
                ORDER BY total DESC
            """)
            por_usuario = cur.fetchall()

            # Distribución global de niveles de urgencia
            cur.execute("""
                SELECT nivel_urgencia, COUNT(*) as total
                FROM triajes
                GROUP BY nivel_urgencia
            """)
            niveles_global = cur.fetchall()

            # Cumplimiento de conductas sugeridas (si se registra en logs o tabla adicional)
            # Simulación: asumimos que todas las conductas sugeridas se cumplen si el triaje se realizó
            cur.execute("SELECT COUNT(*) as total FROM triajes")
            total_triajes = cur.fetchone()['total']
            # Se podría agregar una columna 'conducta_cumplida' en triajes. Por ahora mock.
            cumplimiento = 85  # %

            # Tiempo promedio de atención
            cur.execute("""
                SELECT AVG(EXTRACT(EPOCH FROM (fecha_hora_fin - fecha_hora)))/60 as avg_minutes
                FROM triajes
                WHERE fecha_hora_fin IS NOT NULL AND fecha_hora_fin > fecha_hora
            """)
            tiempo_atencion = cur.fetchone()['avg_minutes'] or 0

    return jsonify({
        'evolucion': evolucion,
        'triajes_por_usuario': por_usuario,
        'niveles_global': niveles_global,
        'cumplimiento_conductas': cumplimiento,
        'tiempo_promedio_atencion_min': round(tiempo_atencion, 2)
    })

@app.route('/api/pacientes/top', methods=['GET'])
def top_pacientes():
    """Pacientes con más triajes."""
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT p.nombre_completo, COUNT(t.id_triaje) as cantidad
                FROM pacientes p
                LEFT JOIN triajes t ON p.id_paciente = t.id_paciente
                GROUP BY p.id_paciente
                ORDER BY cantidad DESC
                LIMIT 10
            """)
            top = cur.fetchall()
    return jsonify(top)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)