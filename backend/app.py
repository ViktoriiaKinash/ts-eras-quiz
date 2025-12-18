from enum import Enum
import random
from flask import Flask, jsonify, request
from flask_cors import CORS
from google.cloud import firestore, storage, pubsub_v1
import logging
import os
import datetime
import json

class Era(Enum):
    _1989 = "1989"
    EVERMORE = "evermore"
    FEARLESS = "fearless"
    FOLKLORE = "folklore"
    LOVER = "lover"
    MIDNIGHTS = "midnights"
    REPUTATION = "reputation"
    SPEAK_NOW = "speak-now"
    TLOAS = "tloas"
    TTPD = "ttpd"

ALL_ERAS = [e.value for e in Era]

# ---------------------------
# Initialize clients
# ---------------------------
db = firestore.Client()
storage_client = storage.Client()
bucket_name = "ts-eras-quiz-images"
bucket = storage_client.bucket(bucket_name)
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(
     "ts-eras-quiz", "quiz-topic"
)

# ---------------------------
# Flask app
# ---------------------------
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": ["*"]}})
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

@app.route("/api/quiz", methods=["POST"])
def quiz():
    try:
        # ---------------------------
        # Randomly pick an era from enum
        # ---------------------------
        selected_era = random.choice(ALL_ERAS)
        logging.info(f"Selected era: {selected_era}")

        # ---------------------------
        # Pick image
        # ---------------------------
        images = [blob.name for blob in storage_client.list_blobs(bucket_name, prefix=f"{selected_era}/") if not blob.name.endswith("/")]
        if not images:
            logging.error(f"No images found for era {selected_era}")
            return jsonify({"error": "No images available for the selected era"}), 500

        selected_image = random.choice(images)
        image_url = f"https://storage.googleapis.com/{bucket_name}/{selected_image}"
        logging.info(f"Selected image: {selected_image}")
        data = {}
        if request.is_json:
            data = request.get_json(silent=True) or {}
        else:
            try:
                data = request.form.to_dict() or {}
            except Exception:
                data = {}

        user_email = data.get("user_email") or request.args.get("user_email") or os.environ.get("DEFAULT_USER_EMAIL", "viktoria.kinash12@gmail.com")
        logging.info(f"Using user_email: {user_email}")

        # ---------------------------
        # Store quiz result in Firestore
        # ---------------------------
        doc_ref = db.collection("quiz_results").add({
            "era": selected_era,
            "image": selected_image,
            "user_email": user_email,
            "created_at": firestore.SERVER_TIMESTAMP,
        })
        logging.info(f"Stored quiz result with ID: {doc_ref[1].id}")

        # ---------------------------
        # Publish message to Pub/Sub
        # ---------------------------

        publisher.publish(
            topic_path,
            json.dumps({
                "era": selected_era,
                "timestamp": datetime.datetime.now(tz=datetime.timezone.utc).isoformat(),
                "user_email": user_email
            }).encode("utf-8")
        )

        # ---------------------------
        # Return response
        # ---------------------------
        response = {
            "era": selected_era,
            "image_url": image_url,
            "message": "Quiz item generated successfully"
        }
        return jsonify(response)

    except Exception as e:
        logging.exception("Error generating quiz item")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
