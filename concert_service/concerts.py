from flask import request, jsonify
from dbConfig import app, db, PORT
from sqlalchemy import Enum
from datetime import datetime
from sqlalchemy.orm import relationship
import uuid

######## 8 ENDPOINTS ########


# /api/v1/getConcerts
# /api/v1/getConcert/<string:concert_id>
# /api/v1/getAdminCreatedConcert/<string:userId>
# /api/v1/addConcert/<string:concert_id>
# /api/v1/updateConcertAvailability/<string:concert_id>
# /api/v1/updateConcertDetails/<string:concert_id>
# /api/v1/getAvailableConcerts


class Concert(db.Model):
    __tablename__ = "concerts"
    concert_id = db.Column(db.String(100), primary_key=True)
    performer = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    venue = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String, nullable=False)
    time = db.Column(db.String, nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(1000), nullable=False)
    category = db.Column(db.String(100), nullable=False, default="category1")
    price = db.Column(db.INTEGER, nullable=False, default=0)
    concert_status = db.Column(
        Enum("AVAILABLE", "CANCELLED", name="concert_status_enum"),
        nullable=False,
        default="AVAILABLE",
    )
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now())
    created_by = db.Column(db.String(100), nullable=False)

    seats = relationship("Seats", backref="concert")

    def __init__(
        self,
        concert_id,
        performer,
        title,
        venue,
        date,
        time,
        capacity,
        price,
        concert_status,
        description,
        created_by,
    ):
        self.concert_id = concert_id
        self.performer = performer
        self.title = title
        self.venue = venue
        self.date = date
        self.time = time
        self.capacity = capacity
        self.price = price
        self.concert_status = concert_status
        self.description = description
        self.created_by = created_by

    def json(self):
        return {
            "concert_id": self.concert_id,
            "performer": self.performer,
            "title": self.title,
            "venue": self.venue,
            "date": self.date,
            "time": self.time,
            "capacity": self.capacity,
            "price": self.price,
            "concert_status": self.concert_status,
            "description": self.description,
            "created_by": self.created_by,
        }


class Seats(db.Model):
    __tablename__ = "seats"
    id = db.Column(db.String(100), primary_key=True, default=lambda: str(uuid.uuid4()))
    concert_id = db.Column(
        db.String(100), db.ForeignKey("concerts.concert_id"), nullable=False
    )
    category = db.Column(db.String(100), nullable=False)
    seat_no = db.Column(db.String(10), nullable=False)
    is_taken = db.Column(db.Boolean, nullable=False)

    def __init__(self, concert_id, category, seat_no, is_taken):
        self.concert_id = concert_id
        self.category = category
        self.seat_no = seat_no
        self.is_taken = is_taken

    def json(self):
        return {
            "concert_id": self.concert_id,
            "category": self.category,
            "seat_no": self.seat_no,
            "is_taken": self.is_taken,
        }


class ConcertTracking(db.Model):
    __tablename__ = "tracking"
    concert_id = db.Column(db.String(50), primary_key=True)
    category = db.Column(db.String, primary_key=True)
    capacity = db.Column(db.Integer, nullable=False)
    takenSeats = db.Column(db.Integer, nullable=False)

    def __init__(self, concert_id, category, capacity, takenSeats):
        self.concert_id = concert_id
        self.category = category
        self.capacity = capacity
        self.takenSeats = takenSeats

    def json(self):
        return {
            "concert_id": self.concert_id,
            "category": self.category,
            "capacity": self.capacity,
            "takenSeats": self.takenSeats,
        }


@app.route("/api/v1/getConcerts")
def getConcerts():
    concerts = db.session.scalars(db.select(Concert)).all()
    if len(concerts):
        return jsonify(
            {
                "code": 200,
                "data": {"concerts": [concert.json() for concert in concerts]},
            }
        )
    return jsonify({"code": 404, "message": "There are no concerts."}), 404


@app.route("/api/v1/getConcert/<string:concert_id>")
def getConcert(concert_id):
    concert = db.session.scalars(
        db.select(Concert).filter_by(concert_id=concert_id).limit(1)
    ).first()

    if not concert:
        return jsonify({"code": 404, "message": "concert not found."}), 404

    return jsonify({"code": 200, "data": concert.json()})


@app.route("/api/v1/getAvailableConcerts", methods=["POST"])
def getAvailableConcerts():
    data = request.get_json()
    concert_arr = data.get("concerts")
    available_concerts = []

    if len(concert_arr) == 0:
        return jsonify({"code": 400, "message": "no available concerts."})

    for concert in concert_arr:
        concert_obj = getConcert(concert).json
        status = concert_obj["data"]["concert_status"]

        if status == "AVAILABLE":
            available_concerts.append(concert)

    return jsonify(
        {
            "code": 200,
            "data": {
                "available_concerts": available_concerts,
            },
        }
    )


################### ADMIN ENDPOINTS ######################
@app.route("/api/v1/getAdminCreatedConcert/<string:userId>")
def getAdminCreatedConcert(userId):
    """
    To be called by admin only to retrieve the list of created concerts
    """

    concerts = db.session.scalars(db.select(Concert).filter_by(created_by=userId)).all()
    if not concerts:
        return jsonify({"code": 404, "message": "concert not found."}), 404

    return jsonify({"code": 200, "data": [concert.json() for concert in concerts]})


@app.route("/api/v1/addConcert/<string:concert_id>", methods=["POST"])
def addConcert(concert_id):
    """
    To be called by admin only to add new concerts
    """

    if db.session.scalars(
        db.select(Concert).filter_by(concert_id=concert_id).limit(1)
    ).first():
        return (
            jsonify(
                {
                    "code": 400,
                    "data": {"concert_id": concert_id},
                    "message": "Concert already exists.",
                }
            ),
            400,
        )

    data = request.get_json()
    concert = Concert(concert_id, **data)

    try:
        db.session.add(concert)
        db.session.commit()
    except:
        return (
            jsonify(
                {
                    "code": 500,
                    "data": {"concert_id": concert_id},
                    "message": "An error occurred creating the concert.",
                }
            ),
            500,
        )

    return (
        jsonify(
            {
                "code": 201,
                "data": concert.json(),
                "message": "A new concert has been added",
            }
        ),
        201,
    )


@app.route("/api/v1/updateConcertAvailability/<string:concert_id>", methods=["PUT"])
def updateConcertAvailability(concert_id):
    """
    For admins to update concert availability
    AVAILABLE | CANCELLED
    """

    concert = db.session.query(Concert).filter_by(concert_id=concert_id).first()
    if not concert:
        return jsonify(
            {
                "code": 404,
                "data": {"concert_id": concert_id},
                "message": "Concert not found.",
            }
        )

    concertStatus = request.get_json()["concertStatus"]

    try:
        db.session.query(Concert).filter_by(concert_id=concert_id).update(
            {"concert_status": concertStatus}
        )
        db.session.commit()
        return (
            jsonify(
                {
                    "code": 200,
                    "data": {"concert_id": concert_id},
                    "message": "Updated concert status successfully.",
                }
            ),
            200,
        )
    except:
        return (
            jsonify(
                {
                    "code": 500,
                    "data": {"concert_id": concert_id},
                    "message": "An error occurred while updating the concert status",
                }
            ),
            500,
        )


@app.route("/api/v1/updateConcertDetails/<string:concert_id>", methods=["PUT"])
def updateConcertDetails(concert_id):
    """
    For admins to update concert details
    """

    concert = db.session.query(Concert).filter_by(concert_id=concert_id).first()
    if not concert:
        return jsonify(
            {
                "code": 404,
                "data": {"concert_id": concert_id},
                "message": "Concert not found.",
            }
        )

    updatedData = request.get_json()

    try:
        db.session.query(Concert).filter_by(concert_id=concert_id).update(updatedData)
        db.session.commit()
        return (
            jsonify(
                {
                    "code": 204,
                    "data": {"concert_id": concert_id},
                    "message": "Updated concert details successfully.",
                }
            ),
            200,
        )
    except:
        return (
            jsonify(
                {
                    "code": 500,
                    "data": {"concert_id": concert_id},
                    "message": "An error occurred while updating the concert details",
                }
            ),
            500,
        )


################### SEATS ENDPOINTS ######################
@app.route("/api/v1/getSeats")
def getSeats():
    seats_list = db.session.scalars(db.select(Seats)).all()
    if len(seats_list):
        return jsonify(
            {"code": 200, "data": {"seats": [seat.json() for seat in seats_list]}}
        )
    return jsonify({"code": 404, "message": "There are no seats."}), 404


@app.route("/api/v1/getSeatsByConcertId/<string:concert_id>")
def getSeatsByConcertId(concert_id):
    seats_list = db.session.scalars(
        db.select(Seats).filter_by(concert_id=concert_id, is_taken=False)
    ).all()

    if not seats_list:
        return jsonify({"code": 404, "message": "There are no seats available."}), 404

    return jsonify(
        {"code": 200, "data": {"seats": [seat.json() for seat in seats_list]}}
    )


@app.route("/api/v1/countNumSeatsAvailable/<string:concert_id>")
def countNumSeatsAvailable(concert_id):
    seats_list = db.session.scalars(
        db.select(Seats).filter_by(concert_id=concert_id, is_taken=False)
    ).all()
    return jsonify({"code": 200, "data": {"numSeatsAvailable": len(seats_list)}})


@app.route("/api/v1/findBySeat/<string:concert_id>/<string:category>/<string:seat_no>")
def findBySeat(concert_id, category, seat_no):
    seat = db.session.scalars(
        db.select(Seats)
        .filter_by(concert_id=concert_id, category=category, seat_no=seat_no)
        .limit(1)
    ).first()
    if seat:
        return jsonify({"code": 200, "data": seat.json()})
    return jsonify({"code": 404, "message": "Seat not found."}), 404


@app.route(
    "/api/v1/createSeats/<string:concert_id>/<string:category>/<int:number_of_seats>",
)
def createSeats(concert_id, category, number_of_seats):
    seat_data_list = [
        {
            "concert_id": concert_id,
            "category": category,
            "seat_no": f"A{i + 1}",
            "is_taken": False,
        }
        for i in range(number_of_seats)
    ]

    seats = [Seats(**seat_data) for seat_data in seat_data_list]

    try:
        db.session.add_all(seats)
        db.session.commit()
    except Exception as e:
        return (
            jsonify(
                {
                    "code": 500,
                    "data": {
                        "concert_id": concert_id,
                        "category": category,
                        "number_of_seats": number_of_seats,
                    },
                    "message": f"An error occurred creating the seats. ${str(e)}",
                }
            ),
            500,
        )

    return jsonify({"code": 201, "data": [seat.json() for seat in seats]}), 201


@app.route(
    "/api/v1/updateSeat",
    methods=["PUT"],
)
def updateSeat():
    data = request.get_json()
    concert_id = data.get("concert_id")
    category = data.get("category")
    seat_no = data.get("seat_no").split(",")
    is_taken = data.get("is_taken")

    updated_seats = []

    for seat in seat_no:
        seat_obj = (
            db.session.query(Seats)
            .filter_by(concert_id=concert_id, category=category, seat_no=seat)
            .first()
        )
        if not seat_obj:
            return (
                jsonify(
                    {
                        "code": 404,
                        "data": {
                            "concert_id": concert_id,
                            "category": category,
                            "seat_no": seat,
                        },
                        "message": "Seat not found.",
                    }
                ),
                404,
            )

        try:
            seat_obj.is_taken = is_taken
            updated_seats.append(seat)
        except Exception as e:
            db.session.rollback()
            return (
                jsonify(
                    {
                        "code": 500,
                        "data": {"is_taken": is_taken},
                        "message": "An error occurred while updating the seat status: "
                        + str(e),
                    }
                ),
                500,
            )

    try:
        db.session.commit()
        return (
            jsonify(
                {
                    "code": 200,
                    "data": {"updated_seats": updated_seats},
                    "message": "Updated seat status successfully.",
                }
            ),
            200,
        )
    except Exception as e:
        db.session.rollback()
        return (
            jsonify(
                {
                    "code": 500,
                    "data": {"is_taken": is_taken},
                    "message": "An error occurred while committing changes: " + str(e),
                }
            ),
            500,
        )


################### TRACKING ENDPOINTS ######################
@app.route("/api/v1/getTracking")
def getTracking():
    tracking_list = db.session.scalars(db.select(ConcertTracking)).all()

    if len(tracking_list):
        return jsonify(
            {
                "code": 200,
                "data": {"tracking": [tracking.json() for tracking in tracking_list]},
            }
        )
    return (
        jsonify({"code": 404, "message": "There are no concert tracking records."}),
        404,
    )


@app.route("/api/v1/findTrackingByConcertid/<string:concert_id>/<string:category>")
def findTrackingByConcertid(concert_id, category):
    concertTracking = db.session.scalars(
        db.select(ConcertTracking)
        .filter_by(concert_id=concert_id, category=category)
        .limit(1)
    ).first()

    if concertTracking:
        return jsonify({"code": 200, "data": concertTracking.json()})
    return jsonify({"code": 404, "message": "Concert tracking not found."}), 404


@app.route(
    "/api/v1/createTracking/<string:concert_id>/<string:category>", methods=["POST"]
)
def createTracking(concert_id, category):

    concert_id = request.json.get("concert_id", None)
    category = request.json.get("category", None)
    tracking = ConcertTracking(concert_id=concert_id, category=category, takenSeats=0)

    try:
        db.session.add(tracking)
        db.session.commit()
    except Exception as e:
        return (
            jsonify(
                {
                    "code": 500,
                    "message": "An error occurred while creating the tracking record. "
                    + str(e),
                }
            ),
            500,
        )

    return jsonify({"code": 201, "data": tracking.json()}), 201


@app.route(
    "/api/v1/updateNumTakenSeats/<string:concert_id>/<string:category>/<string:seat_no>",
    methods=["PUT"],
)
def updateNumTakenSeats(concert_id, category, seat_no):
    try:
        tracking = db.session.scalars(
            db.select(ConcertTracking)
            .filter_by(concert_id=concert_id, category=category)
            .limit(1)
        ).first()
        if not tracking:
            return (
                jsonify(
                    {
                        "code": 404,
                        "data": {"concert_id": concert_id, "category": category},
                        "message": "Concert not found.",
                    }
                ),
                404,
            )

        data = request.get_json()
        if "takenSeats" in data:
            list_seat_numbers = seat_no.split(",")
            num_seats_taken = len(list_seat_numbers)
            current_taken_seats = ConcertTracking.query.first().takenSeats
            new_taken_seats = current_taken_seats + num_seats_taken
            ConcertTracking.takenSeats = new_taken_seats
            db.session.commit()
            return jsonify({"code": 200, "data": {"takenSeats": new_taken_seats}}), 200
    except Exception as e:
        return (
            jsonify(
                {
                    "code": 500,
                    "data": {"concert_id": concert_id, "category": category},
                    "message": "An error occurred while updating the number of seats taken. "
                    + str(e),
                }
            ),
            500,
        )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=True)
