from flask import Flask, request, jsonify
from flask_cors import CORS
import os, sys
from os import environ
from dotenv import load_dotenv
from invokes import invoke_http
import pika
import json
import amqp_connection

load_dotenv()

app = Flask(__name__)
CORS(app, supports_credentials=True)
PORT = 5400

concert_URL = "http://concert_service:5002/api/v1/addConcert/"
stripe_URL = "http://payment_service:5006/api/v1/add_stripeids/"
forum_URL = "http://forum_service:5007/api/v1/addForum"
activity_log_URL = "http://activity_log_service:5004/api/v1/activity_log"
error_URL = "http://error_service:5005/api/v1/error"


exchangename = "concert_topic"
exchangetype = "topic"
connection = amqp_connection.create_connection()
channel = connection.channel()

if not amqp_connection.check_exchange(channel, exchangename, exchangetype):
    print(
        "\nCreate the 'Exchange' before running this microservice. \nExiting the program."
    )
    sys.exit(0)


@app.route("/api/v1/create_concert", methods=["POST"])
def create_concert():
    if request.is_json:
        try:
            concert = request.get_json()
            print("\nReceived a concert creation in JSON:", concert)
            result = processCreateConcert(concert)

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
                        "message": "create_concert.py internal error: " + ex_str,
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


def processCreateConcert(concert):
    print("\n-----Invoking concert microservice-----")
    concert_id = concert["concert_id"]
    data = {
        "performer": concert["performer"],
        "title": concert["title"],
        "venue": concert["venue"],
        "date": concert["date"],
        "time": concert["time"],
        "capacity": concert["capacity"],
        "price": concert["price"],
        "description": concert["description"],
        "created_by": concert["created_by"],
        "concert_status": "AVAILABLE",
    }
    concert_result = invoke_http(concert_URL + concert_id, method="POST", json=data)
    print(concert_result)
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
            "Concert status ({:d}) published to the localhost Exchange:".format(code),
            concert_result,
        )

        return {
            "code": 500,
            "data": {"booking_result": concert_result},
            "message": "Concert creation failure sent for error handling.",
        }

    else:
        print(
            "\n\n-----Publishing the (concert info) message with routing_key=concert.info-----"
        )
        channel.basic_publish(
            exchange=exchangename, routing_key="concert.info", body=message
        )

    print("\Concert published to localhost Exchange.\n")

    print("\n-----Invoking payment microservice (stripe)-----")
    product_data = {"name": concert["title"], "price": concert["price"]}
    stripe_result = invoke_http(
        stripe_URL + concert_id + "/category1", method="POST", json=product_data
    )
    print(stripe_result)
    code = stripe_result["code"]
    message = json.dumps(stripe_result)

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
            "Stripe result status ({:d}) published to the localhost Exchange:".format(
                code
            ),
            stripe_result,
        )

        return {
            "code": 500,
            "data": {"stripe_result": stripe_result},
            "message": "Add product to stripe failure sent for error handling.",
        }

    else:
        print(
            "\n\n-----Publishing the (concert info) message with routing_key=concert.info-----"
        )
        channel.basic_publish(
            exchange=exchangename, routing_key="concert.info", body=message
        )

    print("\n-----Invoking forum microservice-----")
    forum_data = {
        "concert_id": concert["concert_id"],
        "concert_name": concert["title"],
        "user_id": concert["created_by"],
    }

    forum_result = invoke_http(forum_URL, method="POST", json=forum_data)
    print(forum_result)
    code = forum_result["code"]
    message = json.dumps(forum_result)

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
            "Forum result status ({:d}) published to the localhost Exchange:".format(
                code
            ),
            stripe_result,
        )

        return {
            "code": 500,
            "data": {"forum_result": forum_result},
            "message": "Add forum failure sent for error handling.",
        }

    else:
        print(
            "\n\n-----Publishing the (concert info) message with routing_key=concert.info-----"
        )
        channel.basic_publish(
            exchange=exchangename, routing_key="concert.info", body=message
        )

    print("###### Concert Creation Successful ######\n")

    return {
        "code": 201,
        "data": {
            "concert_result": concert_result,
        },
    }


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=True)
