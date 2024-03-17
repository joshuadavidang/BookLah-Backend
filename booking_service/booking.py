from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import uuid

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = (
    "mysql+mysqlconnector://root:root@localhost:8889/booking_process"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

######## 3 ENDPOINTS ########

# /api/v1/get_bookings
# /api/v1/get_booking/<string:booking_id>
# /api/v1//api/v1/create_booking


class Booking(db.Model):
    __tablename__ = "booking"
    booking_id = db.Column(
        db.String(50), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id = db.Column(db.String(50), nullable=False)
    concert_id = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    cat_no = db.Column(db.String, nullable=False)
    seat_no = db.Column(
        db.String(255), nullable=False
    )  # Change to String type for storing array of seat numbers
    quantity = db.Column(db.Integer, nullable=False)
    email = db.Column(db.String(50), nullable=False)

    def json(self):
        return {
            "booking_id": self.booking_id,
            "user_id": self.user_id,
            "concert_id": self.concert_id,
            "price": self.price,
            "cat_no": self.cat_no,
            "seat_no": self.seat_no.split(","),
            "quantity": self.quantity,
            "email": self.email,
        }


@app.route("/api/v1/get_bookings", methods=["GET"])
def get_all_bookings():
    booking_list = Booking.query.all()
    if len(booking_list) > 0:
        return jsonify(
            {
                "code": 200,
                "data": {"bookings": [booking.json() for booking in booking_list]},
            }
        )
    return jsonify({"code": 404, "message": "There are no bookings."}), 404


@app.route("/api/v1/get_booking/<string:booking_id>", methods=["GET"])
def find_booking_by_id(booking_id):
    booking = Booking.query.get(booking_id)
    if booking:
        return jsonify({"code": 200, "data": booking.json()})
    return (
        jsonify(
            {
                "code": 404,
                "data": {"booking_id": booking_id},
                "message": "Booking not found.",
            }
        ),
        404,
    )


@app.route("/api/v1/create_booking", methods=["POST"])
def create_booking():
    data = request.json
    booking = Booking(**data)
    try:
        db.session.add(booking)
        db.session.commit()
        return jsonify({"code": 201, "data": booking.json()}), 201
    except Exception as e:
        return (
            jsonify(
                {
                    "code": 500,
                    "message": f"An error occurred while creating the booking: {str(e)}",
                }
            ),
            500,
        )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
