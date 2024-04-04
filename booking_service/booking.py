from flask import request, jsonify
import uuid
from dbConfig import app, db, PORT

######## 4 ENDPOINTS ########

# /api/v1/get_bookings
# /api/v1/get_booking/<string:booking_id>
# /api/v1/create_booking
# /api/v1/update_forum_joined


class Booking(db.Model):
    __tablename__ = "booking"
    booking_id = db.Column(
        db.String(100), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id = db.Column(db.String(100), nullable=False)
    concert_id = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    cat_no = db.Column(db.String, nullable=False)
    seat_no = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    email = db.Column(db.String(100), nullable=False)
    forum_joined = db.Column(db.BOOLEAN, nullable=False, default=True)

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
            "forum_joined": self.forum_joined,
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
    return jsonify({"code": 404, "message": "There are no bookings."})


@app.route("/api/v1/get_booking/<string:booking_id>", methods=["GET"])
def find_booking_by_id(booking_id):
    booking = Booking.query.get(booking_id)
    if booking:
        return jsonify({"code": 200, "data": booking.json()})
    return jsonify(
        {
            "code": 404,
            "data": {"booking_id": booking_id},
            "message": "Booking not found.",
        }
    )


@app.route("/api/v1/get_concert_bookings/<string:concert_id>", methods=["GET"])
def get_concert_bookings(concert_id):
    booking_list = Booking.query.filter_by(concert_id=concert_id).all()
    if len(booking_list) > 0:
        return jsonify(
            {
                "code": 200,
                "data": {"bookings": [booking.json() for booking in booking_list]},
            }
        )
    return jsonify(
        {"code": 404, "message": f"No bookings found for concert_id: {concert_id}"}
    )


@app.route("/api/v1/get_user_bookings/<string:user_id>", methods=["GET"])
def get_bookings_by_user(user_id):
    booking_list = Booking.query.filter_by(user_id=user_id).all()
    if len(booking_list) > 0:
        return jsonify(
            {
                "code": 200,
                "data": {"bookings": [booking.json() for booking in booking_list]},
            }
        )
    return jsonify(
        {"code": 404, "message": f"No bookings found for user_id: {user_id}"}
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
        return jsonify(
            {
                "code": 500,
                "message": f"An error occurred while creating the booking: {str(e)}",
            }
        )


@app.route("/api/v1/update_forum_joined", methods=["PUT"])
def update_forum_joined():
    data = request.get_json()
    concert_id = data.get("concert_id")
    user_id = data.get("user_id")
    forum_joined = data.get("forum_joined")

    forum_arr = (
        db.session.query(Booking)
        .filter_by(concert_id=concert_id, user_id=user_id)
        .all()
    )

    for forum in forum_arr:
        try:
            forum.forum_joined = forum_joined
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return (
                jsonify(
                    {
                        "code": 500,
                        "data": {"forum_joined": forum_joined},
                        "message": "An error occurred while updating forum joined status: "
                        + str(e),
                    }
                ),
                500,
            )

    return jsonify(
        {
            "code": 200,
            "data": {"concert_id": concert_id, "forum_joined": forum_joined},
            "message": "Successfully updated forum joined status",
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=True)
