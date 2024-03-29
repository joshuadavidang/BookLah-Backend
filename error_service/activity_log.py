import error_service.amqp_setup as amqp_setup
import json
import pika

a_queue_name = "Activity_Log"


def receiveBookingLog(channel):
    try:
        channel.basic_consume(
            queue=a_queue_name, on_message_callback=callback, auto_ack=True
        )
        print("activity_log: Consuming from queue:", a_queue_name)
        channel.start_consuming()

    except pika.exceptions.AMQPError as e:
        print(f"activity_log: Failed to connect: {e}")

    except KeyboardInterrupt:
        print("activity_log: Program interrupted by user.")


def callback(channel, method, properties, body):
    print("\nactivity_log: Received an booking log by " + __file__)
    processBookingLog(json.loads(body))
    print()


def processBookingLog(booking):
    print("activity_log: Recording an booking log:")
    print(booking)


if __name__ == "__main__":
    print("activity_log: Getting Connection")
    connection = amqp_setup.create_connection()
    print("activity_log: Connection established successfully")
    channel = connection.channel()
    receiveBookingLog(channel)
