from kafka import KafkaProducer
import json
import time

producer = KafkaProducer(bootstrap_servers="localhost:9092", value_serializer=lambda v: json.dumps(v).encode('utf-8'))

def producer_prices():
    new_prices = [85,90,95,90,85,80]
    for new_price in new_prices:
        producer.send('new_price',{'price': new_price})
        producer.flush()
        time.sleep(1)  # Sleep for a second


if __name__ == '__main__':
    producer_prices()

    