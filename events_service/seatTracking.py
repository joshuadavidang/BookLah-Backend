from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from os import environ


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('dbURL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Concert(db.Model):
    __tablename__ = 'tracking'

    concertID = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.Integer, primary_key=True)
    capacity = db.Column(db.Integer, nullable=False)
    takenSeats = db.Column(db.Integer, nullable=False)

    def __init__(self, concertID, category, capacity, takenSeats):
        self.concertID = concertID
        self.category = category
        self.capacity = capacity
        self.takenSeats = takenSeats

    def json(self):
        return {"concertID": self.concertID, "category": self.category, "capacity": self.capacity, "takenSeats": self.takenSeats}



@app.route("/tracking")
def get_all():
    tracking_list = db.session.execute("SELECT * FROM tracking").fetchall()

    if len(tracking_list):
        return jsonify(
            {
                "code": 200,
                "data": {
                    "tracking": [tracking.json() for tracking in tracking_list]
                }
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": "There are no concert records."
        }
    ), 404



@app.route("/tracking/<string:concertID>")
def find_by_concertID(concertID, category):
    concert = db.session.execute(
        "SELECT * FROM tracking WHERE concertID = :concertID AND category = :category LIMIT 1",
        {"concertID": concertID, "category": category}
    ).fetchone()


    if concert:
        return jsonify(
            {
                "code": 200,
                "data": concert.json()
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": "Concert not found."
        }
    ), 404



@app.route("/tracking/<string:concertID>", methods=['POST'])
def create_tracking(concertID, category):

    existing_record = db.session.execute(
            "SELECT * FROM tracking WHERE concertID = :concertID AND category = :category LIMIT 1",
            {"concertID": concertID, "category": category}
        ).fetchone()
    
    if existing_record:
        return jsonify(
            {
                "code": 400,
                "data": {
                    "concertID": concertID
                },
                "message": "Concert tracking record already exists."
            }
        ), 400


    data = request.get_json()
    concert_data = {"concertID": concertID, "category": data.get('category')}
    concert = concert(**concert_data, **data)


    try:
        db.session.add(concert)
        db.session.commit()
    except:
        return jsonify(
            {
                "code": 500,
                "data": {
                    "concertID": concertID,
                    "category": category
                },
                "message": "An error occurred creating the concert."
            }
        ), 500


    return jsonify(
        {
            "code": 201,
            "data": concert.json()
        }
    ), 201




if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
