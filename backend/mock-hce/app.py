from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"status": "running", "message": "Mock HCE API is active"}), 200

# Datos de prueba para simular historias clínicas
MOCK_DATA = {
    1: {
        "antecedentes": [
            {"fecha": "2023-10-15", "diagnostico": "Hipertensión Arterial", "tratamiento": "Enalapril 10mg"},
            {"fecha": "2024-01-20", "diagnostico": "Diabetes Tipo 2", "tratamiento": "Metformina 850mg"}
        ],
        "alergias": ["Penicilina", "Aspirina"]
    },
    2: {
        "antecedentes": [
            {"fecha": "2022-05-10", "diagnostico": "Asma Bronquial", "tratamiento": "Salbutamol SOS"}
        ],
        "alergias": ["Polen", "Ácaros"]
    }
}

@app.route('/pacientes/<int:id_paciente>/antecedentes', methods=['GET'])
def get_antecedentes(id_paciente):
    # Si no existe el ID, devolvemos datos genéricos para que no salga vacío en las pruebas
    data = MOCK_DATA.get(id_paciente, {
        "antecedentes": [{"fecha": "Sin datos", "diagnostico": "No se registran antecedentes previos", "tratamiento": "N/A"}],
        "alergias": ["No reportadas"]
    })
    return jsonify(data), 200

@app.route('/api/hce/sync', methods=['POST'])
def sync_hce():
    data = request.json
    print(f"Recibida sincronización HCE: {data}")
    return jsonify({"status": "success", "message": "Sincronizado correctamente con HCE"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
