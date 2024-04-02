from flask import Flask, request, jsonify
from flask_sslify import SSLify
from flask_cors import CORS
import mailtrap as mt
from os import environ

app = Flask(__name__)
PORT = 5003
CORS(app)
# sslify = SSLify(app)
MAILTRAP_API_KEY = environ.get("MAILTRAP_API_KEY")

@app.route("/api/v1/send_email", methods=["POST"])
def send_email():
    if request.method == "POST":
        data = request.get_json()
        recipient_email = data.get("recipient_email")
        message = data.get("message")
        subject = data.get("subject")

        if not (recipient_email and message and subject):
            return jsonify({"code": 400, "error": "Missing required parameters"})

        try:
            mail = mt.Mail(
                sender=mt.Address(email="mailtrap@demomailtrap.com", name="BookLah"),
                to=[mt.Address(email=recipient_email)],
                subject=subject,
                text=message,
                category="Integration Test",
            )

            client = mt.MailtrapClient(token=MAILTRAP_API_KEY)
            client.send(mail)

            return jsonify({"code": 200, "message": "Email sent successfully"})

        except Exception as e:
            return jsonify({"code": 500, "message": str(e)})

@app.route("/api/v1/send_refund_emails", methods=["POST"])
def send_refund_emails():
    if request.method == "POST":
        data = request.get_json()

        recipient_emails = data.get("recipient_email") #array of emails
        message = data.get("message")
        subject = data.get("subject")

        if not (recipient_emails and message and subject):
            return jsonify({"code": 400, "error": "Missing required parameters"})

        try:
            for email in recipient_emails:
                mail = mt.Mail(
                    sender=mt.Address(email="mailtrap@demomailtrap.com", name="BookLah"),
                    to=[mt.Address(email=email)],
                    subject=subject,
                    text=message,
                    category="Integration Test",
                )

                client = mt.MailtrapClient(token=MAILTRAP_API_KEY)
                client.send(mail)

            return jsonify({"code": 200, "message": "Refund emails sent successfully"})

        except Exception as e:
            return jsonify({"code": 500, "message": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=True)
