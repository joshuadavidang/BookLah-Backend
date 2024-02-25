from flask import Flask
from flask_cors import CORS
from config import init_db
from flask import jsonify

app = Flask(__name__)
PORT = 5001
CORS(app, supports_credentials=True)


def fetch_data_as_json():
    conn = init_db.getDbConnection()
    cur = conn.cursor()
    query = "SELECT * FROM concerts;"
    cur.execute(query)
    columns = [desc[0] for desc in cur.description]
    rows = cur.fetchall()
    data = []
    for row in rows:
        data.append(dict(zip(columns, row)))
    cur.close()
    conn.close()

    return data


@app.route("/getConcerts")
def getConcerts():
    data = fetch_data_as_json()
    return (
        jsonify({"code": 200, "message": "List of concerts fetched!", "data": data}),
        200,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=True)
