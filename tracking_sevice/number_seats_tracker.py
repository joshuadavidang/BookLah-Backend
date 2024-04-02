from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root@localhost:3306/events'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db = SQLAlchemy(app)


class Event(db.Model):
    __tablename__ = 'events'


    eventNo = db.Column(db.String(3), primary_key=True)
    title = db.Column(db.String(64), nullable=False)
    price = db.Column(db.Float(precision=2), nullable=False)
    availability = db.Column(db.Integer)


    def __init__(self, eventNo, title, price, availability):
        self.eventNo = eventNo
        self.title = title
        self.price = price
        self.availability = availability


    def json(self):
        return {"eventNo": self.eventNo, "title": self.title, "price": self.price, "availability": self.availability}


@app.route("/events")
def get_all():
    eventlist = db.session.scalars(db.select(Event)).all()


    if len(eventlist):
        return jsonify(
            {
                "code": 200,
                "data": {
                    "events": [event.json() for event in eventlist]
                }
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": "There are no events."
        }
    ), 404



@app.route("/events/<string:eventNo>")
def find_by_event(eventNo):
    event = db.session.scalars(
    	db.select(Event).filter_by(eventNo=eventNo).
    	limit(1)
).first()


    if event:
        return jsonify(
            {
                "code": 200,
                "data": event.json()
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": "Event not found."
        }
    ), 404



@app.route("/events/<string:eventNo>", methods=['POST'])
def create_event(eventNo):
    if (db.session.scalars(
      db.select(Event).filter_by(eventNo=eventNo).
      limit(1)
      ).first()
    ):
        return jsonify(
            {
                "code": 400,
                "data": {
                    "eventNo": eventNo
                },
                "message": "Event already exists."
            }
        ), 400


    data = request.get_json()
    event = Event(eventNo, **data)


    try:
        db.session.add(event)
        db.session.commit()
    except:
        return jsonify(
            {
                "code": 500,
                "data": {
                    "eventNo": eventNo
                },
                "message": "An error occurred creating the event."
            }
        ), 500


    return jsonify(
        {
            "code": 201,
            "data": event.json()
        }
    ), 201

@app.route("/events/<string:eventNo>", methods=['PATCH'])
def update_event(eventNo):
    event = Event.query.get(eventNo)

    if not event:
        return jsonify({'message': 'Event not found'}), 404

    data = request.get_json()
    newAvailability = data.get('availability')
    if newAvailability is not None:
        event.availability = newAvailability
        db.session.commit()
        return jsonify({'message': f'Availability for Event {eventNo} updated successfully'})
    
    return jsonify({'message': 'Invalid data provided'}), 400

if __name__ == '__main__':
    app.run(port=5000, debug=True)
