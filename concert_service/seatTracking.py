from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from os import environ


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = environ.get("dbURL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class ConcertTracking(db.Model):
    __tablename__ = "tracking"
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
        return {
            "concertID": self.concertID,
            "category": self.category,
            "capacity": self.capacity,
            "takenSeats": self.takenSeats,
        }


@app.route("/api/v1/tracking")
def get_all():
    tracking_list = db.session.scalars(db.select(ConcertTracking)).all()

    if len(tracking_list):
        return jsonify(
            {
                "code": 200,
                "data": {"tracking": [tracking.json() for tracking in tracking_list]},
            }
        )
    return jsonify({"code": 404, "message": "There are no concert tracking records."}), 404


@app.route("/api/v1/tracking/<string:concertID>/<string:category>")
def find_by_concertID(concertID, category):
    concertTracking = db.session.scalars(
        db.select(ConcertTracking).filter_by(concertID = concertID, category = category).limit(1)).first()

    if concertTracking:
        return jsonify({"code": 200, "data": concertTracking.json()})
    return jsonify({"code": 404, "message": "Concert tracking not found."}), 404


@app.route("/tracking/<string:concertID>/<string:category>", methods=["POST"])
def create_tracking(concertID, category):

    existing_record = db.session.execute(
        "SELECT * FROM tracking WHERE concertID = :concertID AND category = :category LIMIT 1",
        {"concertID": concertID, "category": category},
    ).fetchone()

    if existing_record:
        return (
            jsonify(
                {
                    "code": 400,
                    "data": {"concertID": concertID},
                    "message": "Concert tracking record already exists.",
                }
            ),
            400,
        )

    data = request.get_json()
    concert_data = {"concertID": concertID, "category": data.get("category")}
    concert = concert(**concert_data, **data)

    try:
        db.session.add(concert)
        db.session.commit()
    except:
        return (
            jsonify(
                {
                    "code": 500,
                    "data": {"concertID": concertID, "category": category},
                    "message": "An error occurred creating the concert.",
                }
            ),
            500,
        )

    return jsonify({"code": 201, "data": concert.json()}), 201

@app.route("/tracking/<string:concertID>/<string:category>", methods=['PUT'])
def update_availseats(concertID, category):
    try:
        tracking = db.session.scalars(
        db.select(ConcertTracking).filter_by(concertID=concertID, category= category).
        limit(1)).first()
        if not tracking:
            return jsonify(
                {
                    "code": 404,
                    "data": {
                        "concertID": concertID, 
                        "category": category
                    },
                    "message": "Concert not found."
                }
            ), 404

        data = request.get_json()
        if 'takenSeats' in data:
            current_taken_seats = ConcertTracking.query.first().takenSeats
            new_taken_seats = current_taken_seats + 1
            ConcertTracking.takenSeats = new_taken_seats
            db.session.commit()
            return jsonify(
                {
                    "code": 200,
                    "data": {"takenSeats": new_taken_seats}
                }
            ), 200
    except Exception as e:
        return jsonify(
            {
                "code": 500,
                "data": {
                    "concertID": concertID, 
                    "category": category
                },
                "message": "An error occurred while updating the number of seats taken. " + str(e)
            }
        ), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
