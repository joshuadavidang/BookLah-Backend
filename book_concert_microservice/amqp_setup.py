import time
import pika

hostname = "localhost"
port = 5672
exchangename = "booking_topic"
exchangetype = "topic"


def create_connection(max_retries=12, retry_interval=5):
    print("amqp_setup:create_connection")

    retries = 0
    connection = None

    while retries < max_retries:
        try:
            print("amqp_setup: Trying connection")
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=hostname,
                    port=port,
                    heartbeat=3600,
                    blocked_connection_timeout=3600,
                )
            )
            print("amqp_setup: Connection established successfully")
            break
        except pika.exceptions.AMQPConnectionError as e:
            print(f"amqp_setup: Failed to connect: {e}")
            retries += 1
            print(f"amqp_setup: Retrying in {retry_interval} seconds...")
            time.sleep(retry_interval)

    if connection is None:
        raise Exception(
            "amqp_setup: Unable to establish a connection to RabbitMQ after multiple attempts."
        )

    return connection


def create_channel(connection):
    print("amqp_setup:create_channel")
    channel = connection.channel()
    print("amqp_setup:create exchange")
    channel.exchange_declare(
        exchange=exchangename, exchange_type=exchangetype, durable=True
    )
    return channel


def create_queues(channel):
    print("amqp_setup:create queues")
    create_error_queue(channel)
    create_activity_log_queue(channel)


def create_activity_log_queue(channel):
    print("amqp_setup:create_activity_log_queue")
    a_queue_name = "Activity_Log"
    channel.queue_declare(queue=a_queue_name, durable=True)
    channel.queue_bind(exchange=exchangename, queue=a_queue_name, routing_key="#")


def create_error_queue(channel):
    print("amqp_setup:create_error_queue")
    e_queue_name = "Error"
    channel.queue_declare(queue=e_queue_name, durable=True)
    channel.queue_bind(exchange=exchangename, queue=e_queue_name, routing_key="*.error")


if __name__ == "__main__":
    connection = create_connection()
    channel = create_channel(connection)
    create_queues(channel)
