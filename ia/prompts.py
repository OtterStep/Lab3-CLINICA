PROMPT_TRIAGE = """
Eres un experto en triaje clínico. Con base en los siguientes signos vitales y síntomas, determina:
- Nivel de urgencia (bajo, moderado, alto, crítico)
- Conducta sugerida (recomendaciones iniciales)
- Diagnósticos diferenciales (máximo 3)

Datos del paciente:
- Presión arterial: {presion_arterial_sist}/{presion_arterial_diast} mmHg
- Frecuencia cardíaca: {frecuencia_cardiaca} lpm
- Temperatura: {temperatura} °C
- Saturación O₂: {saturacion_oxigeno} %
- Síntomas: {sintomas}

Responde en formato JSON con las claves: "nivel_urgencia", "conducta_sugerida", "diagnosticos_diferenciales".
"""
