from flask import Flask, request, jsonify
from flask_cors import CORS
import os, sys
from os import environ
from dotenv import load_dotenv
from invokes import invoke_http

load_dotenv()

import pika
import json
import amqp_connection

app = Flask(__name__)
CORS(app)

booking_URL = "http://booking_service:5001/api/v1/create_booking"
concert_URL = "http://concert_service:5002/api/v1/isConcertSoldOut/"
notification_URL = "http://notification_service:5003/api/v1/send_email"
activity_log_URL = "http://activity_log_service:5004/api/v1/activity_log"
error_URL = "http://error_service:5005/api/v1/error"

# exchangename = environ.get("EXCHANGE_NAME")
# exchangetype = environ.get("EXCHANGE_TYPE")
exchangename = "booking_topic"
exchangetype = "topic"
connection = amqp_connection.create_connection()
channel = connection.channel()

if not amqp_connection.check_exchange(channel, exchangename, exchangetype):
    print(
        "\nCreate the 'Exchange' before running this microservice. \nExiting the program."
    )
    sys.exit(0)


@app.route("/api/v1/book_concert", methods=["POST"])
def book_concert():
    if request.is_json:
        try:
            # booking details (from frontend)
            booking = request.get_json()
            print(booking)
            print("\nReceived a booking order in JSON:", booking)
            print(booking)
            result = processBookConcert(booking)

            return jsonify(result), result["code"]

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            ex_str = (
                str(e)
                + " at "
                + str(exc_type)
                + ": "
                + fname
                + ": line "
                + str(exc_tb.tb_lineno)
            )
            print(ex_str)

            return (
                jsonify(
                    {
                        "code": 500,
                        "message": "book_concert.py internal error: " + ex_str,
                    }
                ),
                500,
            )

    return (
        jsonify(
            {"code": 400, "message": "Invalid JSON input: " + str(request.get_data())}
        ),
        400,
    )


def processBookConcert(booking):
    print("\n-----Invoking booking microservice-----")
    # takes json from frontend and creates a booking
    booking_result = invoke_http(booking_URL, method="POST", json=booking)
    print(booking_result)
    code = booking_result["code"]
    message = json.dumps(booking_result)

    if code not in range(200, 300):
        print(
            "\n\n-----Publishing the (booking error) message with routing_key=booking.error-----"
        )
        channel.basic_publish(
            exchange=exchangename,
            routing_key="booking.error",
            body=message,
            properties=pika.BasicProperties(delivery_mode=2),
        )

        print(
            "Booking status ({:d}) published to the localhost Exchange:".format(code),
            booking_result,
        )

        return {
            "code": 500,
            "data": {"booking_result": booking_result},
            "message": "Booking creation failure sent for error handling.",
        }

    else:
        print(
            "\n\n-----Publishing the (booking info) message with routing_key=booking.info-----"
        )
        channel.basic_publish(
            exchange=exchangename, routing_key="booking.info", body=message
        )

    print("\nBooking published to localhost Exchange.\n")

    concert_id = booking_result["data"]["concert_id"]

    print("\n\n-----Invoking event microservice-----")
    concert_result = invoke_http(concert_URL + str(concert_id), method="GET")
    print("concert_result:", concert_result, "\n")

    code = concert_result["code"]
    if code not in range(200, 300):
        print(
            "\n\n-----Publishing the (event error) message with routing_key=event.error-----"
        )
        message = json.dumps(concert_result)
        channel.basic_publish(
            exchange=exchangename,
            routing_key="event.error",
            body=message,
            properties=pika.BasicProperties(delivery_mode=2),
        )

        print(
            "Booking status ({:d}) published to the localhost Exchange:".format(code),
            concert_result,
        )

        return {
            "code": 500,
            "data": {"concert_result": concert_result},
            "message": "Simulated event error sent for error handling.",
        }

    print("\n\n-----Invoking notification microservice-----")
    # send email from frontend and booking details from booking
    email = booking["email"]
    data = {
        "recipient_email": email,
        "message": "Thank you for booking with us!",
        "subject": "Booking Confirmation",
    }
    notification_result = invoke_http(notification_URL, method="POST", json=data)
    print("notification_result:", notification_result, "\n")

    code = notification_result["code"]
    message = json.dumps(notification_result)

    if code not in range(200, 300):
        print(
            "\n\n-----Publishing the (notification error) message with routing_key=notification.error-----"
        )
        channel.basic_publish(
            exchange=exchangename,
            routing_key="notification.error",
            body=message,
            properties=pika.BasicProperties(delivery_mode=2),
        )
        print(
            "Notification status ({:d}) published to the localhost Exchange:".format(
                code
            ),
            notification_result,
        )
        return {
            "code": 500,
            "data": {"notification_result": notification_result},
            "message": "Notification failure sent for error handling.",
        }

    else:
        print(
            "\n\n-----Publishing the (notification info) message with routing_key=notification.info-----"
        )
        channel.basic_publish(
            exchange=exchangename, routing_key="notification.info", body=message
        )
    print("\nNotification published to localhost Exchange.\n")

    print("###### Booking Successful ######\n")

    return {
        "code": 201,
        "data": {
            "booking_result": booking_result,
        },
    }


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5100, debug=True)
