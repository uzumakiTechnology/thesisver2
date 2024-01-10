from kafka import KafkaProducer
import json
import time
import random

producer = KafkaProducer(bootstrap_servers="localhost:9092", value_serializer=lambda v: json.dumps(v).encode('utf-8'))

def producer_prices():
    new_prices = [90]
    for new_price in new_prices:
        producer.send('new_price',{'price': new_price})
        producer.flush()


if __name__ == '__main__':
    producer_prices()