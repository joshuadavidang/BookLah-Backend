from flask import Flask, request, jsonify
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os
import stripe
import json

load_dotenv()
app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URI")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_recycle": 299}

PORT = 5006
db = SQLAlchemy(app)

CORS(app, supports_credentials=True)
app.config["STRIPE_PUBLIC_KEY"] = os.getenv("STRIPE_PUBLIC_KEY")
app.config["STRIPE_SECRET_KEY"] = os.getenv("STRIPE_SECRET_KEY")
stripe.api_key = app.config["STRIPE_SECRET_KEY"]
FRONT_END_DOMAIN = "http://localhost:3000"


class PaymentIntent(db.Model):
    __tablename__ = "payment_intent"
    payment_intent = db.Column(db.String(100), primary_key=True)
    concert_id = db.Column(db.String(100), nullable=False)
    payment_status = db.Column(db.String(100), nullable=False)

    def json(self):
        return {
            "payment_intent": self.payment_intent,
            "concert_id": self.concert_id,
            "payment_status": self.payment_status,
        }


@app.route("/api/v1/config")
def get_config():
    return jsonify({"code": 200, "publishable_key": os.getenv("STRIPE_PUBLIC_KEY")})


## GET CUSTOMER DATA FROM STRIPE AFTER PAYMENT IS SUCCESSFUL
@app.route("/api/v1/getCustomerData", methods=["POST"])
def getCustomerInfo():
    client_secret = request.get_json().get("client_secret")
    data = stripe.PaymentIntent.retrieve(client_secret)
    return jsonify({"code": 200, "data": data})


## FRONTEND TO CALL
@app.route("/api/v1/create_payment_intent", methods=["POST"])
def create_payment_intent():

    concert_id = request.json.get("concert_id", None)
    price = request.json.get("price", None)

    try:

        payment = stripe.PaymentIntent.create(amount=price * 100, currency="sgd")

        result = add_payment_intent(payment["id"], concert_id, payment["status"])
        print(payment["status"])

        if result:
            return jsonify(
                {
                    "code": 201,
                    "payment_intent": payment["id"],
                    "client_secret": payment.client_secret,
                }
            )

        else:
            return jsonify({"code": 404, "payment_intent": payment["id"]})

    except stripe.error.StripeError as e:
        return jsonify({"error": {"message": str(e)}}), 400
    except Exception as e:
        return jsonify({"error": {"message": str(e)}}), 500


## PAYMENT INTENT DB
@app.route(
    "/api/v1/add_payment_intent",
    methods=["POST"],
)
def add_payment_intent(payment_intent, concert_id, payment_status):
    if db.session.scalars(
        db.select(PaymentIntent).filter_by(payment_intent=payment_intent).limit(1)
    ).first():
        return jsonify(
            {
                "code": 400,
                "data": {"payment_intent": payment_intent},
                "message": "Payment Intent already exist.",
            }
        )

    payment_intent_db = PaymentIntent(
        payment_intent=payment_intent,
        concert_id=concert_id,
        payment_status=payment_status,
    )

    try:
        db.session.add(payment_intent_db)
        db.session.commit()
    except:
        return jsonify(
            {
                "code": 500,
                "data": {
                    "payment_intent": payment_intent,
                    "concert_id": concert_id,
                    "payment_status": payment_status,
                },
                "message": "An error occurred adding the Payment Intent.",
            }
        )

    return jsonify(
        {
            "code": 201,
            "data": payment_intent_db.json(),
            "message": "Payment Intent have been added successfully",
        }
    )


## WEBHOOK
@app.route("/webhook", methods=["POST"])
def webhook_recieved():
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    request_data = json.loads(request.data)

    if webhook_secret:
        event = None
        payload = request.data
        sig_header = request.headers["STRIPE_SIGNATURE"]

        try:
            event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)

        except ValueError as e:
            raise e
        except stripe.error.SignatureVerificationError as e:
            raise e

        data = event["data"]
        event_type = event["type"]

    else:
        data = request_data["data"]
        event_type = request_data["type"]

    data_obj = data["object"]

    if event_type == "payment_intent.succeeded":
        payment_intent = data_obj["id"]
        result = update_payment_intent(payment_intent)

        if result["code"] not in range(200, 300):
            return jsonify({"update_result": result})

    else:
        print("Unhandled event type {}".format(event["type"]))

    return jsonify({"status": "success"})


### FOR WEBHOOK TO CALL WHEN PAYMENT STATUS CHANGE FROM CREATED TO SUCCEEDED
@app.route(
    "/api/v1/update_payment_intent/<string:payment_intent>",
    methods=["PUT"],
)
def update_payment_intent(payment_intent):
    pi = (
        db.session.query(PaymentIntent).filter_by(payment_intent=payment_intent).first()
    )
    if not pi:
        return jsonify(
            {
                "code": 404,
                "data": {"payment_intent": payment_intent},
                "message": "Payment Intent not found.",
            }
        )

    payment_intent_obj = stripe.PaymentIntent.retrieve(payment_intent)

    try:
        db.session.query(PaymentIntent).filter_by(payment_intent=payment_intent).update(
            {"payment_status": payment_intent_obj.status}
        )
        db.session.commit()
        return jsonify(
            {
                "code": 200,
                "data": {"payment_intent": payment_intent},
                "message": "Updated payment status successfully.",
            }
        )
    except:
        return jsonify(
            {
                "code": 500,
                "data": {"payment_intent": payment_intent},
                "message": "An error occurred while updating the payment status",
            }
        )


@app.route(
    "/api/v1/get_payment_intents",
    methods=["GET"],
)
def get_payment_intents():
    pi_list = db.session.scalars(db.select(PaymentIntent)).all()
    if len(pi_list):
        return {
            "code": 200,
            "data": {"payment_intent": [pi.json() for pi in pi_list]},
        }
    return {"code": 404, "message": "There are no payment intents."}


## REFUND
@app.route("/api/v1/refund/<string:concert_id>", methods=["POST"])
def refund(concert_id):

    result = get_payment_intent(concert_id)

    if result["code"] not in range(200, 300):
        return jsonify(
            {
                "code": 400,
                "message": result["message"],
            }
        )

    pi_list = result["data"]["payment_intent"]
    print(pi_list)
    for pi in pi_list:
        payment_intent = pi["payment_intent"]
        refund = stripe.Refund.create(payment_intent=payment_intent)

        if not refund:
            return jsonify(
                {
                    "code": 500,
                    "data": {"payment_intent": pi},
                    "message": "An error occurred when processing refund.",
                }
            )

    return jsonify(
        {
            "code": 201,
            "data": pi_list.json(),
            "message": "Refund successful",
        }
    )


def get_payment_intent(concert_id):
    payment_intent = db.session.scalars(
        db.select(PaymentIntent).filter_by(
            concert_id=concert_id, payment_status="payment_intent.succeeded"
        )
    ).all()

    if len(payment_intent):
        return {
            "code": 200,
            "data": {"payment_intent": [pi.json() for pi in payment_intent]},
        }

    return {"code": 404, "message": "There are no payment intents."}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5006, debug=True)
