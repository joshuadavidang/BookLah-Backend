# test_invoke_http.py
from invokes import invoke_http
import json

# invoke book microservice to get all books
results = invoke_http("http://localhost:5001/api/v1/booking", method="GET")

print(type(results))
print()
print(results)

# invoke book microservice to create a book

seat_numbers = ["Z1", "Z2", "Z3"]
seat_numbers_str = ",".join(seat_numbers)

booking_details = {
    "booking_id": 887,
    "user_id": 123,
    "concert_id": 1989,
    "price": 50,
    "cat_number": "1",
    "seat_numbers": seat_numbers_str,  # Convert list to comma-separated string
    "quantity": len(seat_numbers),
}

create_results = invoke_http(
    "http://localhost:5001/api/v1/booking", method="POST", json=booking_details
)

print()
print(create_results)
