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

booking_URL = "http://booking_service:5001/api/v1/get_bookings"
update_concert_URL = "http://concert_service:5002/api/v1/updateConcertAvailability/"
notification_URL = "http://notification_service:5003/api/v1/send_email"
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
            booking = request.get_json()
            # Retrieve list of users who have booked the specified concert from the booking microservice
            concert_id = booking.get("concert_id")
            booking_response = requests.get(f"{booking_URL}?concert_id={concert_id}")
            if booking_response.status_code == 200:
                booked_users = (
                    booking_response.json().get("data", {}).get("bookings", [])
                )
                print("Booked users for concert_id =", concert_id)
                # Filter booked_users based on concert_id
                booked_users_for_concert = [
                    booking
                    for booking in booked_users
                    if booking.get("concert_id") == concert_id
                ]
                # Print only the booking information for users who booked tickets for the specified concert
                for user_booking in booked_users_for_concert:
                    # process cancel concert
                    result = process_cancel_concert(user_booking, concert_id)
            else:
                return (
                    jsonify(
                        {
                            "code": booking_response.status_code,
                            "message": f"Failed to retrieve booked users from booking microservice: {booking_response.text}",
                        }
                    ),
                    booking_response.status_code,
                )

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


def process_cancel_concert(user_booking, concert_id):
    try:
        # Perform necessary actions for canceling concert
        # Example:
        # 1. Notify ticket holders
        # 2. Trigger refunds
        # 3. Cancel event in the event microservice

        print("\n-----Set concert status to CANCELLED-----")
        data = {"concertStatus": "CANCELLED"}
        cancel_concert_result = invoke_http(
            update_concert_URL + user_booking["concert_id"], method="PUT", json=data
        )
        print("cancel_concert_result:", cancel_concert_result)

        print("\n-----Triggering refunds-----")
        payment_result = invoke_http(
            payment_URL + user_booking["concert_id"], method="POST"
        )
        print("refund_result:", payment_result)

        print("\n-----Notifying ticket holders-----")
        data = {
            "recipient_email": user_booking["email"],
            "subject": "[Alert]",
            "message": "Order has been cancelled",
        }

        notification_result = invoke_http(notification_URL, method="POST", json=data)
        print("notification_result:", notification_result)

        code = notification_result["code"]
        message = json.dumps(notification_result)

        if code not in range(200, 300):
            # Inform the error microservice
            # print('\n\n-----Invoking error microservice as order fails-----')
            print(
                "\n\n-----Publishing the (order error) message with routing_key=order.error-----"
            )

            # invoke_http(error_URL, method="POST", json=order_result)
            channel.basic_publish(
                exchange=exchangename,
                routing_key="order.error",
                body=message,
                properties=pika.BasicProperties(delivery_mode=2),
            )
            # make message persistent within the matching queues until it is received by some receiver
            # (the matching queues have to exist and be durable and bound to the exchange)

            # - reply from the invocation is not used;
            # continue even if this invocation fails
            print(
                "\nOrder status ({:d}) published to the RabbitMQ Exchange:".format(
                    code
                ),
                notification_result,
            )

            # 7. Return error
            return {
                "code": 500,
                "data": {"notification_result": notification_result},
                "message": "Notification creation failure sent for error handling.",
            }
        else:
            # 4. Record new order
            # record the activity log anyway
            # print('\n\n-----Invoking activity_log microservice-----')
            print(
                "\n\n-----Publishing the (notification info) message with routing_key= notification.info-----"
            )

            channel.basic_publish(
                exchange=exchangename, routing_key="notification.info", body=message
            )

        print("###### Concert Successfully Cancelled ######\n")

        return {
            "code": 200,
            "data": {
                "notification_result": notification_result,
                "payment_result": payment_result,
                "cancel_event_result": cancel_concert_result,
            },
        }

    except Exception as e:
        return {
            "code": 500,
            "message": f"An error occurred while processing cancelation: {str(e)}",
        }


if __name__ == "__main__":
    print("This is flask " + os.path.basename(__file__) + " for canceling concerts...")
    app.run(host="0.0.0.0", port=PORT, debug=True)
