from flask import Flask, request, jsonify
from flask_cors import CORS

import os, sys

import requests
from invokes import invoke_http

app = Flask(__name__)
CORS(app)

event_URL = "http://localhost:5000/getConcerts"
booking_URL = "http://localhost:5001/order"
payment_URL = "http://localhost:5002/create-checkout-session"
notification_URL = "http://localhost:5003/notification"
tracking_URL = "http://localhost:5004/tracking"
activity_log_URL = "http://localhost:5005/activity_log"
error_URL = "http://localhost:5006/error"


@app.route("/book_concert", methods=['POST'])
def book_concert():
    # Simple check of input format and data of the request are JSON
    if request.is_json:
        try:
            booking = request.get_json()
            print("\nReceived an order in JSON:", booking)

            # do the actual work
            # 1. Send order info {cart items}
            result = processBookConcert(booking)
            return jsonify(result), result["code"]

        except Exception as e:
            # Unexpected error in code
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            ex_str = str(e) + " at " + str(exc_type) + ": " + fname + ": line " + str(exc_tb.tb_lineno)
            print(ex_str)

            return jsonify({
                "code": 500,
                "message": "book_concert.py internal error: " + ex_str
            }), 500

    # if reached here, not a JSON request.
    return jsonify({
        "code": 400,
        "message": "Invalid JSON input: " + str(request.get_data())
    }), 400


def processBookConcert(booking):
    # 2. Send the order info {cart items}
    # Invoke the booking microservice
    print('\n-----Invoking booking microservice-----')
    booking_result = invoke_http(booking_URL, method='POST', json=booking)
    print("booking result :", booking_result)


    # 4. Record new order
    # record the activity log anyway
    print('\n\n-----Invoking activity_log microservice-----')
    invoke_http(activity_log_URL, method="POST", json=booking_result)
    print("\nOrder sent to activity log.\n")
    # - reply from the invocation is not used;
    # continue even if this invocation fails

    # Check the order result; if a failure, send it to the error microservice.
    code = booking_result["code"]
    if code not in range(200, 300):
        # Inform the error microservice
        print('\n\n-----Invoking error microservice as booking fails-----')
        invoke_http(error_URL, method="POST", json=booking_result)
        # - reply from the invocation is not used; 
        # continue even if this invocation fails
        print("Order status ({:d}) sent to the error microservice:".format(code), booking_result)

        # 7. Return error
        return {
            "code": 500,
            "data": {"booking_result": booking_result},
            "message": "Booking creation failure sent for error handling."
        }


    print('\n\n-----Invoking payment microservice-----')
    payment_result = invoke_http(payment_URL, method="POST", json=booking_result['data'])
    print("payment_result:", payment_result, '\n')

    code = payment_result["code"]
    if code not in range(200, 300):
        # Inform the error microservice
        print('\n\n-----Invoking error microservice as payment fails-----')
        invoke_http(error_URL, method="POST", json=payment_result)
        # - reply from the invocation is not used; 
        # continue even if this invocation fails
        print("Order status ({:d}) sent to the error microservice:".format(code), payment_result)

        return {
            "code": 500,
            "data": {"booking_result": booking_result,
                     "payment_result": payment_result},
            "message": "Simulated payment error sent for error handling."
        }
    
    
    print('\n\n-----Invoking notification microservice-----')
    notification_result = invoke_http(notification_URL, method="POST", json=booking_result['data'])
    print("notification_result:", notification_result, '\n')

    code = notification_result["code"]
    if code not in range(200, 300):
        # Inform the error microservice
        print('\n\n-----Invoking error microservice as notification fails-----')
        invoke_http(error_URL, method="POST", json=notification_result)
        # - reply from the invocation is not used; 
        # continue even if this invocation fails
        print("Order status ({:d}) sent to the error microservice:".format(code), notification_result)

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
        # Inform the error microservice
        print('\n\n-----Invoking error microservice as tracking fails-----')
        invoke_http(error_URL, method="POST", json=tracking_result)
        # - reply from the invocation is not used; 
        # continue even if this invocation fails
        print("Order status ({:d}) sent to the error microservice:".format(code), tracking_result)

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
    