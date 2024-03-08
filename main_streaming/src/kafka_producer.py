from kafka import KafkaProducer
import time
from json import dumps
import random
from configparser import ConfigParser
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider

 
conf_file_name = "config.conf"
config_obj = ConfigParser()
config_read_obj = config_obj.read(conf_file_name)

kafka_host_name = config_obj.get('kafka', 'host')
kafka_port_no = config_obj.get('kafka', 'port_no')
kafka_topic_name = config_obj.get('kafka', 'streamorder')

KAFKA_TOPIC_NAME_CONS = kafka_topic_name
KAFKA_BOOTSTRAP_SERVERS_CONS = kafka_host_name + ':' + kafka_port_no

kafka_producer_obj = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS_CONS,
    value_serializer=lambda x: dumps(x).encode('utf-8'),
    batch_size=46384,  # Adjust based on your requirement
    linger_ms=1,  # Adjust based on your requirement
    compression_type='gzip'  # Options: 'gzip', 'snappy', 'lz4', 'zstd'
)

def get_order_uuid():
    auth_provider = PlainTextAuthProvider(username='admin', password='chitoge1234')
    cluster = Cluster(['127.0.0.1'], port=9042, auth_provider=auth_provider)
    session = cluster.connect('trading_data')    
    query = "SELECT uuid FROM orders WHERE is_matched = false ALLOW FILTERING"
    rows = session.execute(query)
    return [str(row.uuid) for row in rows]

def generate_price():
    # Simulate price fluctuation
    base_price = 80
    fluctuation = round(random.uniform(-5,5))
    price = base_price + fluctuation
    return price

def send_price_update(producer, price, uuids):
    for uuid in uuids:
        message = {'price': price, 'uuid': uuid}
        producer.send(KAFKA_TOPIC_NAME_CONS, message)

if __name__ == "__main__":
    print("Kafka Price Generator Started ... ")
    
    kafka_producer_obj = KafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS_CONS,value_serializer=lambda x: dumps(x).encode('utf-8'))
    try:
        while True:
            current_price = generate_price()  # Generate one price for all orders
            order_uuids = get_order_uuid()    # Get all order UUIDs
            send_price_update(kafka_producer_obj, current_price, order_uuids)
            print(f"Sending price update: {current_price}")
            time.sleep(10)  # Sleep for some time before sending the next update
    except KeyboardInterrupt:
        print("\nKafka Price Generator Stopped.")
    print("Kafka Producer Application Completed.")
