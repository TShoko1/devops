from flask import Flask, jsonify

app = Flask(__name__)

# Обработчик для маршрута /livnes
@app.route('/livnes', methods=['GET', 'POST'])
def livnes():
    return jsonify({"message": "Livnes handler reached."}), 200

# Обработчик для маршрута /rightness
@app.route('/rightness', methods=['GET', 'POST'])
def rightness():
    return jsonify({"message": "Rightness handler reached."}), 200

if __name__ == '__main__':
    # Запуск приложения на localhost:5000
    app.run(debug=True, port=80)
