from flask import Flask
from flask_cors import CORS
from config import init_db
from flask import jsonify

app = Flask(__name__)
PORT = 5001
CORS(app, supports_credentials=True)


@app.route("/getConcerts")
def getConcerts():
    conn = init_db.getDbConnection()
    cursor = conn.cursor()
    query = "SELECT * FROM concerts;"
    cursor.execute(query)

    rows = cursor.fetchall()

    if rows:
        columns = [column[0] for column in cursor.description]
        concerts = [{columns[i]: row[i] for i in range(len(columns))} for row in rows]
        cursor.close()
        conn.close()
        return jsonify({"code": 200, "data": concerts}), 200

    cursor.close()
    conn.close()
    return jsonify({"code": 404, "message": "Data not found"}), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=True)
