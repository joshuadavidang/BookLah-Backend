import os
import psycopg2


def getDbConnection():
    conn = psycopg2.connect(
        host="localhost",
        database="shortensg-users",
        user=os.environ["DB_USERNAME"],
        password=os.environ["DB_PASSWORD"],
    )
    return conn


conn = getDbConnection()
cur = conn.cursor()

cur.execute("DROP TABLE IF EXISTS concerts;")
cur.execute("DROP TYPE IF EXISTS concert_type_enum;")
cur.execute("CREATE TYPE concert_type_enum AS ENUM ('SOLO', 'GROUP');")
cur.execute(
    "CREATE TABLE concerts (id serial PRIMARY KEY,"
    "performer varchar(50) NOT NULL,"
    "concertName varchar(150) NOT NULL,"
    "concertVenue varchar(150) NOT NULL,"
    "concertDate varchar(150) NOT NULL,"
    "concertCapacity integer NOT NULL,"
    "concertType concert_type_enum NOT NULL,"
    "date_added date DEFAULT CURRENT_TIMESTAMP);"
)

cur.execute(
    "INSERT INTO concerts (performer, concertName, concertVenue, concertDate, concertCapacity, concertType)"
    "VALUES (%s, %s, %s, %s, %s, %s )",
    (
        "Ed Sheeran",
        "Mathematics Tour",
        "Singapore National Stadium",
        "2024-03-01",
        1000,
        "SOLO",
    ),
)

cur.execute(
    "INSERT INTO concerts (performer, concertName, concertVenue, concertDate, concertCapacity, concertType)"
    "VALUES (%s, %s, %s, %s, %s, %s )",
    ("JJ Lin", "Concert Name", "SMU", "2024-03-01", 1000, "SOLO"),
)

conn.commit()
cur.close()
conn.close()
