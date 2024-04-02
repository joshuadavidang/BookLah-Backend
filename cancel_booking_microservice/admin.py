from flask import Flask, request, jsonify
from flask_cors import CORS
import os, sys
import requests
from invokes import invoke_http
import pika
import json
import amqp_connection

app = Flask(__name__)
CORS(app, supports_credentials=True)
PORT = 5200

booking_URL = "http://booking_service:5001/api/v1/get_concert_bookings/"
update_concert_URL = "http://concert_service:5002/api/v1/updateConcertAvailability/"
notification_URL = "http://notification_service:5003/api/v1/send_refund_emails"
activity_log_URL = "http://activity_log_service:5004/api/v1/activity_log"
error_URL = "http://error_service:5005/api/v1/error"
payment_URL = "http://payment_service:5006/api/v1/refund/"


exchangename = "order_topic"
exchangetype = "topic"

connection = amqp_connection.create_connection()
channel = connection.channel()


if not amqp_connection.check_exchange(channel, exchangename, exchangetype):
    print(
        "\nCreate the 'Exchange' before running this microservice. \nExiting the program."
    )
    sys.exit(0)


@app.route("/api/v1/cancel_concert", methods=["POST"])
def cancel_concert():
    if request.is_json:
        try:
            # booking details (from frontend)
            booking = request.get_json()
            print(booking)
            print("\nReceived a booking order in JSON:", booking)
            result = process_cancel_concert(booking)

            # return jsonify(result), result["code"]
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
                jsonify({"code": 500, "message": "admin.py internal error: " + ex_str}),
                500,
            )

    return (
        jsonify(
            {"code": 400, "message": "Invalid JSON input: " + str(request.get_data())}
        ),
        400,
    )


def process_cancel_concert(booking):
    # Perform necessary actions for canceling concert
    # Example:
    # 1. Notify ticket holders
    # 2. Trigger refunds
    # 3. Cancel event in the event microservice

    print("\n-----Set concert status to CANCELLED-----")
    data = {"concertStatus": "CANCELLED"}

    cancel_concert_result = invoke_http(
        update_concert_URL + booking["concert_id"], method="PUT", json=data
    )
    print("cancel_concert_result:", cancel_concert_result)

    code = cancel_concert_result["code"]
    message = json.dumps(cancel_concert_result)

    if code not in range(200, 300):
        print(
            "\n\n-----Publishing the (concert error) message with routing_key=concert.error-----"
        )
        channel.basic_publish(
            exchange=exchangename,
            routing_key="concert.error",
            body=message,
            properties=pika.BasicProperties(delivery_mode=2),
        )

        print(
            "Concert status ({:d}) published to the localhost Exchange:".format(code),
            cancel_concert_result,
        )

        return {
            "code": 500,
            "data": {"cancel_concert_result": cancel_concert_result},
            "message": "Cancelling concert failure sent for error handling.",
        }

    else:
        print(
            "\n\n-----Publishing the (concert info) message with routing_key=concert.info-----"
        )
        channel.basic_publish(
            exchange=exchangename, routing_key="concert.info", body=message
        )

    print("\n Concert published to localhost Exchange.\n")

    print("\n-----INVOKING BOOKING MICROSERVICE-----")

    # Retrieve list of users who have booked the specified concert from the booking microservice
    # concert_id = booking.get("concert_id")
    booking_result = invoke_http(booking_URL + booking["concert_id"], method="GET")

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
            "message": "Retrieving bookings failure sent for error handling.",
        }

    else:
        print(
            "\n\n-----Publishing the (booking info) message with routing_key=booking.info-----"
        )
        channel.basic_publish(
            exchange=exchangename, routing_key="booking.info", body=message
        )

    print("Booking published to localhost Exchange.\n")

    print("\n-----Triggering refunds-----")
    payment_result = invoke_http(
        payment_URL + booking["concert_id"], method="POST"
    )
    print("refund_result:", payment_result)
    code = payment_result["code"]
    message = json.dumps(payment_result)

    if code not in range(200, 300):
        print(
            "\n\n-----Publishing the (payment error) message with routing_key=refund.error-----"
        )
        channel.basic_publish(
            exchange=exchangename,
            routing_key="refund.error",
            body=message,
            properties=pika.BasicProperties(delivery_mode=2),
        )

        print(
            "Refund status ({:d}) published to the localhost Exchange:".format(code),
            payment_result,
        )

        return {
            "code": 500,
            "data": {"refund_result": payment_result},
            "message": "Triggering refund failure sent for error handling.",
        }

    else:
        print(
            "\n\n-----Publishing the (refund info) message with routing_key=refund.info-----"
        )
        channel.basic_publish(
            exchange=exchangename, routing_key="refund.info", body=message
        )

    print("\nRefund published to localhost Exchange.\n")


    print("\n-----Notifying ticket holders-----")
    print(booking_result)
    booking_arr = booking_result["data"]["bookings"]
    email_arr = []
    for booking_obj in booking_arr: 
        email = booking_obj["email"]
        email_arr.append(email)

    print(email_arr)

    data = {
        "recipient_email": email_arr,
        "subject": "[Alert]",
        "message": "Order has been cancelled",
    }

    notification_result = invoke_http(notification_URL, method="POST", json=data)
    print("notification_result:", notification_result)

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
            "\nNotification status ({:d}) published to the RabbitMQ Exchange:".format(
                code
            ),
            notification_result,
        )

        return {
            "code": 500,
            "data": {"notification_result": notification_result},
            "message": "Notification creation failure sent for error handling.",
        }
    
    else:
        print(
            "\n\n-----Publishing the (notification info) message with routing_key= notification.info-----"
        )

        channel.basic_publish(
            exchange=exchangename, routing_key="notification.info", body=message
        )

    print("###### Concert Successfully Cancelled ######\n")

    return {
        "code": 201,
        "data": {
            "notification_result": notification_result,
            "payment_result": payment_result,
            "cancel_event_result": cancel_concert_result,
        },
    }


if __name__ == "__main__":
    print("This is flask " + os.path.basename(__file__) + " for canceling concerts...")
    app.run(host="0.0.0.0", port=PORT, debug=True)
