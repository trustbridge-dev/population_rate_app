import pika

def consume_messages():
    #Consume messages from the RabbitMQ queue.
    # Connect to RabbitMQ
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    # Declare a queue
    channel.queue_declare(queue='population_updates')

    # Callback function to process messages
    def callback(ch, method, properties, body):
        print(f"Received message: {body.decode()}")

    # Start consuming messages
    channel.basic_consume(queue='population_updates', on_message_callback=callback, auto_ack=True)

    print('Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

if __name__ == '__main__':
    consume_messages()

