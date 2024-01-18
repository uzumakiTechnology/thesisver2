from kafka import KafkaConsumer
import redis
import json
import socketio
import asyncio
from datetime import datetime, timedelta
import pytz
import uuid


r = redis.Redis(host='127.0.0.1', port=6379)


vietnam_tz = pytz.timezone('Asia/Ho_Chi_Minh')

sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
app = socketio.ASGIApp(sio)


socket_app = socketio.ASGIApp(sio, app)

@sio.event
async def connect(sid, environ):
    print('Client connected', sid)

@sio.event
async def disconnect(sid):
    print('Client disconnected', sid)

orders = {}

BATCH_SIZE = 100

def parse_datetime_with_fallback(datetime_str):
    # Correcting malformed timestamp
    parts = datetime_str.split('T')
    if len(parts) == 2:
        date_part, time_part = parts
        time_components = time_part.split(':')
        if len(time_components) > 0 and len(time_components[0]) == 3:
            # Correct the hour part
            corrected_hour = time_components[0][1:]  # Remove the extra leading zero
            time_components[0] = corrected_hour
            time_part = ':'.join(time_components)
            datetime_str = f"{date_part}T{time_part}"
    
    try:
        return datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=pytz.utc)
    except ValueError:
        try:
            return datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=pytz.utc)
        except ValueError:
            print(f"Incorrect timestamp format: {datetime_str}")
            return None

consumer = KafkaConsumer(
    "new_price", 
    bootstrap_servers="localhost:9092", 
    value_deserializer=lambda x: json.loads(x.decode('utf-8')),
    auto_offset_reset='latest',  
    enable_auto_commit=True 
)


async def listen_for_price_updates():
    print("Batching Consumer started. Listening for price updates...")
    try:
        for message in consumer:
            try:
                new_price = message.value['price']
                print(f"Received new price: {new_price}")
                await process_new_price(new_price)
            except Exception as process_error:
                print(f"Error processing message: {process_error}")
    except Exception as consumer_error:
        print(f"Error in consumer loop: {consumer_error}")
    finally:
        consumer.close()
        print("Consumer closed.")


def calculate_percentage_change(initial_price, selling_price):
    if initial_price == 0:
        return 0
    return ((selling_price - initial_price) / initial_price) * 100

    
async def process_new_price(new_price):
    all_order_uuids = r.keys("order:*")
    start_time = datetime.now()
    if not all_order_uuids:
        print("No orders found.")  # Debug print
        return
    
    batch = []
    for order_uuid in all_order_uuids:
        batch.append(order_uuid.decode('utf-8'))
        if len(batch) >= BATCH_SIZE:
            await process_batch(batch, new_price)
            batch = [] # reset batch
        
    if batch:
        await process_batch(batch, new_price)


async def process_batch(batch, new_price):
    start_time = datetime.now()
    # Process all updates in the batch
    
    update_tasks = [update_order_with_new_price(order_uuid, new_price) for order_uuid in batch]
    await asyncio.gather(*update_tasks)
    end_time = datetime.now()
    print(f"Time taken to update batch of orders: {end_time - start_time}")


async def update_order_with_new_price(order_uuid, new_price):
    clean_order_uuid = order_uuid.split(":")[1]
    order_key = f"order:{clean_order_uuid}"
    order_history_key = f"order_history:{clean_order_uuid}"
    chart_data_key = f"chart_data:{clean_order_uuid}"

    pipe = r.pipeline()
    pipe.hgetall(order_key)
    pipe.lrange(order_history_key, 0, 0)
    order_data_result, last_history_entries = pipe.execute()

    if not order_data_result:
        print(f"No order found for UUID: {clean_order_uuid}")
        return

    order_data = {k.decode('utf-8'): v.decode('utf-8') for k, v in order_data_result.items()}
    highest_price = float(order_data.get('highest_price', 0))
    stoploss = float(order_data.get('stoploss', 0))
    stopsize = float(order_data.get('stopsize', 0))
    initial_market_price = float(order_data.get('initial_market_price', 0))
    is_matched_already = order_data.get('is_matched') == 'True'
    is_matched = 'False' 
    last_update_time = datetime.strptime(order_data.get('timestamp'), "%Y-%m-%dT%H:%M:%S.%fZ")
    percentage_change = None

    price_update_count = int(order_data.get('price_update_count', 0))
    if not is_matched_already:
        price_update_count += 1

    new_timestamp = (last_update_time + timedelta(minutes=30)).isoformat() + 'Z'
    status = 'updated'
    selling_price = order_data.get('selling_price', '')
    evaluation_result = order_data.get('evaluation_result', 'not_evaluated')

    if not is_matched_already and new_price <= stoploss:
        selling_price = str(new_price)
        status = 'matched'
        is_matched = 'True'
        percentage_change =  calculate_percentage_change(initial_market_price, new_price)  
        evaluation_result = "good" if new_price > initial_market_price else "bad"
    elif is_matched_already:
        is_matched = 'True'
        status = 'matched'
        percentage_change = order_data.get('percentage_change', None)

    new_data = {
        'market_price': str(new_price),
        'highest_price': str(max(new_price, highest_price)),
        'stoploss': str(max(new_price - stopsize, stoploss)),
        'timestamp': new_timestamp,
        'status': status,
        'selling_price': selling_price,
        'price_update_count': price_update_count,
        'stopsize': str(stopsize),
        'is_matched': is_matched,
        'evaluation_result': evaluation_result,
        'percentage_change': str(percentage_change)
    }

    json_new_data = json.dumps(new_data)

    if not last_history_entries or (last_history_entries and last_history_entries[0].decode('utf-8') != json_new_data):
        try:
            pipe.hset(order_key, mapping=new_data)
            pipe.lpush(order_history_key, json_new_data)
            pipe.lpush(chart_data_key, json_new_data)
            if status == 'matched':
                pipe.sadd('orders:matched', clean_order_uuid)
                await sio.emit('sell_order_triggered', new_data)
            pipe.execute()
        except Exception as e:
            print(f"Redis pipeline execution error: {e}")


async def main():
    asyncio.create_task(listen_for_price_updates())


if __name__ == '__main__':
    asyncio.run(listen_for_price_updates())


