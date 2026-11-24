import os
from typing_extensions import Final

import pika #Get the pika library for RabbitMQ communication
import app.normalization as normalization #Import the normalization module
import app.db as db #Import the database module

QUEUE: Final = "company-events"
RABBITMQ_URL: Final = os.environ.get("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/") #Setu p the RabbitMQ URL from environment variable

def running_consumer(conn, body, message_id):
    result = normalization.message_validation(body) #Normalize and validate the message using the normalization module
    
    if result["status"] == "saved":
        print(f"Message is valid: {result['data']}")
        
        verify_storage = db.get_updated_at(conn, result["data"]["registrationnumber"])
        description_hash = normalization.get_description_hash(result["data"]["data"]["natureofbusiness"]) 
        
        embedding = db.find_embedding_by_hash(conn, description_hash) or normalization.get_embedding(result["data"]["data"]["natureofbusiness"]) #Check if the embedding already exists in the database, if not, generate a new embedding using the normalization module
        
        if verify_storage is None: #Check if the company already exists in the database
            db.insert_company(conn, result["data"], description_hash, embedding, message_id) #Insert the valid message into the database using the database module
        else:
            if verify_storage < result["data"]["updatedat"]: #Check if the new message is newer than the existing one
                db.update_company(conn, result["data"], description_hash, embedding, message_id) #Update the existing company in the database using the database module (only if the new message is newer than the existing one)
                print(f"Message is valid and updated: {result['data']['registrationnumber']}")
    else:
        print(f"Message is invalid: {result['status']}") #If the status is not, ensure the program still can continue to process the next message without crashing or stopping the program

    conn.commit()


def main() -> None:
    normalization.get_model()  #Load the model
    conn = db.connect() #Connect to the database using the database module
    db.create_tables(conn) #Create the tables in the database
    
    #Connect and open a channel 
    connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE, durable=True) #Declare the queue to ensure it exists
    channel.basic_qos(prefetch_count=50) #Limit the number of unacknowledged messages to 50 to avoid overwhelming the consumer

    #Better handling the exception and close the connection
    try:
        for method_frame, properties, body in channel.consume(QUEUE):
            try:
                    running_consumer(conn, body, properties.message_id)
                    channel.basic_ack(delivery_tag=method_frame.delivery_tag)
            except Exception as e:
                print(f"Error occurred while processing message: {e}")
                channel.basic_nack(delivery_tag=method_frame.delivery_tag, requeue=True)
    except KeyboardInterrupt:
        print("Consumer interrupted. Exiting...")
        pass
    finally:
        #Close the channel and connection
        channel.cancel()
        connection.close()
        conn.close()

if __name__ == "__main__":
    main()