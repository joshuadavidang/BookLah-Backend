import time
import pika
import uuid

hostname = "host.docker.internal"
port = 5006


# function to create a connection to the broker
def create_connection(correlation_id=None, max_retries=12, retry_interval=5):
    print("amqp_connection: Create_connection")

    retries = 0
    connection = None

    while retries < max_retries:
        try:
            print("amqp_connection: Trying connection")
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=hostname,
                    port=port,
                    heartbeat=3600,
                    blocked_connection_timeout=3600,
                )
            )
            print("amqp_connection: Connection established successfully")
            break
        except pika.exceptions.AMQPConnectionError as e:
            print(f"amqp_connection: Failed to connect: {e}")
            retries += 1
            print(f"amqp_connection: Retrying in {retry_interval} seconds...")
            time.sleep(retry_interval)

    if connection is None:
        raise Exception(
            "Unable to establish a connection to RabbitMQ after multiple attempts"
        )

    if correlation_id:
        return connection, correlation_id
    else:
        return connection


# function to check if the exchange exists
def check_exchange(channel, exchangename, exchangetype):
    try:
        channel.exchange_declare(exchangename, exchangetype, durable=True, passive=True)
    except Exception as e:
        print("Exception:", e)
        return False
    return True


if __name__ == "__main__":
    correlation_id = str(uuid.uuid4())
    connection, correlation_id = create_connection(correlation_id=correlation_id)
    print(f"Connection: {connection}")
    print(f"Correlation ID: {correlation_id}")
