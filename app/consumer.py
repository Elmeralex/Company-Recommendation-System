import argparse
import json
import os
from typing_extensions import Final
import warnings

import pika #Get the pika library for RabbitMQ communication

QUEUE: Final = "company-events"
RABBITMQ_URL: Final = os.environ.get("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/") #Setu p the RabbitMQ URL from environment variable

def message_validation(body: bytes) -> str:
    """Return a status for one raw message. Rough checks for exploring only."""
    try:
        event = json.loads(body)
    except json.JSONDecodeError:
        return "bad-json"

    if not isinstance(event, dict):  #the body is null skip
        return "skip"
    if event.get("registrationNumber") is None: #the register number is null skip
        return "skip"
    return "saved"

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--read", action="store_true", help="dequeue the message from the RabbitMQ queue")
    args = parser.parse_args()

    #Connect and open a channel 
    connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
    channel = connection.channel()

    result = channel.queue_declare(queue=QUEUE, durable=True)
    print(f"{result.method.message_count} messages waiting in {QUEUE}")

    #Limit the number of message, ensure all message are read and processed before the connection is closed (Avoid because of high volume of messages cause it to be closed before all messages are processed)
    if args.read:
        channel.basic_qos(prefetch_count=50)

    for method_frame, properties, body in channel.consume(QUEUE, inactivity_timeout=1):
        if method_frame is None:
            break

        #display method_frame
        print(f"Method Frame: {method_frame} \nProperties: {properties} \nBody: {body.decode()}")

        status = message_validation(body)
        if status == "saved":
            print("Message is valid and saved.")

        if args.read:
            channel.basic_ack(delivery_tag=method_frame.delivery_tag)

    #Close the channel and connection
    channel.cancel()
    connection.close()

if __name__ == "__main__":
    main()