from flask import Flask, redirect, request, jsonify
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from sqlalchemy.dialects.postgresql import UUID
import os
import stripe

load_dotenv()

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URI")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_recycle": 299}
app.config["STRIPE_PUBLIC_KEY"] = os.getenv("STRIPE_PUBLIC_KEY")
app.config["STRIPE_SECRET_KEY"] = os.getenv("STRIPE_SECRET_KEY")
stripe.api_key = app.config["STRIPE_SECRET_KEY"]
FRONT_END_DOMAIN = "http://localhost:3000"

PORT = 5006
db = SQLAlchemy(app)
CORS(app)


class StripeIds(db.Model):
    __tablename__ = "payment"

    concert_id = db.Column(UUID(as_uuid=True), primary_key=True)
    category = db.Column(db.String(100), primary_key=True)
    concert_name = db.Column(db.String(100), nullable=False)
    price_obj = db.Column(db.String(100), nullable=False)
    price_id = db.Column(db.String(100), nullable=False)
    product_id = db.Column(db.String(100), nullable=False)

    __table_args__ = (db.PrimaryKeyConstraint("concert_id", "category"),)

    def json(self):
        return {
            "concert_id": self.concert_id,
            "category": self.category,
            "concert_name": self.concert_name,
            "price_obj": self.price_obj,
            "price_id": self.price_id,
            "product_id": self.product_id,
        }


@app.route("/payment/<string:concert_id>/<string:category>")
def find_stripe_ids(concert_id, category):
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

    # if not find_stripe_ids(concert_id, category):
    #     result = create_products()["data"]
    # else:
    #     result = find_stripe_ids(concert_id, category)["data"]

    # price = result["price_id"]

    try:
        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    "price": "price_1OsSEpFBfCxiguYffsBlmZ5m",
                    "quantity": 1,
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=True)
