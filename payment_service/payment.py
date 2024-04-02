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


class StripeIds(db.Model):
    __tablename__ = "payment"
    concert_id = db.Column(db.String(100), primary_key=True)
    category = db.Column(db.String(100), primary_key=True)
    concert_name = db.Column(db.String(100), nullable=False)
    price_id = db.Column(db.String(100), nullable=False)
    product_id = db.Column(db.String(100), nullable=False)

    def json(self):
        return {
            "concert_id": self.concert_id,
            "category": self.category,
            "concert_name": self.concert_name,
            "price_id": self.price_id,
            "product_id": self.product_id,
        }


class PaymentIntent(db.Model):
    __tablename__ = "payment_intent"
    payment_intent = db.Column(db.String(100), primary_key=True)
    concert_id = db.Column(db.String(100), nullable=False)

    def json(self):
        return {
            "payment_intent": self.payment_intent,
            "concert_id": self.concert_id,
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


## COMPLEX 1
@app.route("/api/v1/create_payment_intent", methods=["POST"])
def create_payment_intent():

    # concert_id = request.json.get("concert_id", None)
    # category = request.json.get("category", None)
    email = request.json.get("email", None)
    price = request.json.get("price", None)

    # stripeids = get_stripeids(concert_id, category)["data"]

    try:

        payment = stripe.PaymentIntent.create(
            amount=price * 100, currency="sgd", receipt_email=email
        )

        return jsonify({"client_secret": payment.client_secret})
    except stripe.error.StripeError as e:
        return jsonify({"error": {"message": e.user_message}}), 400
    except Exception as e:
        return jsonify({"error": {"message": e.user_message}}), 500


## PAYMENT INTENT DB
def add_payment_intent(payment_intent, concert_id):
    if db.session.scalars(
        db.select(PaymentIntent).filter_by(payment_intent=payment_intent).limit(1)
    ).first():
        return (
            jsonify(
                {
                    "code": 400,
                    "data": {"payment_intent": payment_intent},
                    "message": "Payment Intent already exist.",
                }
            ),
            400,
        )

    payment_intent_db = PaymentIntent(
        payment_intent=payment_intent, concert_id=concert_id
    )

    try:
        db.session.add(payment_intent_db)
        db.session.commit()
    except:
        return (
            jsonify(
                {
                    "code": 500,
                    "data": {
                        "payment_intent": payment_intent,
                        "concert_id": concert_id,
                    },
                    "message": "An error occurred adding the Payment Intent.",
                }
            ),
            500,
        )

    return (
        jsonify(
            {
                "code": 201,
                "data": payment_intent_db.json(),
                "message": "Payment Intent have been added successfully",
            }
        ),
        201,
    )


## WEBHOOK
@app.route("/webhook", methods=["POST"])
def webhook_recieved():
    # webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    webhook_secret = (
        "whsec_e3851f59862b600aa6e9b2230e2b8b09cc2735e1469bcf09fe66bc47a575d48b"
    )
    request_data = json.loads(request.data)

    if webhook_secret:
        # signature = request.headers.get("stripe-signature")
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
        # client_secret = payment_intent['client_secret']
        # concert_id = request.json.get("concert_id", None)
        concert_id = "fcbeba79-7bfe-4648-83d8-552ba91c274f"
        add_payment_intent(payment_intent, concert_id)
        # print(payment_intent)
    else:
        print("Unhandled event type {}".format(event["type"]))

    return jsonify({"status": "success"})


## PAYMENT INTENT DB
@app.route(
    "/api/v1/add_payment_intent/<string:payment_intent>/<string:concert_id>",
    methods=["POST"],
)
def add_payment_intent(payment_intent, concert_id):
    if db.session.scalars(
        db.select(PaymentIntent).filter_by(payment_intent=payment_intent).limit(1)
    ).first():
        return (
            jsonify(
                {
                    "code": 400,
                    "data": {"payment_intent": payment_intent},
                    "message": "Payment Intent already exist.",
                }
            ),
            400,
        )

    payment_intent_db = PaymentIntent(
        payment_intent=payment_intent, concert_id=concert_id
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


## ADMIN
# create stripe ids from Stripe
def create_stripeids(product_name, price):

    price = stripe.Price.create(
        currency="sgd",
        unit_amount=price * 100,  # in cents
        product_data={"name": product_name},
    )

    return {
        "code": 201,
        "data": {"price_id": price["id"], "product_id": price["product"]},
        "message": "Stripe IDs created successfully",
    }


## REFUND
@app.route("/api/v1/refund/<string:concert_id>", methods=["POST"])
def refund(concert_id):
    pi_list = get_payment_intent(concert_id)["data"]["payment_intent"]

    for pi in pi_list:
        refund = stripe.Refund.create(payment_intent=pi)

        if not refund:
            return (
                jsonify(
                    {
                        "code": 500,
                        "data": {"payment_intent": pi},
                        "message": "An error occurred when processing refund.",
                    }
                ),
                500,
            )

    return (
        jsonify(
            {
                "code": 201,
                "data": pi_list.json(),
                "message": "Refund successful",
            }
        ),
        201,
    )


def get_payment_intent(concert_id):

    payment_intent = db.session.scalars(
        db.select(PaymentIntent).filter_by(concert_id=concert_id)
    ).all()

    if len(payment_intent):
        return jsonify(
            {
                "code": 200,
                "data": {"payment_intent": [pi.json() for pi in payment_intent]},
            }
        )
    return jsonify({"code": 404, "message": "There are no payment intents."})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5006, debug=True)
