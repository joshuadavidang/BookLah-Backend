import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()


def getDbConnection():
    conn = psycopg2.connect(
        host="localhost",
        database=os.getenv("DATABASE"),
        user=os.getenv("DB_USERNAME"),
        password=os.getenv("DB_PASSWORD"),
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
    "title varchar(150) NOT NULL,"
    "venue varchar(150) NOT NULL,"
    "date varchar(150) NOT NULL,"
    "time varchar(50) NOT NULL,"
    "capacity integer NOT NULL,"
    "type concert_type_enum NOT NULL,"
    "date_added date DEFAULT CURRENT_TIMESTAMP);"
)


def insert_concert(cur, performer, title, venue, date, time, capacity, concert_type):
    script = """
        INSERT INTO concerts (performer, title, venue, date, time, capacity, type)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    values = (performer, title, venue, date, time, capacity, concert_type)
    cur.execute(script, values)


insert_concert(
    cur,
    "Ed Sheeran",
    "Mathematics Tour",
    "Singapore National Stadium",
    "5 May 2024",
    "8:00 PM",
    1000,
    "SOLO",
)

insert_concert(
    cur,
    "JJ Lin",
    "JJ24 world tour",
    "Singapore Sports Hub",
    "3 Mar 2024",
    "7:30 PM",
    1000,
    "SOLO",
)

conn.commit()
cur.close()
conn.close()
