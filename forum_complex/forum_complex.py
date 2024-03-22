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


@app.route("/api/v1/get_bookings", methods=["POST"])
def get_forum():
    # Simple check of input format and data of the request are JSON
    if request.is_json:
        try:
            booking = request.get_json()
            print("\nReceived an order in JSON:", booking)

            # do the actual work
            # 1. Send order info {cart items}
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
                    {"code": 500, "message": "forum_complex.py internal error: " + ex_str}
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


def processGetForum(order):
    # 2. Send the order info {cart items}
    # Invoke the order microservice

    print("\n-----Invoking order microservice-----")
    order_result = invoke_http(order_URL, method="POST", json=order)
    print("order_result:", order_result)

    # Check the order result; if a failure, send it to the error microservice.
    code = order_result["code"]
    message = json.dumps(order_result)

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
            "\nOrder status ({:d}) published to the RabbitMQ Exchange:".format(code),
            order_result,
        )

        # 7. Return error
        return {
            "code": 500,
            "data": {"order_result": order_result},
            "message": "Order creation failure sent for error handling.",
        }

    # Notice that we are publishing to "Activity Log" only when there is no error in order creation.
    # In http version, we first invoked "Activity Log" and then checked for error.
    # Since the "Activity Log" binds to the queue using '#' => any routing_key would be matched
    # and a message sent to “Error” queue can be received by “Activity Log” too.

    else:
        # 4. Record new order
        # record the activity log anyway
        # print('\n\n-----Invoking activity_log microservice-----')
        print(
            "\n\n-----Publishing the (order info) message with routing_key=order.info-----"
        )

        # invoke_http(activity_log_URL, method="POST", json=order_result)
        channel.basic_publish(
            exchange=exchangename, routing_key="order.info", body=message
        )

    print("\nOrder published to RabbitMQ Exchange.\n")
    # - reply from the invocation is not used;
    # continue even if this invocation fails

    # 5. Send new order to shipping
    # Invoke the shipping record microservice
    print("\n\n-----Invoking shipping_record microservice-----")

    shipping_result = invoke_http(
        shipping_record_URL, method="POST", json=order_result["data"]
    )
    print("shipping_result:", shipping_result, "\n")

    # Check the shipping result;
    # if a failure, send it to the error microservice.
    code = shipping_result["code"]
    if code not in range(200, 300):
        # Inform the error microservice
        # print('\n\n-----Invoking error microservice as shipping fails-----')
        print(
            "\n\n-----Publishing the (shipping error) message with routing_key=shipping.error-----"
        )

        # invoke_http(error_URL, method="POST", json=shipping_result)
        message = json.dumps(shipping_result)
        channel.basic_publish(
            exchange=exchangename,
            routing_key="shipping.error",
            body=message,
            properties=pika.BasicProperties(delivery_mode=2),
        )

        print(
            "\nShipping status ({:d}) published to the RabbitMQ Exchange:".format(code),
            shipping_result,
        )

        # 7. Return error
        return {
            "code": 400,
            "data": {"order_result": order_result, "shipping_result": shipping_result},
            "message": "Simulated shipping record error sent for error handling.",
        }

    # 7. Return created order, shipping record
    return {
        "code": 201,
        "data": {"order_result": order_result, "shipping_result": shipping_result},
    }


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5011, debug=True)
