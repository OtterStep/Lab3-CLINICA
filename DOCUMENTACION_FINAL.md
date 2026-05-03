# 🏥 Sistema de Triaje Clínico Asistido por IA

## 📝 Descripción General
Este sistema permite automatizar y optimizar el proceso de triaje en centros de salud utilizando Inteligencia Artificial (Google Gemini). El objetivo es clasificar la urgencia de los pacientes basándose en signos vitales y síntomas, integrándose con sistemas de Historia Clínica Electrónica (HCE) y enviando notificaciones en tiempo real.

---

## 🛠️ Arquitectura del Sistema
El sistema está compuesto por los siguientes servicios orquestados mediante **Docker**:

1.  **PostgreSQL (BD)**: Almacén central de datos (pacientes, triajes, auditoría).
2.  **API Flask (Backend)**: Punto central de acceso a datos para interfaces externas.
3.  **Streamlit (Frontend Clínico)**: Interfaz principal para el personal de salud (triaje, gestión de pacientes).
4.  **IA Modelo**: Lógica de integración con Google Gemini AI.
5.  **n8n (Automatización)**: Gestión de flujos asíncronos (notificaciones Telegram, sincronización HCE).
6.  **Mock HCE**: Simulador de un sistema de Historia Clínica externo.

---

## 🚀 Funcionalidades Principales

### 1. Registro y Gestión de Pacientes
- Permite registrar nuevos pacientes con datos demográficos y documento de identidad.
- Consulta automáticamente antecedentes en la **HCE externa** al seleccionar un paciente.

### 2. Evaluación de Triaje con IA
- **Captura de Signos Vitales**: Presión arterial, frecuencia cardíaca, temperatura y saturación.
- **Validación Médica**: El sistema alerta si los signos están fuera de rangos normales (ej. Saturación < 90%).
- **Motor de IA**: Envía los datos a **Gemini 1.5 Flash** para obtener:
    - Nivel de urgencia (Crítico, Alto, Moderado, Bajo).
    - Conducta sugerida.
    - Diagnósticos diferenciales.
- **Auditoría**: Se guarda el prompt exacto enviado y la respuesta cruda de la IA para fines legales y de mejora.

### 3. Automatización con n8n
- **Notificaciones**: Si la IA detecta un caso **Crítico** o **Alto**, se envía una alerta inmediata vía **Telegram** al médico de guardia.
- **Sincronización HCE**: Los resultados del triaje se envían automáticamente al sistema de historia clínica externo.
- **Reportes Diarios**: Generación de un resumen de actividad cada 24 horas.

### 4. Dashboards de Control
- **Operativo**: Monitoreo en tiempo real de los triajes realizados hoy.
- **Gestión**: Análisis de tendencias mensuales y productividad por usuario.

---

## ⚙️ Configuración y Despliegue

### Requisitos Previos
- Docker y Docker Desktop.
- API Key de Google Generative AI.
- Bot de Telegram (Token).

### Instalación
1.  Clonar el repositorio.
2.  Configurar el archivo `.env` con tu `GOOGLE_API_KEY`.
3.  Levantar los servicios:
    ```bash
    docker-compose up -d --build
    ```

### Acceso
- **Streamlit**: `http://localhost:8502`
- **n8n**: `http://localhost:5680` (admin/admin123)
- **API**: `http://localhost:5000`

---

## 🔒 Seguridad y Auditoría
- **Autenticación**: Acceso restringido mediante usuario y contraseña (hasheadas con bcrypt).
- **Logs**: Cada acción (login, creación de triaje, consulta IA) queda registrada con IP y timestamp en la tabla `logs_auditoria`.
- **Integridad**: Relaciones estrictas en BD para asegurar que cada triaje tenga su respaldo de IA.

---
*Desarrollado para la optimización de la atención médica de urgencia.*
