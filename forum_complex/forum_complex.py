from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests


app = Flask(__name__)
CORS(app)

booking_URL = ""
forum_URL = "http://localhost:5003"

@app.route("/get_forum", methods=['GET'])
def get_forum():
    try:
        response = requests.get(f"{forum_URL}/getPosts")

        if response.status_code == 200:
            forums = response.json()["data"]["posts"]
            return jsonify(forums), 200
        else:
            return jsonify({
                "code": response.status_code,
                "message": "Failed to fetch forums from the forum microservice"
            }), response.status_code

    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"An error occurred: {str(e)}"
        }), 500
    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5011, debug=True)

