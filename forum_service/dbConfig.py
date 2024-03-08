from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os

app = Flask(__name__)
PORT = 5003
CORS(app, supports_credentials=True)

db_username = os.environ.get("DB_USERNAME")
db_password = os.environ.get("DB_PASSWORD")
database_uri = f"postgresql://{db_username}:{db_password}@localhost:5432/forum"
app.config["SQLALCHEMY_DATABASE_URI"] = database_uri
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)