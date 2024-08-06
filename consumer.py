import pika

def consume_messages():
    #Consume messages from the specified RabbitMQ queue
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    # Declare the queue with durable=True
    channel.queue_declare(queue='population_updates', durable=True)

    def callback(ch, method, properties, body):
        print(f" [x] Received {body.decode()}")
        # Process the message
        ch.basic_ack(delivery_tag=method.delivery_tag)

    # Consume messages
    channel.basic_consume(queue='population_updates', on_message_callback=callback)

    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

if __name__ == '__main__':
    consume_messages()


