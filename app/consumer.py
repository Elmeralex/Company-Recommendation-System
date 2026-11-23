import argparse
import os
from typing_extensions import Final

import pika #Get the pika library for RabbitMQ communication
import app.normalization as normalization #Import the normalization module
import app.db as db #Import the database module

QUEUE: Final = "company-events"
RABBITMQ_URL: Final = os.environ.get("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/") #Setu p the RabbitMQ URL from environment variable

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

    conn = db.connect() #Connect to the database using the database module
    db.create_tables(conn) #Create the tables in the database

    for method_frame, properties, body in channel.consume(QUEUE, inactivity_timeout=1):
        if method_frame is None:
            break

        #display method_frame
        print(f"Method Frame: {method_frame} \nProperties: {properties} \n")

        result = normalization.message_validation(body) #Normalize and validate the message using the normalization module
        if result["status"] == "saved":
            print(f"Message is valid: {result['data']}")
            verify_storage = db.get_updated_at(conn, result["data"]["registrationnumber"])

            description_hash = normalization.get_description_hash(result["data"]["data"]["natureofbusiness"]) 
            embedding = normalization.get_embedding(result["data"]["data"]["natureofbusiness"]) #Get the embedding for the nature of business using the normalization module
            
            if verify_storage is None: #Check if the company already exists in the database
                db.insert_company(conn, result["data"], description_hash, embedding, properties.message_id) #Insert the valid message into the database using the database module
            else:
                if verify_storage < result["data"]["updatedat"]: #Check if the new message is newer than the existing one
                    db.update_company(conn, result["data"], description_hash, embedding, properties.message_id) #Update the existing company in the database using the database module (only if the new message is newer than the existing one)
                    print(f"Message is valid and updated: {result['data']['registrationnumber']}")
        else:
            print(f"Message is invalid: {result['status']}") #If the status is not, ensure the program still can continue to process the next message without crashing or stopping the program
            continue

        conn.commit()
        if args.read:
            channel.basic_ack(delivery_tag=method_frame.delivery_tag)

    #Close the channel and connection
    channel.cancel()
    connection.close()
    conn.close()

if __name__ == "__main__":
    main()