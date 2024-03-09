from flask import request, jsonify
from dbConfig import app, db, PORT
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import stripe

# /api/v1/getConcerts
# /api/v1/getConcert
# /api/v1/isConcertSoldOut/<string:concertid>
# /api/v1/getAdminCreatedConcert
# /api/v1/addConcert/<string:concertid>
# /api/v1/deleteConcert/<string:concertid>


class Concert(db.Model):
    __tablename__ = "concert"
    concertid = db.Column(UUID(as_uuid=True), primary_key=True)
    performer = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    venue = db.Column(db.String(150), nullable=False)
    date = db.Column(db.String, nullable=False)
    time = db.Column(db.String, nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(1000), nullable=False)
    sold_out = db.Column(db.Boolean, nullable=False, default=False)
    price = db.Column(db.INTEGER, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    created_by = db.Column(db.String(50), nullable=False)

    def __init__(
        self,
        concertid,
        performer,
        title,
        venue,
        date,
        time,
        capacity,
        price,
        description,
        created_by,
    ):
        self.concertid = concertid
        self.performer = performer
        self.title = title
        self.venue = venue
        self.date = date
        self.time = time
        self.capacity = capacity
        self.price = price
        self.description = description
        self.created_by = created_by

    def json(self):
        return {
            "concertid": self.concertid,
            "performer": self.performer,
            "title": self.title,
            "venue": self.venue,
            "date": self.date,
            "time": self.time,
            "capacity": self.capacity,
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


@app.route("/api/v1/getConcert/<string:concertid>")
def getConcert(concertid):

    concert = db.session.scalars(
        db.select(Concert).filter_by(concertid=concertid).limit(1)
    ).first()

    if not concert:
        return jsonify({"code": 404, "message": "concert not found."}), 404

    return jsonify({"code": 200, "data": concert.json()})


@app.route("/api/v1/isConcertSoldOut/<string:concertid>")
def isConcertSoldOut(concertid):
    concert = db.session.query(Concert).filter_by(concertid=concertid).first()
    if not concert:
        return jsonify({"code": 404, "message": "concert not found."}), 404

    return jsonify(
        {
            "code": 200,
            "data": {"concertid": concert.concertid, "sold_out": concert.sold_out},
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


@app.route("/api/v1/addConcert/<string:concertid>", methods=["POST"])
def addConcert(concertid):
    if db.session.scalars(
        db.select(Concert).filter_by(concertid=concertid).limit(1)
    ).first():
        return (
            jsonify(
                {
                    "code": 400,
                    "data": {"concertid": concertid},
                    "message": "Concert already exists.",
                }
            ),
            400,
        )

    data = request.get_json()
    concert = Concert(concertid, **data)

    try:
        db.session.add(concert)
        db.session.commit()
    except:
        return (
            jsonify(
                {
                    "code": 500,
                    "data": {"concertid": concertid},
                    "message": "An error occurred creating the concert.",
                }
            ),
            500,
        )

    return jsonify({"code": 201, "data": concert.json()}), 201


@app.route("/api/v1/deleteConcert/<string:concertid>", methods=["DELETE"])
def deleteConcert(concertid):
    concert = db.session.query(Concert).filter_by(concertid=concertid).first()
    if not concert:
        return jsonify(
            {
                "code": 404,
                "data": {"concertid": concertid},
                "message": "Concert not found.",
            }
        )

    try:
        db.session.delete(concert)
        db.session.commit()
        return (
            jsonify(
                {
                    "code": 200,
                    "data": {"concertid": concertid},
                    "message": "Concert deleted successfully.",
                }
            ),
            200,
        )
    except:
        return (
            jsonify(
                {
                    "code": 500,
                    "data": {"concertid": concertid},
                    "message": "An error occurred while deleting the concert.",
                }
            ),
            500,
        )


class Product(db.Model):
    __tablename__ = "product"
    concertid = db.Column(UUID(as_uuid=True), primary_key=True)
    price = db.Column(db.INTEGER, nullable=False)

    def __init__(self, concertid, price):
        self.concertid = concertid
        self.price = price

    def json(self):
        return {"concertid": self.concertid, "price": self.price}


@app.route("/api/v1/addProductToStripe", methods=["POST"])
def addProductToStripe():
    data = request.get_json()
    name = data["name"]
    price = data["price"]

    product = stripe.Price.create(
        currency="sgd", unit_amount=(price * 100), product_data={"name": name}
    )

    return jsonify({"code": 201, "data": product}), 201


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=True)
