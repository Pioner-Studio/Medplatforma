from flask import Flask, jsonify
from flask_cors import CORS
from pymongo import MongoClient

app = Flask(__name__)
CORS(app)

# Подключение к MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["medplatforma"]
patients_collection = db["patients"]

@app.route('/')
def index():
    return 'МедПлатформа API подключена к MongoDB!'

@app.route('/patients')
def get_patients():
    patients = list(patients_collection.find())
    for p in patients:
        p['_id'] = str(p['_id'])
    return jsonify(patients)

@app.route('/add_patient')
def add_patient():
    patient = {"name": "Иван Иванов", "age": 34, "status": "new"}
    result = patients_collection.insert_one(patient)
    return jsonify({"inserted_id": str(result.inserted_id)})

if __name__ == '__main__':
    app.run(debug=True)
