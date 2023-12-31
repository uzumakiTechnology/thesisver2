from kafka import KafkaProducer
import json

producer = KafkaProducer(bootstrap_servers='localhost:9092')
priceList = [100,90,110]

def kafkaSend():
    for price in priceList: 
        data={
            "price":price
        }
        producer.send("new_price",json.dumps(data).encode("utf8"))
        producer.flush()



if __name__ == '__main__':
        kafkaSend()