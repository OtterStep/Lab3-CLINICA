# 🚀 Guía Completa de Instalación - Sistema de Triaje IA

Esta guía detalla los pasos necesarios para desplegar, configurar y poner en marcha el Sistema de Triaje Clínico Asistido por IA.

---

## 📋 Requisitos Previos

Antes de comenzar, asegúrate de tener instalado:
1. **Docker y Docker Compose**: Fundamental para el despliegue de microservicios.
2. **Git**: Para clonar el repositorio.
3. **Google AI Key**: Una API Key de Gemini (puedes obtenerla en [Google AI Studio](https://aistudio.google.com/)).
4. **Telegram Bot Token**: Si deseas habilitar las notificaciones de alerta (opcional).

---

## ⚙️ Paso 1: Configuración de Variables de Entorno

El sistema utiliza un archivo `.env` en la raíz del proyecto para centralizar la configuración.

1. Crea o edita el archivo `.env` en la raíz del proyecto:
   ```env
   # Configuración de Base de Datos
   DB_HOST=postgres
   DB_PORT=5432
   DB_NAME=triaje_ia
   DB_USER=postgres
   DB_PASSWORD=postgres

   # IA (Gemini API)
   GOOGLE_API_KEY=TU_API_KEY_AQUI
   USE_MOCK_IA=false

   # n8n (Autenticación Básica)
   N8N_BASIC_AUTH_ACTIVE=true
   N8N_BASIC_AUTH_USER=admin
   N8N_BASIC_AUTH_PASSWORD=admin123
   ```

---

## 🐳 Paso 2: Despliegue con Docker Compose

El sistema está totalmente dockerizado. Para iniciar todos los servicios:

1. Abre una terminal en la carpeta raíz del proyecto.
2. Ejecuta el comando de construcción y arranque:
   ```bash
   docker-compose up -d --build
   ```
3. Verifica que todos los contenedores estén corriendo:
   ```bash
   docker-compose ps
   ```

### Servicios Desplegados:
- **Streamlit (Triaje/Admin)**: [http://localhost:8502](http://localhost:8502)
- **React (Dashboards)**: [http://localhost:3000](http://localhost:3000)
- **n8n (Automatización)**: [http://localhost:5680](http://localhost:5680)
- **API Flask**: [http://localhost:5000](http://localhost:5000)
- **Base de Datos (Postgres)**: Puerto 5433 (externo)

---

## 🤖 Paso 3: Configuración de n8n y Workflows

Para que las alertas y automatizaciones funcionen, debes importar los flujos en n8n:

1. Accede a **n8n** ([http://localhost:5680](http://localhost:5680)).
2. Logueate con las credenciales del `.env` (Default: `admin` / `admin123`).
3. Ve a **Workflows** -> **Import from File**.
4. Selecciona los archivos situados en `backend/n8n-workflows/`:
   - `workflow_triaje_principal.json` (Core de procesamiento).
   - `workflow_notificacion.json` (Envío de alertas).
5. **Configura las credenciales en n8n**:
   - Crea una credencial de tipo **PostgreSQL** con los datos del `.env`.
   - Crea una credencial de tipo **Telegram Bot** (si usas alertas).
6. **Activa los Workflows**: Asegúrate de que el interruptor de cada flujo esté en "Active".

---

## 🔑 Paso 4: Credenciales de Acceso al Sistema

### Acceso a Streamlit
Por defecto, puedes usar las siguientes credenciales para el panel de triaje y administración:
- **Usuario**: `admin`
- **Contraseña**: `admin123`

---

## 🛠️ Resolución de Problemas Comunes

1. **Error de Cuota (429) en IA**:
   - Verifica que tu `GOOGLE_API_KEY` sea válida y tenga cuota en Google AI Studio.
   - Reinicia el sistema tras cambiar la llave: `docker-compose down; docker-compose up -d`.

2. **No se envían notificaciones**:
   - Asegúrate de que el Chat ID de Telegram esté configurado en el perfil del usuario dentro de la base de datos.
   - Verifica que el workflow `notificacion` en n8n esté activo.

3. **Error de Conexión a Base de Datos**:
   - El contenedor de Postgres tarda unos segundos en estar "Healthy". Espera un momento y refresca la aplicación.

---

## 📊 Módulos Incluidos

- **Panel de Nuevo Triaje**: Registro clínico con análisis de IA en tiempo real.
- **Gestión de Pacientes**: Directorio con historial de urgencia y edición de registros.
- **Gestión de Triajes**: Auditoría y modificación de evaluaciones previas.
- **Reportes PDF**: Generación de informes operacionales y por paciente con diseño optimizado.
- **Dashboard React**: Visualización de métricas avanzadas y búsqueda por DNI.

---
*Guía generada para el Sistema de Triaje Clínico Asistido por IA - 2026*
