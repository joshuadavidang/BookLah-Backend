from flask import request, jsonify
from dbConfig import app, db, PORT


class Events(db.Model):
    __tablename__ = "concert"
    concertid = db.Column(db.Integer, primary_key=True)
    performer = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    venue = db.Column(db.String(150), nullable=False)
    date = db.Column(db.String(150), nullable=False)
    time = db.Column(db.String(50), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(1000), nullable=False)

    def __init__(
        self,
        concertid,
        performer,
        title,
        venue,
        date,
        time,
        capacity,
        description,
    ):
        self.concertid = concertid
        self.performer = performer
        self.title = title
        self.venue = venue
        self.date = date
        self.time = time
        self.capacity = capacity
        self.description = description

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
        }


@app.route("/getConcerts")
def getConcerts():
    concerts = db.session.scalars(db.select(Events)).all()

    if len(concerts):
        return jsonify(
            {
                "code": 200,
                "data": {"concerts": [concert.json() for concert in concerts]},
            }
        )
    return jsonify({"code": 404, "message": "There are no concerts."}), 404


@app.route("/getConcert/<string:concertid>")
def getConcert(concertid):

    concert = db.session.scalars(
        db.select(Events).filter_by(concertid=concertid).limit(1)
    ).first()

    if concert:
        return jsonify({"code": 200, "data": concert.json()})
    return jsonify({"code": 404, "message": "concert not found."}), 404


@app.route("/addConcert/<string:concertid>", methods=["POST"])
def addConcert(concertid):
    if db.session.scalars(
        db.select(Events).filter_by(concertid=concertid).limit(1)
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
    concert = Events(concertid, **data)

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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=True)
