import uuid
from fastapi import requests
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
import json
import time
from pyspark.sql.functions import when, col, lit
from pyspark.sql.functions import udf
from pyspark.sql.types import StructType, StructField, StringType, FloatType, BooleanType, IntegerType
from datetime import datetime, timedelta
from pyspark.sql.functions import greatest
from http.client import HTTPConnection
from pyspark.sql.types import StringType
from order2 import Order2  # Ensure order.py is accessible
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from cassandra.query import BatchStatement
from decimal import Decimal


def send_http_request(data):
    data['price'] = float(data['price']) if data['price'] is not None else 0.0
    conn = HTTPConnection("localhost", 8000)
    headers = {'Content-type': 'application/json'}
    conn.request("POST", "/price_update", json.dumps(data), headers)
    response = conn.getresponse()
    return response.read().decode()

# Initialize Cassandra connection
def get_cassandra_session():
    auth_provider = PlainTextAuthProvider(username='admin', password='chitoge1234')
    cluster = Cluster(['localhost'], port=9042, auth_provider=auth_provider)
    session = cluster.connect('trading_data')
    return session

send_http_request_udf = udf(send_http_request, StringType())


def main():
    cassandra_host_name = 'localhost'
    cassandra_port_no = '3306'
    cassandra_keyspace_name = 'trading_data'
    cassandra_table_name = 'orders'

    cassandra_session = get_cassandra_session()  # Get Cassandra session
    kafka_topic_name = 'streamorder'
    kafka_bootstrap_servers = 'localhost:9092'
    
    spark = SparkSession \
        .builder \
        .appName("Trailing Stop Sell Order Processing") \
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,com.datastax.spark:spark-cassandra-connector_2.12:3.1.0") \
        .config("spark.cassandra.connection.host", cassandra_host_name) \
        .master("local[*]") \
        .getOrCreate()
    
    
    spark.sparkContext.setLogLevel("ERROR")
    
    new_data_schema = StructType([
        StructField("uuid", StringType()),
        StructField("price", DecimalType())
    ])

    kafka_source_df = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", kafka_bootstrap_servers) \
        .option("subscribe", kafka_topic_name) \
        .option("startingOffsets", "latest") \
        .load()
    

    price_df = kafka_source_df.select(from_json(col("value").cast("string"), new_data_schema).alias("data")).select("data.uuid", "data.price")
    
    def update_order_logic(order_dict, new_price):
        new_price = float(new_price if new_price is not None else 0.0)
        highest_price = float(order_dict['highest_price']) if order_dict['highest_price'] is not None else 0.0

        is_matched_already = order_dict.get('is_matched', False)
        stoploss = float(order_dict.get('stoploss', 0))
        price_update_count = int(order_dict.get('price_update_count', 0))

        updated_highest_price = new_price if new_price > highest_price else highest_price
        updated_stoploss = stoploss if new_price > stoploss else new_price - float(order_dict.get('stopsize', 0))
        status = 'updated'
        selling_price = None
        evaluation_result = 'not_evaluated'

        if not is_matched_already and new_price <= updated_stoploss:
            selling_price = new_price
            status = 'matched'
            price_update_count += 1

        history_record = {
            'uuid': str(order_dict['uuid']),
            'market_price': new_price,
            'highest_price': updated_highest_price,
            'stoploss': updated_stoploss,
            'status': status,
            'evaluation_result': evaluation_result,
            'stopsize': order_dict.get('stopsize'),
            'user_id': str(order_dict.get('user_id')),
            'is_matched': status == 'matched',
            'selling_price': selling_price,
            'price_update_count': price_update_count  
        }

        order_dict.update({
            'highest_price': updated_highest_price,
            'stoploss': updated_stoploss,
            'status': status,
            'selling_price': selling_price,
            'evaluation_result': evaluation_result,
            'market_price': new_price,
            'is_matched': status == 'matched',
            'price_update_count': price_update_count
        })

        return {
            'uuid': order_dict['uuid'],  
            'order_dict': order_dict, 
            'history_record': history_record,  
        }

    def process_batch(batch_df, batch_id):
        start_time = datetime.now()
        print(f"Starting processing for batch {batch_id}")

        if batch_df.rdd.isEmpty():
            print("Batch is empty, skipping processing.")
            return

        new_price_row = batch_df.select("price").head()
        if new_price_row is not None:
            new_price = new_price_row["price"]
        else:
            new_price = None

        def process_partition(iterator):
            session = get_cassandra_session()
            for order_dict in iterator:
                updated_order = update_order_logic(order_dict, new_price)
                history_record = updated_order['history_record']
                Order2.save_history_record(history_record['uuid'], history_record, session)
            session.shutdown()

        existing_orders_df = spark.read \
            .format("org.apache.spark.sql.cassandra") \
            .options(table="orders", keyspace="trading_data") \
            .load()

        orders_rdd = existing_orders_df.rdd.map(lambda order: order.asDict())
        orders_rdd.foreachPartition(process_partition)

        end_time = datetime.now()
        print(f"Batch {batch_id} processed. Time taken: {(end_time - start_time).total_seconds()} seconds")


    query = price_df \
            .writeStream \
            .foreachBatch(process_batch) \
            .start()

    query.awaitTermination()



if __name__ == "__main__":
    main()