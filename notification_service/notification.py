from flask import Flask, request, jsonify
from flask_sslify import SSLify
import requests
from flask_cors import CORS
from os import environ

app = Flask(__name__)
CORS(app)
sslify = SSLify(app)

MAILERSEND_API_KEY = environ.get("MAILERSEND_API_KEY")
MAILERSEND_DOMAIN_ID = environ.get("MAILERSEND_DOMAIN_ID")


@app.route("/api/v1/send-email", methods=["POST"])
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
                f"https://api.mailersend.com/v1/email",
                headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {MAILERSEND_API_KEY}'},
                json={
                    'from': {'email': 'your_email@example.com'},
                    'to': [{'email': recipient_email}],
                    'subject': subject,
                    'text': message
                }
            )
            response.raise_for_status()
            
            return jsonify({"message": "Email sent successfully"}), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5020, debug=True)
