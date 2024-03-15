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

    def json(self):
        return {
            "concert_id": self.concert_id,
            "category": self.category,
            "concert_name": self.concert_name,
            "price_id": self.price_id,
            "product_id": self.product_id,
        }


@app.route("/payment/<string:concert_id>/<string:category>")
def get_stripeids(concert_id, category):
    stripe_ids = (
        db.session.query(StripeIds)
        .filter_by(concert_id=concert_id, category=category)
        .first()
    )
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

    # concert_id = request.json.get("concert_id", None)
    # category = request.json.get("category", None)
    # quantity = request.json.get("quantity", None)

    # price = result["price_id"]
    concert_name = "test"
    result = create_stripeids(concert_name)

    return jsonify(result)

    # try:
    #     checkout_session = stripe.checkout.Session.create(
    #         line_items=[
    #             {
    #                 "price": "price_1OsSEpFBfCxiguYffsBlmZ5m",
    #                 "quantity": 1,
    #             },
    #         ],
    #         mode="payment",
    #         invoice_creation={"enabled": True},
    #         success_url=FRONT_END_DOMAIN + "/success?session_id={CHECKOUT_SESSION_ID}",
    #         cancel_url=FRONT_END_DOMAIN + "/error",
    #     )

    # except Exception as e:
    #     return str(e)

    # return jsonify({"checkout_url": checkout_session.url})




#create stripe ids from Stripe
def create_stripeids(product_name):

    price = stripe.Price.create(
        currency="sgd",
        unit_amount=1000, #in cents
        product_data={"name": product_name},
        )

    return {"price_id": price["id"], "product_id": price["product"]}

#add Stripe IDs to database
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

    data = request.get_json()
    stripe_ids = StripeIds(concert_id, category, **data)

    try:
        db.session.add(stripe_ids)
        db.session.commit()
    except:
        return (
            jsonify(
                {
                    "code": 500,
                    "data": {"concert_id": concert_id,
                             "category": category},
                    "message": "An error occurred creating the Stripe IDs.",
                }
            ),
            500,
        )

    return (
        jsonify(
            {
                "code": 201,
                "data": stripe_ids.json(),
                "message": "Stripe IDs have been added successfully",
            }
        ),
        201,
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)
