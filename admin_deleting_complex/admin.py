from flask import Flask, request, jsonify
from flask_cors import CORS
import os, sys
import requests
from invokes import invoke_http

app = Flask(__name__)
CORS(app)

events_URL = "http://localhost:5000/events"
booking_URL = "http://localhost:5001/booking"
notification_URL = "http://localhost:5002/notification"
payment_URL = "http://localhost:5003/payment"
error_URL = "http://localhost:5004/error"

@app.route("/cancel_concert", methods=['POST'])
def cancel_concert():
    if request.is_json:
        try:
            booking = request.get_json()
            # Retrieve list of users who have booked the specified concert from the booking microservice
            concert_id = booking.get("concert_id")
            booking_response = requests.get(f"{booking_URL}?concert_id={concert_id}")
            if booking_response.status_code == 200:
                booked_users = booking_response.json().get("data", {}).get("bookings", [])
                print("Booked users for concert_id =", concert_id)
                # Filter booked_users based on concert_id
                booked_users_for_concert = [booking for booking in booked_users if booking.get("concert_id") == concert_id]
                # Print only the booking information for users who booked tickets for the specified concert
                for user_booking in booked_users_for_concert:
                    print(user_booking)
            else:
                return jsonify({"code": booking_response.status_code, "message": f"Failed to retrieve booked users from booking microservice: {booking_response.text}"}), booking_response.status_code

            # Process canceling concert
            result = process_cancel_concert(booked_users_for_concert, concert_id)  # Pass booked_users_for_concert and concert_id
            return jsonify(result), result["code"]
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            ex_str = str(e) + " at " + str(exc_type) + ": " + fname + ": line " + str(exc_tb.tb_lineno)
            print(ex_str)
            return jsonify({"code": 500, "message": "admin.py internal error: " + ex_str}), 500
    return jsonify({"code": 400, "message": "Invalid JSON input: " + str(request.get_data())}), 400

def process_cancel_concert(booked_users_for_concert, concert_id):
    try:
        # Perform necessary actions for canceling concert
        # Example:
        # 1. Notify ticket holders
        # 2. Trigger refunds
        # 3. Cancel event in the event microservice

        # Example of notifying ticket holders
        print('\n-----Notifying ticket holders-----')
        notification_result = invoke_http(notification_URL, method='POST', json=booked_users_for_concert)
        print('notification_result:', notification_result)

        # Example of triggering refunds
        print('\n-----Triggering refunds-----')
        payment_result = invoke_http(payment_URL, method='POST', json=booked_users_for_concert)
        print('refund_result:', payment_result)

        # Example of canceling event
        print('\n-----Canceling event-----')
        cancel_event_result = invoke_http(events_URL, method='POST', json=booked_users_for_concert)
        print('cancel_event_result:', cancel_event_result)

        return {"code": 200, "data": {"notification_result": notification_result, "payment_result": payment_result, "cancel_event_result": cancel_event_result}}
    except Exception as e:
        return {"code": 500, "message": f"An error occurred while processing cancelation: {str(e)}"}

if __name__ == "__main__":
    print("This is flask " + os.path.basename(__file__) + " for canceling concerts...")
    app.run(host="0.0.0.0", port=5200, debug=True)
