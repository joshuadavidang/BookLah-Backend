from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from dotenv import load_dotenv
import os

load_dotenv()
app = Flask(__name__)
PORT = 5002
CORS(app, supports_credentials=True)

app.config["SQLALCHEMY_DATABASE_URI"] = (
    "postgresql://joshuadavid:password123@localhost:5432/concertdb"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
