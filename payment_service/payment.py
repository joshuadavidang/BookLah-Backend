from flask import Flask, redirect, request, jsonify
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from sqlalchemy.dialects.postgresql import UUID
import os
import stripe

load_dotenv()

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = (
    "mysql+mysqlconnector://root:root@localhost:8889/esd_proj"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_recycle": 299}

db = SQLAlchemy(app)

CORS(app)
app.config["STRIPE_PUBLIC_KEY"] = os.getenv("STRIPE_PUBLIC_KEY")
app.config["STRIPE_SECRET_KEY"] = os.getenv("STRIPE_SECRET_KEY")
stripe.api_key = app.config["STRIPE_SECRET_KEY"]
FRONT_END_DOMAIN = "http://localhost:3000"


class StripeIds(db.Model):
    __tablename__ = "payment"
    concert_id = db.Column(UUID(as_uuid=True), primary_key=True)
    category = db.Column(db.String(100), primary_key=True)
    concert_name = db.Column(db.String(100), nullable=False)
    price_id = db.Column(db.String(100), nullable=False)
    product_id = db.Column(db.String(100), nullable=False)

    # __table_args__ = (
    #         {"extend_existing": True},  # Extend existing table args
    #         {"primary_key": (concert_id, category)}  # Define composite primary key
    #     )
    
    def json(self):
        return {
            "concert_id": self.concert_id,
            "category": self.category,
            "concert_name": self.concert_name,
            "price_id": self.price_id,
            "product_id": self.product_id,
        }


@app.route("/payment/get_stripeids/<uuid:concert_id>/<string:category>")
def get_stripeids(concert_id, category):
    stripe_ids = db.session.scalars(
            db.select(StripeIds).filter_by(concert_id=concert_id, category=category).
            limit(1)
    ).first()

    if stripe_ids:
        return jsonify({"code": 200, "data": stripe_ids.json()})
    return (
        jsonify(
            {
                "code": 404,
                "data": {"concert_id": concert_id, "category": category},
                "message": "Stripe IDs not found.",
            }
        ),
        404,
    )

@app.route("/api/v1/getCustomerEmail", methods=["POST"])
def getCustomerInfo():
    session_id = request.get_json().get("sessionId")
    checkout_session = stripe.checkout.Session.retrieve(session_id)
    email = checkout_session.customer_details.email
    return jsonify({"code": 200, "email": email})

@app.route("/api/v1/processPayment", methods=["POST"])
def create_session():

    concert_id = request.json.get("concert_id", None)
    category = request.json.get("category", None)
    quantity = request.json.get("quantity", None)

    stripeids = get_stripeids(concert_id, category)["data"]

    try:
        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    "price": stripeids["price_id"],
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


## ADMIN
#create stripe ids from Stripe
def create_stripeids(product_name, price):

    price = stripe.Price.create(
        currency="sgd",
        unit_amount=price * 100, #in cents
        product_data={"name": product_name},
    )

    print(price)

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
        db.select(StripeIds).filter_by(concert_id=concert_id, category=category).limit(1)
    ).first():
        return (
            jsonify(
                {
                    "code": 400,
                    "data": {"concert_id": concert_id,
                             "category": category},
                    "message": "Stripe IDs already exist.",
                }
            ),
            400,
        )

    # data = request.get_json()
    # concert_name = data["name"]
    # price = data["price"]

    concert_name = "PLEASE"
    price = 1000

    stripeids = create_stripeids(concert_name, price)

    stripeids_db = StripeIds(
                                concert_id=concert_id,
                                category=category,
                                concert_name=concert_name,
                                price_id=stripeids["data"]["price_id"],
                                product_id=stripeids["data"]["product_id"]
                            )
    
    try:
        db.session.add(stripeids_db)
        db.session.commit()
    except:
        return (
            jsonify(
                {
                    "code": 500,
                    "data": {"concert_id": concert_id,
                             "category": category},
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5006, debug=True)
