from kafka import KafkaProducer
import json
import time
import random

producer = KafkaProducer(bootstrap_servers="localhost:9092", value_serializer=lambda v: json.dumps(v).encode('utf-8'))

def producer_prices():
    # new_price = get_new_market_price()
    new_prices = [90, 100, 105, 90]
    for new_price in new_prices:
        producer.send('new_price',{'price': new_price})
        producer.flush()
        time.sleep(1) # wait 1 seconds before sending the next price update


if __name__ == '__main__':
    producer_prices()