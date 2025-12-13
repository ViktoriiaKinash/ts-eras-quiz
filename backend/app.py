from flask import Flask, jsonify
from google.cloud import firestore
from google.cloud import storage

client = storage.Client()
bucket = client.bucket("ts-eras-quiz-images")

app = Flask(__name__)
db = firestore.Client()

@app.route("/health")
def health():
    return {"status": "ok"}

@app.route("/write-test")
def write_test():
    doc = db.collection("test").add({"msg": "hello from flask"})
    return jsonify({"written": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
