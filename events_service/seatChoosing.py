from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
from flask_sqlalchemy import SQLAlchemy

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root@localhost:3306/book'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Seats(db.Model):
    __tablename__ = 'seats'

    concertID = db.Column(db.Integer, nullable=False)
    category = db.Column(db.Integer, nullable=False)
    seat_number = db.Column(db.Integer, nullable=False)
    taken = db.Column(db.Boolean, nullable=False)

def __init__(self, concertID, category, seat_number, taken):
    self.concertID = concertID
    self.category = category
    self.seat_number = seat_number
    self.taken = taken

def json(self):
    return {"concertID": self.concertID, "category": self.category, "seat_number": self.seat_number, "taken": self.taken}



@app.route("/seats")
def get_all():
    seats_list = db.session.execute("SELECT * FROM seats").fetchall()

    if len(seats_list):
        return jsonify(
            {
                "code": 200,
                "data": {
                    "seats": [seat.json() for seat in seats_list]
                }
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": "There are no seats."
        }
    ), 404



@app.route("/seats/<string:concertID>")
def find_by_seat(concertID, category, seat_number):
    seat = db.session.execute(
        "SELECT * FROM seats WHERE concertID = :concertID AND category = :category AND seat_number = :seat_number LIMIT 1",
        {"concertID": concertID, "category": category, "seat_number": seat_number}
    ).fetchone()

    if seat:
        return jsonify(
            {
                "code": 200,
                "data": seat.json()
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": "Seat not found."
        }
    ), 404



@app.route("/seats/<string:concertID>", methods=['POST'])
def create_tracking(concertID, category, seat_number):

    existing_record = db.session.execute(
        "SELECT * FROM seats WHERE concertID = :concertID AND category = :category AND seat_number = :seat_number LIMIT 1",
        {"concertID": concertID, "category": category, "seat_number": seat_number}
    ).fetchone()    

    if existing_record:
        return jsonify(
            {
                "code": 400,
                "data": {
                    "concertID": concertID,
                    "category": category,
                    "seat_number": seat_number

                },
                "message": "Seat number record already exists."
            }
        ), 400


    data = request.get_json()
    seat_data = {
        "concertID": concertID,
        "category": data.get('category'),
        "seat_number": data.get('seat_number'),
        "taken": data.get('taken')
    }
    seat = Seats(**seat_data)

    try:
        db.session.add(seat)
        db.session.commit()
    except:
        return jsonify(
            {
                "code": 500,
                "data": {
                    "concertID": concertID,
                    "category": category,
                    "seat_number": seat_number
                },
                "message": "An error occurred creating the seat."
            }
        ), 500


    return jsonify(
        {
            "code": 201,
            "data": seat.json()
        }
    ), 201




if __name__ == '__main__':
    app.run(port=5000, debug=True)
