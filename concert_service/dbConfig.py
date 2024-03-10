from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from dotenv import load_dotenv
import os
import stripe

load_dotenv()

app = Flask(__name__)
PORT = 5001
CORS(app, supports_credentials=True)

db_username = os.getenv("DB_USERNAME")
db_password = os.getenv("DB_PASSWORD")
database_uri = os.getenv("DATABASE_URI")

app.config["SQLALCHEMY_DATABASE_URI"] = database_uri
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["STRIPE_PUBLIC_KEY"] = os.getenv("STRIPE_PUBLIC_KEY")
app.config["STRIPE_SECRET_KEY"] = os.getenv("STRIPE_SECRET_KEY")

stripe.api_key = app.config["STRIPE_SECRET_KEY"]

db = SQLAlchemy(app)
