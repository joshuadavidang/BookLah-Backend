from flask import Flask, request, jsonify
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from sqlalchemy.dialects.postgresql import UUID
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
    concert_id = db.Column(UUID(as_uuid=True), nullable=False)

    def json(self):
        return {
            "payment_intent": self.payment_intent,
            "concert_id": self.concert_id,
        }


@app.route("/api/v1/config")
def get_config():
    return jsonify({"code": 200, "publishable_key": os.getenv("STRIPE_PUBLIC_KEY")})


##STRIPE IDS
@app.route("/payment/get_stripeids/<string:concert_id>/<string:category>")
def get_stripeids(concert_id, category):

    # return (concert_id, type(concert_id))
    # concert_id_uuid = UUID(str(concert_id))

    stripe_ids = db.session.scalars(
        db.select(StripeIds)
        .filter_by(concert_id=concert_id, category=category)
        .limit(1)
    ).first()

    if stripe_ids:
        return jsonify({"code": 200, "data": stripe_ids.json()})

    return jsonify(
        {
            "code": 404,
            "data": {"concert_id": concert_id, "category": category},
            "message": "Stripe IDs not found.",
        }
    )


## GET EMAIL
@app.route("/api/v1/getCustomerEmail", methods=["POST"])
def getCustomerInfo():
    session_id = request.get_json().get("sessionId")
    checkout_session = stripe.checkout.Session.retrieve(session_id)
    email = checkout_session.customer_details.email
    return jsonify({"code": 200, "email": email})


## COMPLEX 1
@app.route("/api/v1/create_payment_intent", methods=["GET"])
def create_payment_intent():

    # concert_id = request.json.get("concert_id", None)
    # category = request.json.get("category", None)
    # price = request.json.get("price", None)

    price = 1000
    # stripeids = get_stripeids(concert_id, category)["data"]

    try:

        payment = stripe.PaymentIntent.create(
            amount=price * 100,
            currency="sgd",
        )

        return jsonify({"client_secret": payment.client_secret})
    except stripe.error.StripeError as e:
        return jsonify({"error": {"message": e.user_message}}), 400
    except Exception as e:
        return jsonify({"error": {"message": e.user_message}}), 500


@app.route("/api/v1/processPayment", methods=["POST"])
def create_session():
    data = request.get_json()
    concert_id = data["concert_id"]
    category = data["category"]
    quantity = data["quantity"]

    stripeids = get_stripeids(concert_id, category).json

    try:
        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    "price": stripeids["data"]["price_id"],
                    "quantity": quantity,
                },
            ],
            mode="payment",
            invoice_creation={"enabled": True},
            success_url=FRONT_END_DOMAIN + "/success?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=FRONT_END_DOMAIN + "/error",
        )

    except Exception as e:
        return str(e)

    return jsonify({"checkout_url": checkout_session.url})


## WEBHOOK
@app.route("/webhook", methods=["POST"])
def webhook_recieved():
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    request_data = json.loads(request.data)

    if webhook_secret:
        signature = request.headers.get("stripe-signature")
        try:
            event = stripe.Webhook.construct_event(
                payload=request_data, sig_header=signature, secret=webhook_secret
            )

            data = event["data"]

        except Exception as e:
            raise e
        event_type = event["type"]

    else:
        data = request_data["data"]
        event_type = request_data["type"]

    data_obj = data["object"]

    if event_type == "payment_intent.succeeded":
        payment_intent = data_obj
        # client_secret = payment_intent['client_secret']
        concert_id = request.json.get("concert_id", None)
        add_payment_intent(payment_intent, concert_id)
        print("Payment received!")

    return jsonify({"status": "success"})


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


# add Stripe IDs to database
@app.route(
    "/api/v1/add_stripeids/<string:concert_id>/<string:category>", methods=["POST"]
)
def add_stripeids(concert_id, category):
    if db.session.scalars(
        db.select(StripeIds)
        .filter_by(concert_id=concert_id, category=category)
        .limit(1)
    ).first():
        return (
            jsonify(
                {
                    "code": 400,
                    "data": {"concert_id": concert_id, "category": category},
                    "message": "Stripe IDs already exist.",
                }
            ),
            400,
        )

    data = request.get_json()
    concert_name = data["name"]
    price = data["price"]

    stripeids = create_stripeids(concert_name, price)

    stripeids_db = StripeIds(
        concert_id=concert_id,
        category=category,
        concert_name=concert_name,
        price_id=stripeids["data"]["price_id"],
        product_id=stripeids["data"]["product_id"],
    )

    try:
        db.session.add(stripeids_db)
        db.session.commit()
    except:
        return (
            jsonify(
                {
                    "code": 500,
                    "data": {"concert_id": concert_id, "category": category},
                    "message": "An error occurred adding the Stripe IDs.",
                }
            ),
            500,
        )

    return (
        jsonify(
            {
                "code": 201,
                "data": stripeids_db.json(),
                "message": "Stripe IDs have been added successfully",
            }
        ),
        201,
    )


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
    return jsonify({"code": 404, "message": "There are no payment intents."}), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=True)
