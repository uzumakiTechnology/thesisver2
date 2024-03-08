Update 

New entry : updated state of the order add to redis list

order_history:{order_uuid}  : Act as version history for the order, each entry in this
list represent the state of the order at a certain point in time
Every time you update the order, you push the new state to the list using `lpush`
This command adds a new entry to the head of the list, so the latest state is always at the beginning.


REtrieving the Order History : Get the entire history of the order, retrieve the entire list
using lrange

LRANGE order_history:ab83d806-b08e-4904-b726-1e5e31f3f7ae 0 -1



f you want to fetch a specific version (e.g., the third version since the order was created), you can use the index when calling lrange
LINDEX order_history:ab83d806-b08e-4904-b726-1e5e31f3f7ae 2

delete keys in redis (key order)
EVAL "for _,key in ipairs(redis.call('keys', 'order:*')) do redis.call('del', key) end" 0
EVAL "for _,key in ipairs(redis.call('keys', 'order_history:*')) do redis.call('del', key) end" 0


    # def process_batch(batch_df, batch_id):
    #     successful_updates = 0
    #     failed_updates = 0
    #     print(f"Starting processing for batch {batch_id}")
    #     try:
    #         if batch_df.count() > 0:
    #             new_price = batch_df.agg({"price": "max"}).collect()[0][0]
    #             send_http_request({'price': float(new_price)})

    #             # Read the current state of orders from Cassandra
    #             existing_orders_df = spark.read \
    #                 .format("org.apache.spark.sql.cassandra") \
    #                 .options(table=cassandra_table_name, keyspace=cassandra_keyspace_name) \
    #                 .load().select("uuid", "user_id", "quantity", "highest_price", "initial_market_price", "stopsize", "stoploss", "price_update_count", "selling_price", "status", "is_matched")

    #             # Perform an inner join between the existing orders and the new prices using the UUID
    #             joined_df = existing_orders_df.join(batch_df, ["uuid"], "inner")
    #             joined_df = joined_df.withColumn('new_price', lit(new_price))


    #             # Update each order with the new price information
    #             updated_orders_rdd = joined_df.rdd.map(lambda row: update_order_logic(row, row.new_price))


    #             # Filter out None values which indicate a failed update
    #             updated_orders_rdd = updated_orders_rdd.filter(lambda x: x is not None)

    #             result = update_order_logic(lambda row: update_order_logic(row, new_price))
    #             if result:
    #                 successful_updates += 1
    #             else:
    #                 failed_updates += 1

    #             # Convert the RDD to a DataFrame
    #             updated_orders_df = batch_df.withColumn('updated_order', update_order_logic_udf(col('order'), col('new_price')))

    #             # Write the updated DataFrame back to Cassandra
    #             updated_orders_df.write \
    #                 .format("org.apache.spark.sql.cassandra") \
    #                 .options(table=cassandra_table_name, keyspace=cassandra_keyspace_name) \
    #                 .mode("append") \
    #                 .save()
    #             print(f"Batch {batch_id} processed with {successful_updates} successful updates and {failed_updates} failed updates.")
    #     except Exception as e:
    #         print(f"Exception in process_batch for batch {batch_id}: {e}")
    