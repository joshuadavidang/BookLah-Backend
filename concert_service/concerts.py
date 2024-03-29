from flask import request, jsonify
from dbConfig import app, db, PORT
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Enum
from datetime import datetime

######## 8 ENDPOINTS ########

# /api/v1/getConcerts
# /api/v1/getConcert/<string:concert_id>
# /api/v1/isConcertSoldOut/<string:concert_id>
# /api/v1/updateTicketStatus/<string:concert_id>
# /api/v1/getAdminCreatedConcert/<string:userId>
# /api/v1/addConcert/<string:concert_id>
# /api/v1/updateConcertAvailability/<string:concert_id>
# /api/v1/updateConcertDetails/<string:concert_id>


class Concert(db.Model):
    __tablename__ = "concert"
    concert_id = db.Column(UUID(as_uuid=True), primary_key=True)
    performer = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    venue = db.Column(db.String(150), nullable=False)
    date = db.Column(db.String, nullable=False)
    time = db.Column(db.String, nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(1000), nullable=False)
    sold_out = db.Column(db.Boolean, nullable=False, default=False)
    price = db.Column(db.INTEGER, nullable=False, default=0)
    concert_status = db.Column(
        Enum("AVAILABLE", "CANCELLED", name="concert_status_enum"),
        nullable=False,
        default="AVAILABLE",
    )
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now())
    created_by = db.Column(db.String(50), nullable=False)

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


@app.route("/api/v1/isConcertSoldOut/<string:concert_id>")
def isConcertSoldOut(concert_id):
    concert = db.session.query(Concert).filter_by(concert_id=concert_id).first()
    if not concert:
        return jsonify({"code": 404, "message": "concert not found."}), 404

    return jsonify(
        {
            "code": 200,
            "data": {"concert_id": concert.concert_id, "sold_out": concert.sold_out},
        }
    )


@app.route("/api/v1/updateTicketStatus/<string:concert_id>", methods=["PUT"])
def updateTicketStatus(concert_id):
    """
    Update Ticket Status
    isSoldOut = True if sold out
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

    isSoldOut = request.get_json()["isSoldOut"]

    try:
        db.session.query(Concert).filter_by(concert_id=concert_id).update(
            {"sold_out": isSoldOut}
        )
        db.session.commit()
        return (
            jsonify(
                {
                    "code": 200,
                    "data": {"concert_id": concert_id},
                    "message": "Updated concert ticket status successfully.",
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
                    "message": "An error occurred while updating the ticket status",
                }
            ),
            500,
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=True)
