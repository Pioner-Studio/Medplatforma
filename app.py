from flask import Flask, render_template, jsonify
from pymongo import MongoClient

app = Flask(__name__)

client = MongoClient("mongodb+srv://medadmin:medpass123@medplatforma.cnv7fbo.mongodb.net/")
db = client["medplatforma"]

doctors_collection = db["doctors"]
events_collection = db["events"]

@app.route("/")
def index():
    return "Medplatforma работает!"

@app.route("/calendar")
def calendar():
    return render_template("calendar.html")

@app.route("/api/resources")
def api_resources():
    doctors = list(doctors_collection.find({}, {"_id": 1, "title": 1}))
    resources = [{"id": str(doc["_id"]), "title": doc["title"]} for doc in doctors]
    return jsonify(resources)

@app.route("/api/events")
def api_events():
    events = list(events_collection.find({}, {"_id": 0}))
    for e in events:
        e["resourceId"] = e.pop("resourceId", None) or e.get("resource_id")
    return jsonify(events)

if __name__ == "__main__":
    app.run(debug=True)