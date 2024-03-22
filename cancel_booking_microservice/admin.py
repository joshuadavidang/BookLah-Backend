from flask import Flask, request, jsonify
from flask_cors import CORS
import os, sys
import requests
from invokes import invoke_http

import pika
import json
import amqp_connection

app = Flask(__name__)
CORS(app)

booking_URL = "http://localhost:5001/api/v1/create_booking"
concert_URL = "http://localhost:5002/api/v1/isConcertSoldOut/"
notification_URL = "http://localhost:5003/api/v1/send_email"
activity_log_URL = "http://localhost:5004/api/v1/activity_log"
error_URL = "http://localhost:5005/api/v1/error"
payment_URL= "http://localhost:5006/api/v1/refund_payment"


exchangename = "order_topic" # exchange name
exchangetype="topic" # use a 'topic' exchange to enable interaction
connection = amqp_connection.create_connection() 
channel = connection.channel()

#if the exchange is not yet created, exit the program
if not amqp_connection.check_exchange(channel, exchangename, exchangetype):
    print("\nCreate the 'Exchange' before running this microservice. \nExiting the program.")
    sys.exit(0)  # Exit with a success status

@app.route("/api/v1/cancel_concert", methods=['POST'])
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

        # Example of canceling event
        print('\n-----Invoking concert microservice-----')
        cancel_concert_result = invoke_http(concert_URL, method='POST', json=booked_users_for_concert)
        print('cancel_concert_result:', cancel_concert_result)
        code = cancel_concert_result["code"]
        message = json.dumps(cancel_concert_result)

        if code not in range(200, 300):
            print(
                "\n\n-----Publishing the (event error) message with routing_key=event.error-----"
            )
            
            channel.basic_publish(
                exchange=exchangename,
                routing_key="event.error",
                body=message,
                properties=pika.BasicProperties(delivery_mode=2),
            )

            print(
                "Booking status ({:d}) published to the localhost Exchange:".format(code),
                cancel_concert_result,
            )

            return {
                "code": 500,
                "data": {"concert_result": cancel_concert_result},
                "message": "Simulated event error sent for error handling.",
            }


         # Example of triggering refunds
        print('\n-----Triggering refunds-----')
        payment_result = invoke_http(payment_URL, method='POST', json=booked_users_for_concert)
        print('refund_result:', payment_result)

        if code not in range(200, 300):
            print(
                "\n\n-----Publishing the (event error) message with routing_key=event.error-----"
            )
            message = json.dumps(payment_result)
            channel.basic_publish(
                exchange=exchangename,
                routing_key="event.error",
                body=message,
                properties=pika.BasicProperties(delivery_mode=2),
            )

            print(
                "Booking status ({:d}) published to the localhost Exchange:".format(code),
                payment_result,
            )

            return {
                "code": 500,
                "data": {"payment_result": payment_result},
                "message": "Simulated event error sent for error handling.",
            }

        # Example of notifying ticket holders
        print('\n-----Notifying ticket holders-----')
        notification_result = invoke_http(notification_URL, method='POST', json=booked_users_for_concert)
        print('notification_result:', notification_result)

        code = notification_result["code"]
        message = json.dumps(notification_result)

    
        if code not in range(200, 300):
            # Inform the error microservice
            #print('\n\n-----Invoking error microservice as order fails-----')
            print('\n\n-----Publishing the (order error) message with routing_key=order.error-----')

            # invoke_http(error_URL, method="POST", json=order_result)
            channel.basic_publish(exchange=exchangename, routing_key="order.error", 
                body=message, properties=pika.BasicProperties(delivery_mode = 2)) 
            # make message persistent within the matching queues until it is received by some receiver 

            # - reply from the invocation is not used;
            # continue even if this invocation fails        
            print("\nOrder status ({:d}) published to the RabbitMQ Exchange:".format(
                code), notification_result)

            # 7. Return error
            return {
                "code": 500,
                "data": {"notification_result": notification_result},
                "message": "Notification creation failure sent for error handling."
            }
        else:
            print('\n\n-----Publishing the (notification info) message with routing_key= notification.info-----')        
        
            channel.basic_publish(exchange=exchangename, routing_key="notification.info", 
                body=message)
        
        print("\nNotification published to localhost Exchange.\n")

        print("###### Booking Successfully Cancelled ######\n")


        return {
            "code": 200, 
            "data": {
                "notification_result":notification_result
            }
        }
    

if __name__ == "__main__":
    print("This is flask " + os.path.basename(__file__) + " for canceling concerts...")
    app.run(host="0.0.0.0", port=5200, debug=True)