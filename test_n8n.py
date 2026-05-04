import requests
import json

def test_notificacion_webhook():
    print("Testing Webhook Notificacion...")
    url = "http://localhost:5680/webhook/notificacion"
    payload = {
        "chat_id": "123456789",
        "mensaje": "🚨 TEST: Alerta de triaje crítico",
        "paciente_nombre": "Paciente de Prueba",
        "signos_vitales": {
            "pa": "120/80",
            "fc": 80,
            "temp": 37.0,
            "sat": 98
        }
    }
    try:
        response = requests.post(url, json=payload, timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

def test_reporte_doctor_webhook():
    print("\nTesting Webhook Reporte Doctor...")
    url = "http://localhost:5680/webhook/reporte-doctor"
    payload = {
        "chat_id": "123456789",
        "doctor_nombre": "Dr. Test",
        "fecha": "04/05/2026",
        "pacientes": [
            {"nombre": "Paciente 1", "urgencia": "crítico", "diagnostico": "Observación inmediata"},
            {"nombre": "Paciente 2", "urgencia": "bajo", "diagnostico": "Control ambulatorio"}
        ]
    }
    try:
        response = requests.post(url, json=payload, timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_notificacion_webhook()
    test_reporte_doctor_webhook()
