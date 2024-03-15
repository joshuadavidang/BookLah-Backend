# test_invoke_http.py
from invokes import invoke_http

# invoke book microservice to get all books
results = invoke_http("http://localhost:5001/getConcerts", method='GET')

# # invoke book microservice to create a book
# isbn = '9213213213213'
# book_details = { "availability": 5, "price": 213.00, "title": "ESD" }
# create_results = invoke_http(
#         "http://localhost:5000/book/" + isbn, method='POST', 
#         json=book_details
#     )

# print( create_results )
# print()
print( type(results) )
print()
print( results )
