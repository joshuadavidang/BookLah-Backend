from flask import Flask, request, jsonify
from flask_cors import CORS
import os, sys
from dotenv import load_dotenv
from invokes import invoke_http
import amqp_connection
import pika
import json


app = Flask(__name__)
CORS(app, supports_credentials=True)
PORT = 5300

load_dotenv()


booking_URL = "http://booking_service:5001/api/v1/get_user_bookings/"
forum_URL = "http://forum_service:5007/api/v1/getForum/"
GET_CONCERT_STATUS = "http://concert_service:5002/api/v1/getConcertStatus"

exchangename = "forum_topic"
exchangetype = "topic"
connection = amqp_connection.create_connection()
channel = connection.channel()

if not amqp_connection.check_exchange(channel, exchangename, exchangetype):
    print(
        "\nCreate the 'Exchange' before running this microservice. \nExiting the program."
    )
    sys.exit(0)


@app.route("/api/v1/get_forum", methods=["POST"])
def get_forum():
    if request.is_json:
        try:
            booking = request.get_json()
            print("\nReceived an order in JSON:", booking)

            result = processGetForum(booking)
            print("\n------------------------")
            print("\nresult: ", result)
            return result

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

            return jsonify(
                {
                    "code": 500,
                    "message": "forum_complex.py internal error: " + ex_str,
                }
            )

    return (
        jsonify(
            {"code": 400, "message": "Invalid JSON input: " + str(request.get_data())}
        ),
        400,
    )


def processGetForum(booking):
    try:
        print("\n-----Invoking booking microservice to get userid-----")
        user_id = booking["user_id"]
        print(booking_URL + user_id)
        booking_result = invoke_http(booking_URL + user_id, method="GET", json=booking)
        filtered_booking_result = [
            booking
            for booking in booking_result["data"]["bookings"]
            if booking["forum_joined"] == True
        ]
        print("filtered_booking_result:", filtered_booking_result)

        booking_code = booking_result["code"]
        if booking_code not in range(200, 300):
            error_message = json.dumps(booking_result)
            channel.basic_publish(
                exchange=exchangename,
                routing_key="booking.error",
                body=error_message,
                properties=pika.BasicProperties(delivery_mode=2),
            )
            return (
                jsonify(
                    {
                        "code": 500,
                        "message": "Booking microservice failed to retrieve concert ID.",
                    }
                ),
            )
        else:
            print(
                "\n\n-----Publishing the (booking info) message with routing_key=forum.info-----"
            )
            channel.basic_publish(
                exchange=exchangename,
                routing_key="forum.info",
                body="Bookings obtained succesfully",
            )

        if len(filtered_booking_result) == 0:
            return (
                jsonify(
                    {
                        "code": 200,
                        "message": "User has not joined any forums.",
                    }
                ),
                200,
            )

        print("\n-----Invoking forum microservice to get forum-----")
        forum_result = invoke_http(forum_URL + user_id, method="GET")
        print("forum_result", forum_result)

        forum_code = forum_result["code"]
        if forum_code not in range(200, 300):
            error_message = json.dumps(forum_result)
            channel.basic_publish(
                exchange=exchangename,
                routing_key="forum.error",
                body=error_message,
                properties=pika.BasicProperties(delivery_mode=2),
            )
            return (
                jsonify(
                    {
                        "code": 500,
                        "message": "Forum microservice failed to retrieve forum.",
                    }
                ),
                500,
            )

        else:
            print(
                "\n\n-----Publishing the (booking info) message with routing_key=forum.info-----"
            )
            channel.basic_publish(
                exchange=exchangename,
                routing_key="forum.info",
                body="forums obtained successfully",
            )

        print(
            "\n-----Invoking concert microservice to get concert status. only return those available concerts-----"
        )

        available_forum = []
        for forum in forum_result["data"]:
            concert_id = forum["concert_id"]
            GET_CONCERT_STATUS_API = f"{GET_CONCERT_STATUS}/{concert_id}"
            concert_result = invoke_http(GET_CONCERT_STATUS_API, method="GET")
            if concert_result["data"]["concert_status"] == "AVAILABLE":
                available_forum.append(forum)

        if len(available_forum) == 0:
            return (
                jsonify(
                    {
                        "code": 400,
                        "message": "No available forums.",
                    }
                ),
                400,
            )

        print("###### Forums Retrieved Successful ######\n")

        return jsonify(
            {
                "code": 200,
                "data": available_forum,
                "message": "Forums retrieved successfully.",
            }
        )

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
                {"code": 500, "message": "forum_complex.py internal error: " + ex_str}
            ),
            500,
        )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=True)
