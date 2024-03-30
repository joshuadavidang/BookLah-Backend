-- SQL SCRIPT TO CREATE CONCERT TABLE --
CREATE DATABASE concertdb;
DROP TABLE IF EXISTS CONCERT;
DROP TYPE IF EXISTS concert_status_enum;
CREATE TYPE concert_status_enum AS ENUM ('AVAILABLE', 'CANCELLED');
CREATE TABLE concert (
  concert_id UUID PRIMARY KEY,
  performer VARCHAR(50) NOT NULL,
  title VARCHAR(255) NOT NULL,
  venue VARCHAR(255) NOT NULL,
  date VARCHAR(100) NOT NULL,
  time VARCHAR(100) NOT NULL,
  capacity INTEGER NOT NULL,
  description VARCHAR(1000) NOT NULL,
  sold_out BOOLEAN NOT NULL DEFAULT FALSE,
  price INTEGER NOT NULL DEFAULT 0,
  concert_status concert_status_enum NOT NULL DEFAULT 'AVAILABLE',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  created_by VARCHAR(100) NOT NULL
);

-- SQL SCRIPT TO CREATE SEATS TABLE--
CREATE TABLE seats (
    concert_id VARCHAR(50) NOT NULL,
    category VARCHAR(50) NOT NULL,
    seat_number INT NOT NULL,
    taken BOOLEAN NOT NULL,
    PRIMARY KEY (concert_id, seat_number)
);

--SQL SCRIPT TO CREATE TACKING TABLE--
CREATE TABLE tracking (
    concert_id VARCHAR(50) NOT NULL,
    category VARCHAR(50) NOT NULL,
    capacity INT NOT NULL,
    takenSeats INT NOT NULL,
    PRIMARY KEY (concert_id, category)
);