from flask import Flask, request, jsonify
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from twilio.rest import Client

app = Flask(__name__)

# Configuration for SendGrid API
SENDGRID_API_KEY = 'your_sendgrid_api_key'

# Configuration for Twilio API
TWILIO_ACCOUNT_SID = 'your_twilio_account_sid'
TWILIO_AUTH_TOKEN = 'your_twilio_auth_token'
TWILIO_PHONE_NUMBER = 'your_twilio_phone_number'

@app.route('/send-email', methods=['POST'])
def send_email():
    data = request.json
    recipient_email = data.get('email')
    subject = data.get('subject')
    message = data.get('message')

    if not (recipient_email and subject and message):
        return jsonify({'error': 'Missing required parameters'}), 400

    # Send email using SendGrid
    try:
        message = Mail(
            from_email='your_email@example.com',
            to_emails=recipient_email,
            subject=subject,
            html_content=message)
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        return jsonify({'message': 'Email sent successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/send-sms', methods=['POST'])
def send_sms():
    data = request.json
    recipient_phone = data.get('phone')
    message = data.get('message')

    if not (recipient_phone and message):
        return jsonify({'error': 'Missing required parameters'}), 400

    # Send SMS using Twilio
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=recipient_phone
        )
        return jsonify({'message': 'SMS sent successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000, debug=True)
