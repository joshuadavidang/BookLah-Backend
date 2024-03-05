from flask import Flask, redirect, request, jsonify
from dotenv import load_dotenv
import os

import stripe

app = Flask(__name__)

def configure():
    load_dotenv()

app.config["STRIPE_PUBLIC_KEY"] = os.getenv("public_key")
app.config["STRIPE_SECRET_KEY"] = os.getenv("secret_key")

stripe.api_key = app.config["STRIPE_SECRET_KEY"]

app = Flask(__name__, static_url_path='', static_folder='./payment_test')

YOUR_DOMAIN = 'http://localhost:5002'

@app.route('/process_payment', methods=['POST'])
def process_payment():
    # get json data from frontend 
    # import events db to generate price id? -> create line items array dynamically 

    session = create_checkout_session()

    return jsonify({"checkout_url": session.url})

def create_checkout_session():
    configure()    

    try:
        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    # Provide the exact Price ID (for example, pr_1234) of the product you want to sell
                    'price': 'price_1Onmq1FBfCxiguYfQ7QJVpcw',
                    'quantity': 1,
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