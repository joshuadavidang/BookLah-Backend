import amqp_setup
import json
import pika

e_queue_name = 'Error'        

def receiveError(channel):
    try:
        channel.basic_consume(queue=e_queue_name, on_message_callback=callback, auto_ack=True)
        print('error microservice: Consuming from queue:', e_queue_name)
        channel.start_consuming()
    
    except pika.exceptions.AMQPError as e:
        print(f"error microservice: Failed to connect: {e}") 

    except KeyboardInterrupt:
        print("error microservice: Program interrupted by user.")

def callback(channel, method, properties, body): 
    print("\nerror microservice: Received an error by " + __file__)
    processError(body)
    print()

def processError(errorMsg):
    print("error microservice: Printing the error message:")
    try:
        error = json.loads(errorMsg)
        print("--JSON:", error)
    except Exception as e:
        print("--NOT JSON:", e)
        print("--DATA:", errorMsg)
    print()

if __name__ == "__main__": 
    print("error microservice: Getting Connection")
    connection = amqp_connection.create_connection() 
    print("error microservice: Connection established successfully")
    channel = connection.channel()
    receiveError(channel)
