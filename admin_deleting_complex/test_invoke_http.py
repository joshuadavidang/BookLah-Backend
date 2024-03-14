# test_invoke_http.py
from invokes import invoke_http

# invoke book microservice to get all books
results = invoke_http("http://localhost:5001/booking", method='GET')

print( type(results) )
print()
print( results )

# invoke book microservice to create a book
booking_id='999'
booking_details = {
    "user_id": 123,
    "concert_id": 1989,
    "price": 50,
    "cat_number": "1",
    "seat_numbers": ["Z1", "Z2", "Z3"],
    "quantity": 3 }
create_results = invoke_http(
        "http://localhost:5001/booking/", method='POST', 
        json=booking_details
    )

print()
print( create_results )
