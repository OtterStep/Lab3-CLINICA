import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from .prompts import PROMPT_TRIAGE

# Cargar variables de entorno usando ruta absoluta relativa a este archivo
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=env_path)

# Configuración de Gemini
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', '').strip()
USE_MOCK = os.getenv('USE_MOCK_IA', 'true').lower().strip() == 'true'

# Configurar el SDK si hay API Key
if GOOGLE_API_KEY and GOOGLE_API_KEY != "tu_api_key_de_gemini_aqui":
    # Se agrega transport='rest' para mejorar la compatibilidad en algunos entornos (como Windows)
    genai.configure(api_key=GOOGLE_API_KEY, transport='rest')

def obtener_recomendacion_ia(datos_triaje):
    """
    Llama al SDK de Gemini o retorna una respuesta mock si no hay clave.
    """
    is_mocking = USE_MOCK or not GOOGLE_API_KEY or GOOGLE_API_KEY == "tu_api_key_de_gemini_aqui" or GOOGLE_API_KEY == ""
    
    if is_mocking:
        return {
            "nivel_urgencia": "moderado",
            "conducta_sugerida": "Realizar evaluación médica en las próximas 2 horas. (MODO SIMULACIÓN ACTIVO)",
            "diagnosticos_diferenciales": "Infección respiratoria, deshidratación, ansiedad.",
            "metodo": "MOCK",
            "prompt_enviado": "MOCK_PROMPT",
            "respuesta_raw": "MOCK_RESPONSE"
        }
    else:
        try:
            prompt = PROMPT_TRIAGE.format(
                presion_arterial_sist=datos_triaje['presion_arterial_sist'],
                presion_arterial_diast=datos_triaje['presion_arterial_diast'],
                frecuencia_cardiaca=datos_triaje['frecuencia_cardiaca'],
                temperatura=datos_triaje['temperatura'],
                saturacion_oxigeno=datos_triaje['saturacion_oxigeno'],
                sintomas=datos_triaje['sintomas']
            )
            
            # Usar el SDK oficial con gemini-flash-latest (nombre validado para este entorno)
            model = genai.GenerativeModel("gemini-flash-latest")
            
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.2
                )
            )
            
            # El SDK ya maneja la respuesta
            content = response.text
            res = json.loads(content)
            res['metodo'] = "GEMINI-AI"
            res['prompt_enviado'] = prompt
            res['respuesta_raw'] = content
            return res
            
        except Exception as e:
            return {
                "nivel_urgencia": "moderado",
                "conducta_sugerida": "Error en SDK de Gemini. Evaluar manualmente.",
                "diagnosticos_diferenciales": f"Error: {str(e)}",
                "metodo": "ERROR-FALLBACK",
                "prompt_enviado": prompt if 'prompt' in locals() else "N/A",
                "respuesta_raw": str(e)
            }
