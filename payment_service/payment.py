from flask import Flask, redirect, request, jsonify
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
import os
import stripe

load_dotenv()

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:root@localhost:8889/esd_proj'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 299}

db = SQLAlchemy(app)

CORS(app)  

app.config["STRIPE_PUBLIC_KEY"] = os.getenv("STRIPE_PUBLIC_KEY")
app.config["STRIPE_SECRET_KEY"] = os.getenv("STRIPE_SECRET_KEY")

stripe.api_key = app.config["STRIPE_SECRET_KEY"]

YOUR_DOMAIN = 'http://localhost:5002'

class StripeIds(db.Model):
    __tablename__ = 'payment'

    concert_id = db.Column(UUID(as_uuid=True), primary_key=True)
    category = db.Column(db.String(100), primary_key=True)
    concert_name = db.Column(db.String(100), nullable=False)
    price_obj = db.Column(db.String(100), nullable=False)
    price_id = db.Column(db.String(100), nullable=False)
    product_id = db.Column(db.String(100), nullable=False)
    
    __table_args__ = (
        db.PrimaryKeyConstraint('concert_id', 'category'),
    )

    def json(self):
        return {
            'concert_id': self.concert_id,
            'category': self.category,
            'concert_name': self.concert_name,
            'price_obj': self.price_obj,
            'price_id': self.price_id,
            'product_id': self.product_id
        }

@app.route("/payment/<string:concert_id>/<string:category>")
def find_stripe_ids(concert_id, category):
    stripe_ids = db.session.query(StripeIds).filter_by(concert_id=concert_id, category=category).first()
    if stripe_ids:
        return jsonify(
            {
                "code": 200,
                "data": stripe_ids.json()
            }
        )
    return jsonify(
        {
            "code": 404,
            "data": {
                "concert_id": concert_id,
                "category": category
            },
            "message": "Stripe IDs not found."
        }
    ), 404

@app.route("/create_products/<string:id>", methods=['POST'])
def create_products(id):
    # concert_id = request.json.get('concert_id', None)
    # category = request.json.get('category', None)
    # concert_name = request.json.get('concert_name', None)
    data = request.get_json()
    print(data)
    # price = request.json.get('price', None)

    if (db.session.scalars(db.select(StripeIds).filter_by(concert_id=id).limit(1)).first()):
        return jsonify(
            {
                "code": 400,
                "data": {
                    "concert_id": id,
                },
                "message": "Stripe Id already exists."
            }
        ), 400
    
    # price_obj = stripe.Price.create(
    #             currency="sgd",
    #             unit_amount=(price * 100),
    #             product_data={"name": concert_name},
    #             )
    
    # stripeids = StripeIds(concert_id=concert_id, 
    #                       category=category, 
    #                       concert_name=concert_name, 
    #                       price_obj = str(price_obj),
    #                       price_id=price_obj["id"],
    #                       product_id=price_obj["product"])

    
    stripeids = StripeIds(id, **data)

    try:
        db.session.add(stripeids)
        db.session.commit()
    except:
        return jsonify(
            {
                "code": 500,
                "data": {
                    "stripeids": stripeids
                },
                "message": "An error occurred creating the book."
            }
        ), 500

    return jsonify(
        {
            "code": 201,
            "data": stripeids.json()
        }
    ), 201


@app.route('/process_payment', methods=['POST'])
def create_session():

    concert_id = request.json.get('concert_id', None)
    category = request.json.get('category', None)
    quantity = request.json.get('quantity', None)

    if not find_stripe_ids(concert_id, category):
        result = create_products()["data"]
    else:
        result = find_stripe_ids(concert_id, category)["data"]

    price = result["price_id"]

    try:
        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    # Provide the exact Price ID (for example, pr_1234) of the product you want to sell
                    'price': price,
                    'quantity': quantity,
                },
            ],
            mode='payment',
            invoice_creation={"enabled": True},
            success_url=YOUR_DOMAIN + '/success.html?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=YOUR_DOMAIN + '/cancel.html',
        )
        
    except Exception as e:
        return str(e)
    
    return redirect(checkout_session.url, code=303)
    # return jsonify({"checkout_url": checkout_session.url})

@app.route('/session-status', methods=['GET'])
def session_status():
  session = stripe.checkout.Session.retrieve(request.args.get('session_id'))

  return jsonify(status=session.status, customer_email=session.customer_details.email)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)