from flask import Flask, request, jsonify
from flask_cors import CORS
import os, sys
from os import environ
from dotenv import load_dotenv
from invokes import invoke_http
import amqp_connection

app = Flask(__name__)
CORS(app)

load_dotenv()

import pika
import json
import amqp_setup

booking_URL = "http://localhost:5001/get_bookings"
forum_URL = "http://localhost:5003/getPosts"


# exchangename = environ.get("EXCHANGE_NAME")
# exchangetype = environ.get("EXCHANGE_TYPE")
exchangename = "booking_topic"
exchangetype = "topic"
connection = amqp_setup.create_connection()
channel = connection.channel()

if not amqp_connection.check_exchange(channel, exchangename, exchangetype):
    print(
        "\nCreate the 'Exchange' before running this microservice. \nExiting the program."
    )
    sys.exit(0)  # Exit with a success status


@app.route("/get_forum", methods=["POST"])
def get_forum():
    # Simple check of input format and data of the request are JSON
    if request.is_json:
        try:
            booking = request.get_json()
            print("\nReceived an order in JSON:", booking)

            # do the actual work
            # 1. Get forum based on concert ID
            result = processGetForum(booking)
            print("\n------------------------")
            print("\nresult: ", result)
            return jsonify(result), result["code"]

        except Exception as e:
            # Unexpected error in code
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
                        "message": "forum_complex.py internal error: " + ex_str,
                    }
                ),
                500,
            )

    # if reached here, not a JSON request.
    return (
        jsonify(
            {"code": 400, "message": "Invalid JSON input: " + str(request.get_data())}
        ),
        400,
    )


def processGetForum(booking):
    try:
        # Invoke booking microservice to get concert ID
        print("\n-----Invoking booking microservice to get concert ID-----")
        booking_result = invoke_http(booking_URL, method="POST", json=order)
        print("booking_result:", booking_result)

        # Check the booking result; if a failure, publish error to error microservice and return the error
        booking_code = booking_result["code"]
        if booking_code not in range(200, 300):
            # Publish error message to error microservice
            error_message = json.dumps(booking_result)
            channel.basic_publish(
                exchange=exchangename,
                routing_key="booking.error",
                body=error_message,
                properties=pika.BasicProperties(delivery_mode=2),
            )
            # Return error message
            return (
                jsonify(
                    {
                        "code": 500,
                        "message": "Booking microservice failed to retrieve concert ID.",
                    }
                ),
                500,
            )

        # Extract concert ID from booking result
        concert_id = booking_result["data"]["concert_id"]

        # Invoke forum microservice to get forum based on concert ID
        print("\n-----Invoking forum microservice to get forum-----")
        forum_result = invoke_http(
            forum_URL, method="POST", json={"concert_id": concert_id}
        )
        print("forum_result:", forum_result)

        # Check the forum result; if a failure, publish error to error microservice and return the error
        forum_code = forum_result["code"]
        if forum_code not in range(200, 300):
            # Publish error message to error microservice
            error_message = json.dumps(forum_result)
            channel.basic_publish(
                exchange=exchangename,
                routing_key="forum.error",
                body=error_message,
                properties=pika.BasicProperties(delivery_mode=2),
            )
            # Return error message
            return (
                jsonify(
                    {
                        "code": 500,
                        "message": "Forum microservice failed to retrieve forum.",
                    }
                ),
                500,
            )

        # Return forum result
        return jsonify(forum_result), forum_result["code"]

    except Exception as e:
        # Unexpected error in code
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
                {"code": 500, "message": "forum_complex.py internal error: " + ex_str}
            ),
            500,
        )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5300, debug=True)
