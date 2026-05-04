# Sistema de Triaje Clínico Asistido por IA

Para una guía detallada de configuración paso a paso, consulta:
👉 **[GUIA_INSTALACION.md](file:///c:/Users/Zaleth/Downloads/Lab03.%20Sistema%20de%20Triaje%20Cl%C3%ADnico%20Asistido%20por%20IA%20-%20copia/Lab03.%20Sistema%20de%20Triaje%20Cl%C3%ADnico%20Asistido%20por%20IA/Lab3-CLINICA/GUIA_INSTALACION.md)**

## Prerrequisitos
- Docker y Docker Compose
- Cuenta de Google AI (Gemini API)
- n8n para automatizaciones (incluido en Docker)

## Inicio Rápido
1. Configura tu `.env` con tu `GOOGLE_API_KEY`.
2. Levanta el sistema:
   ```bash
   docker-compose up -d --build
   ```
3. Accede a los servicios:
   - **Streamlit**: [http://localhost:8502](http://localhost:8502) (User: `admin` / Pass: `admin123`)
   - **React Dashboard**: [http://localhost:3000](http://localhost:3000)
   - **n8n**: [http://localhost:5680](http://localhost:5680)

---
