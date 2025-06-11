from flask import Flask, jsonify, request, Response
from flask_cors import CORS
from pymongo import MongoClient
from bson.objectid import ObjectId
import json

app = Flask(__name__)
CORS(app)

client = MongoClient("mongodb://localhost:27017/")
db = client["medplatforma"]
patients_collection = db["patients"]

@app.route('/patients', methods=['GET'])
def get_patients():
    patients = list(patients_collection.find())
    for p in patients:
        p['_id'] = str(p['_id'])
    return Response(
        json.dumps(patients, ensure_ascii=False),
        content_type='application/json; charset=utf-8'
    )

@app.route('/add_patient', methods=['POST'])
def add_patient():
    data = request.get_json()
    result = patients_collection.insert_one(data)
    return jsonify({"inserted_id": str(result.inserted_id)})

@app.route('/update_patient/<patient_id>', methods=['PUT'])
def update_patient(patient_id):
    data = request.get_json()
    # !!! ВАЖНО: убираем лишние символы из id !!!
    clean_id = patient_id.strip()
    try:
        result = patients_collection.update_one(
            {"_id": ObjectId(clean_id)},
            {"$set": data}
        )
        if result.matched_count:
            return jsonify({"message": "Пациент обновлён", "patient_id": clean_id})
        else:
            return jsonify({"message": "Пациент не найден"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    
@app.route('/delete_patient/<patient_id>', methods=['DELETE'])
def delete_patient(patient_id):
    result = patients_collection.delete_one({"_id": ObjectId(patient_id.strip())})
    if result.deleted_count:
        return jsonify({"message": "Пациент удалён", "patient_id": patient_id})
    return jsonify({"message": "Пациент не найден"}), 404

if __name__ == '__main__':
    app.run(debug=True)
    