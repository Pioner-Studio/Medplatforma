from flask import Flask, render_template
from db import doctors_collection, patients_collection, events_collection

app = Flask(__name__)

@app.route("/")
def home():
    return "<h2>Medplatforma работает!</h2>"

@app.route("/calendar")
def calendar():
    doctors = list(doctors_collection.find())
    events = list(events_collection.find())
    return render_template("calendar.html", doctors=doctors, events=events)

if __name__ == "__main__":
    app.run(debug=True)
