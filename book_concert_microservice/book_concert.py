from flask import Flask, request, jsonify
from flask_cors import CORS

import os, sys
from os import environ

from invokes import invoke_http

import pika
import json
import amqp_connection

app = Flask(__name__)
CORS(app)

booking_URL = "http://localhost:5001/create_booking" 
event_URL = "http://localhost:5002/isConcertSoldOut/"
notification_URL = "http://localhost:5003/notification"
activity_log_URL = "http://localhost:5004/activity_log"
error_URL = "http://localhost:5005/error"

exchangename = environ.get('exchangename')
exchangetype = environ.get('exchangetype')

connection = amqp_connection.create_connection() 
channel = connection.channel()

#if the exchange is not yet created, exit the program
if not amqp_connection.check_exchange(channel, exchangename, exchangetype):
    print("\nCreate the 'Exchange' before running this microservice. \nExiting the program.")
    sys.exit(0)  

@app.route("/book_concert", methods=['POST'])
def book_concert():
    if request.is_json:
        try:
            #booking (from frontend)
            booking = request.get_json()
            print("\nReceived an order in JSON:", booking)

            result = processBookConcert(booking)
            return jsonify(result), result["code"]

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            ex_str = str(e) + " at " + str(exc_type) + ": " + fname + ": line " + str(exc_tb.tb_lineno)
            print(ex_str)

            return jsonify({
                "code": 500,
                "message": "book_concert.py internal error: " + ex_str
            }), 500

    return jsonify({
        "code": 400,
        "message": "Invalid JSON input: " + str(request.get_data())
    }), 400


def processBookConcert(booking):
    print('\n-----Invoking booking microservice-----')
    # takes json from frontend and creates a booking 
    booking_result = invoke_http(booking_URL, method='POST', json=booking["data"])
    print("booking result :", booking_result)

    code = booking_result["code"]
    message = json.dumps(booking_result)
    if code not in range(200, 300):
        print('\n\n-----Publishing the (booking error) message with routing_key=booking.error-----')
        channel.basic_publish(exchange=exchangename, routing_key="booking.error", 
            body=message, properties=pika.BasicProperties(delivery_mode = 2)) 

        print("Booking status ({:d}) published to the RabbitMQ Exchange:".format(code), booking_result)

        return {
            "code": 500,
            "data": {"booking_result": booking_result},
            "message": "Booking creation failure sent for error handling."
        }

    else:
        
        print('\n\n-----Publishing the (booking info) message with routing_key=booking.info-----')        

        channel.basic_publish(exchange=exchangename, routing_key="booking.info", 
            body=message)
    
    print("\nBooking published to RabbitMQ Exchange.\n")

    concert_id = booking_result["data"]["concert_id"]

    print('\n\n-----Invoking event microservice-----')
    event_result = invoke_http(event_URL + concert_id, method="GET")
    print("event_result:", event_result, '\n')

    code = event_result["code"]
    if code not in range(200, 300):
        print('\n\n-----Publishing the (event error) message with routing_key=event.error-----')
        message = json.dumps(event_result)
        channel.basic_publish(exchange=exchangename, routing_key="event.error", 
            body=message, properties=pika.BasicProperties(delivery_mode = 2)) 
        
        print("Booking status ({:d}) published to the RabbitMQ Exchange:".format(code), event_result)

        return {
            "code": 500,
            "data": {
                     "event_result": event_result},
            "message": "Simulated event error sent for error handling."
        }
    
    
    print('\n\n-----Invoking notification microservice-----')
    #send email from frontend and booking details from booking
    notification_result = invoke_http(notification_URL, method="POST", json=jsonify({"email": booking["data"]["email"], "booking_details": booking_result["data"]}))
    print("notification_result:", notification_result, '\n')

    code = notification_result["code"]
    if code not in range(200, 300):
        print('\n\n-----Publishing the (notification error) message with routing_key=notification.error-----')
        message = json.dumps(notification_result)
        channel.basic_publish(exchange=exchangename, routing_key="notification.error", 
            body=message, properties=pika.BasicProperties(delivery_mode = 2)) 
        
        print("Booking status ({:d}) published to the RabbitMQ Exchange:".format(code), notification_result)

        # 7. Return error
        return {
            "code": 500,
            "data": {"booking_result": booking_result,
                     "notification_result": notification_result},
            "message": "Simulated notification record error sent for error handling."
        }
    
    return { "code": 201,
        "data": {
            "booking_result": booking_result,
            "event_result": event_result,
            "notification_result": notification_result,
        }
}


# Execute this program if it is run as a main script (not by 'import')
if __name__ == "__main__":
    print("This is flask " + os.path.basename(__file__) +
          " for placing an order...")
    app.run(host="0.0.0.0", port=5100, debug=True)
    