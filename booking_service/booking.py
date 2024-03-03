from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root@localhost:3306/booking'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Booking(db.Model):
    __tablename__ = 'booking'
    booking_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    concert_id = db.Column(db.Integer, nullable=False)
    performer = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    price = db.Column(db.Float(precision=2), nullable=False)
    cat_number = db.Column(db.Integer)
    seat_number = db.Column(db.String(10), nullable=False)
    availability = db.Column(db.Integer)

    def json(self):
        return {
            "booking_id": self.booking_id,
            "user_id": self.user_id,
            "concert_id": self.concert_id,
            "performer": self.performer,
            "title": self.title,
            "date": str(self.date),
            "time": str(self.time),
            "price": self.price,
            "cat_number": self.cat_number,
            "seat_number": self.seat_number,
            "availability": self.availability
        }

@app.route("/booking", methods=['GET'])
def get_all_bookings():
    booking_list = Booking.query.all()
    if len(booking_list) > 0:
        return jsonify({"code": 200, "data": {"bookings": [booking.json() for booking in booking_list]}})
    return jsonify({"code": 404, "message": "There are no bookings."}), 404

@app.route("/booking/<int:booking_id>", methods=['GET'])
def find_booking_by_id(booking_id):
    booking = Booking.query.get(booking_id)
    if booking:
        return jsonify({"code": 200, "data": booking.json()})
    return jsonify({"code": 404, "message": "Booking not found."}), 404

@app.route("/booking", methods=['POST'])
def create_booking():
    data = request.json
    booking = Booking(**data)
    try:
        db.session.add(booking)
        db.session.commit()
        return jsonify({"code": 201, "data": booking.json()}), 201
    except Exception as e:
        return jsonify({"code": 500, "message": f"An error occurred while creating the booking: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
