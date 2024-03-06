from flask import Flask, request, jsonify
from flask_cors import CORS

import os, sys
from os import environ

import requests
from invokes import invoke_http

import pika
import json
import amqp_connection

app = Flask(__name__)
CORS(app)

event_URL = "http://localhost:5000/getConcerts"
booking_URL = "http://localhost:5001/create_booking" 
payment_URL = "http://localhost:5002/process_payment"
notification_URL = "http://localhost:5003/notification"
tracking_URL = "http://localhost:5004/tracking"
activity_log_URL = "http://localhost:5005/activity_log"
error_URL = "http://localhost:5006/error"

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
        # make message persistent within the matching queues until it is received by some receiver 

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
    
    print("\nOrder published to RabbitMQ Exchange.\n")


    print('\n\n-----Invoking payment microservice-----')
    payment_result = invoke_http(payment_URL, method="POST", json=booking["data"])
    print("payment_result:", payment_result, '\n')

    code = payment_result["code"]
    if code not in range(200, 300):
        print('\n\n-----Publishing the (payment error) message with routing_key=payment.error-----')
        message = json.dumps(payment_result)
        channel.basic_publish(exchange=exchangename, routing_key="payment.error", 
            body=message, properties=pika.BasicProperties(delivery_mode = 2)) 
        
        print("Booking status ({:d}) published to the RabbitMQ Exchange:".format(code), payment_result)

        return {
            "code": 500,
            "data": {
                     "payment_result": payment_result},
            "message": "Simulated payment error sent for error handling."
        }
    
    
    print('\n\n-----Invoking notification microservice-----')
    #send email from payment and booking details from booking
    notification_result = invoke_http(notification_URL, method="POST", json=jsonify({"email": payment_result["email"], "booking_details": booking_result["data"]}))
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
            "message": "Simulated shipping record error sent for error handling."
        }
    
    print('\n\n-----Invoking tracking microservice-----')
    tracking_result = invoke_http(tracking_URL, method="POST", json=booking_result['data'])
    print("tracking_result:", tracking_result, '\n')

    code = tracking_result["code"]
    if code not in range(200, 300):
        print('\n\n-----Publishing the (tracking error) message with routing_key=tracking.error-----')
        message = json.dumps(tracking_result)
        channel.basic_publish(exchange=exchangename, routing_key="tracking.error", 
            body=message, properties=pika.BasicProperties(delivery_mode = 2)) 
        
        print("Booking status ({:d}) published to the RabbitMQ Exchange:".format(code), tracking_result)

        # 7. Return error
        return {
            "code": 500,
            "data": {"booking_result": booking_result,
                     "tracking_result": tracking_result},
            "message": "Simulated tracking error sent for error handling."
        }

    return { "code": 201,
        "data": {
            "booking_result": booking_result,
            "payment_result": payment_result,
            "notification_result": notification_result,
            "tracking_result": tracking_result,
        }
}


# Execute this program if it is run as a main script (not by 'import')
if __name__ == "__main__":
    print("This is flask " + os.path.basename(__file__) +
          " for placing an order...")
    app.run(host="0.0.0.0", port=5100, debug=True)
    