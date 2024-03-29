import time
import pika
from pika.exceptions import ChannelClosed, AMQPConnectionError

hostname = "localhost"
port = 5672
exchangename = "forum_topic"
exchangetype = "topic"


def create_connection(max_retries=12, retry_interval=5):
    retries = 0
    connection = None

    while retries < max_retries:
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=hostname,
                    port=port,
                    heartbeat=3600,
                    blocked_connection_timeout=3600,
                )
            )
            channel = connection.channel()
            channel.exchange_declare(
                exchange=exchangename, exchange_type=exchangetype, durable=True
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
    channel = connection.channel()
    return channel


def create_queues(channel):
    create_error_queue(channel)
    create_activity_log_queue(channel)

    queue_name = 'forum_queue'
    channel.queue_declare(queue=queue_name, durable=True)
    channel.queue_bind(exchange=exchangename, queue=queue_name, routing_key="forum.info")


def create_activity_log_queue(channel):
    a_queue_name = "Activity_Log"
    channel.queue_declare(
        queue=a_queue_name, durable=True
    )
    channel.queue_bind(exchange=exchangename, queue=a_queue_name, routing_key="#")


def create_error_queue(channel):
    e_queue_name = "Error"
    channel.queue_declare(queue=e_queue_name, durable=True)
    channel.queue_bind(exchange=exchangename, queue=e_queue_name, routing_key="*.error")


def check_queue_exists(channel, queue_name):
    try:
        channel.queue_declare(queue=queue_name, passive=True)
        print(f"Queue '{queue_name}' already exists.")
    except ChannelClosed:
        print(f"Queue '{queue_name}' does not exist.")


def check_exchange(channel, exchangename, exchangetype):
    try:
        channel.exchange_declare(exchangename, exchangetype, durable=True, passive=True)
    except Exception as e:
        print("Exception:", e)
        return False
    return True


if __name__ == "__main__":
    connection = create_connection()
    channel = create_channel(connection)
    create_queues(channel)

