from flask import Flask, request, jsonify
from flask_cors import CORS
import os, sys
from invokes import invoke_http
import amqp_connection
import pika
import json


### Get Forum Complex Microservice 3
# Booking microservice - Retrieve list of users who booked the concert
# Concert microservice - Retrieve list of available concerts, status != CANCELLED
# Forum microservice - Retrieve list of forums that user has joined
###


app = Flask(__name__)
CORS(app, supports_credentials=True)
PORT = 5300


booking_URL = "http://booking_service:5001/api/v1/get_user_bookings/"
forum_URL = "http://forum_service:5007/api/v1/getUserForums"
GET_CONCERT_STATUS = "http://concert_service:5002/api/v1/getAvailableConcerts"


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
            forum = request.get_json()
            print("\nReceived an request to populate forum in JSON:", forum)

            result = processGetForum(forum)
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


def processGetForum(forum):
    print("\n-----Invoking booking microservice to get userid-----")
    user_id = forum["user_id"]
    print(booking_URL + user_id)
    booking_result = invoke_http(booking_URL + user_id, method="GET", json=forum)
    booking_code = booking_result["code"]
    message = json.dumps(booking_result)

    if booking_code not in range(200, 300):
        channel.basic_publish(
            exchange=exchangename,
            routing_key="booking.error",
            body=message,
            properties=pika.BasicProperties(delivery_mode=2),
        )
        return jsonify(
            {
                "code": 500,
                "message": "Booking microservice failed to retrieve concert ID by users.",
            }
        )
    else:
        print(
            "\n\n-----Publishing the (booking info) message with routing_key=forum.info-----"
        )
        channel.basic_publish(
            exchange=exchangename,
            routing_key="booking.info",
            body=message,
        )

    filtered_booking_result = [
        booking
        for booking in booking_result["data"]["bookings"]
        if booking["forum_joined"] == True
    ]
    print("filtered_booking_result:", filtered_booking_result)

    if len(filtered_booking_result) == 0:
        return jsonify({"code": 400, "message": "User has not joined any forums."})

    print(
        "\n-----Invoking concert microservice to get concert status. only return those available concerts-----"
    )

    print(filtered_booking_result)
    concert_arr = []
    for booking_obj in filtered_booking_result:
        concert = booking_obj["concert_id"]
        concert_arr.append(concert)

    print(concert_arr)

    data = {
        "concerts": concert_arr,
    }

    concert_result = invoke_http(GET_CONCERT_STATUS, method="POST", json=data)

    code = concert_result["code"]
    message = json.dumps(concert_result)

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
            "\nConcert status ({:d}) published to the RabbitMQ Exchange:".format(code),
            concert_result,
        )

        return {
            "code": 500,
            "data": {"concert_result": concert_result},
            "message": "Failure to get available concerts sent for error handling.",
        }

    else:
        print(
            "\n\n-----Publishing the (concert info) message with routing_key= concert.info-----"
        )

        channel.basic_publish(
            exchange=exchangename, routing_key="concert.info", body=message
        )

    if len(concert_result) == 0:
        return jsonify(
            {
                "code": 400,
                "message": "No available forums.",
            }
        )

    print("\n-----Invoking forum microservice to get forum that user has joined-----")

    forum_result = invoke_http(forum_URL, method="POST", json=concert_result["data"])
    print("forum_result", forum_result)

    message = json.dumps(forum_result)
    forum_code = forum_result["code"]

    if forum_code not in range(200, 300):
        channel.basic_publish(
            exchange=exchangename,
            routing_key="forum.error",
            body=message,
            properties=pika.BasicProperties(delivery_mode=2),
        )
        return jsonify(
            {
                "code": 500,
                "message": "Forum microservice failed to retrieve forum.",
            }
        )

    else:
        print(
            "\n\n-----Publishing the (forum info) message with routing_key=forum.info-----"
        )
        channel.basic_publish(
            exchange=exchangename,
            routing_key="forum.info",
            body=message,
        )

    print("###### Forums Retrieved Successful ######\n")

    return jsonify(
        {
            "code": 200,
            "data": forum_result,
            "message": "Forums retrieved successfully.",
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=True)
