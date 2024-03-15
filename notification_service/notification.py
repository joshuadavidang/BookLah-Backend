from flask import Flask, request, jsonify
from flask_sslify import SSLify
import requests
import os
from flask_cors import CORS
from os import environ

app = Flask(__name__)
CORS(app)
sslify = SSLify(app)  # Force HTTPS for all routes

MAILGUN_API_KEY = environ.get("MAILGUN_API_KEY")
MAILGUN_DOMAIN = environ.get("MAILGUN_DOMAIN")


@app.route("/send-email", methods=["POST"])
def send_email():
    if request.method == "POST":
        data = request.get_json()
        recipient_email = data.get("recipient_email")
        subject = data.get("subject")
        message = data.get("message")

        if not (recipient_email and subject and message):
            return jsonify({"error": "Missing required parameters"}), 400

        try:
            response = requests.post(
                f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
                auth=("api", MAILGUN_API_KEY),
                data={
                    "from": "joshuadavidang@outlook.sg",
                    "to": "joshuadavidang@outlook.sg",
                    "subject": "subject",
                    "text": "message",
                },
            )
            print("!!!", response.json())
            return jsonify({"message": "Email sent successfully"}), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5020, debug=True)
