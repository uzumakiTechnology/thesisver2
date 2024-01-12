from kafka import KafkaConsumer
import redis
import json
import socketio
import asyncio
from datetime import datetime, timedelta
import pytz
import uuid


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
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

r = redis.Redis(host='127.0.0.1',port=6379)

async def listen_for_price_updates():
    # Kafka consumer listen for price updates
    for message in consumer:
        new_price = message.value['price']
        await process_new_price(new_price)    

    
async def process_new_price(new_price):
    all_order_uuids = r.keys("order:*")
    start_time = datetime.now()

    for order_uuid in all_order_uuids:
        order_uuid = order_uuid.decode('utf-8')
        await update_order_with_new_price(order_uuid, new_price)

    end_time = datetime.now()
    elapsed_time = end_time - start_time
    print(f"Time taken to update orders: {elapsed_time}")



async def update_order_with_new_price(order_uuid, new_price):
    clean_order_uuid = order_uuid.split(":")[1]
    order_key = f"order:{clean_order_uuid}"
    order_history_key = f"order_history:{clean_order_uuid}"
    chart_data_key = f"chart_data:{clean_order_uuid}"  # New key for chart data

    # Fetch order data and the latest history entry
    pipe = r.pipeline()
    pipe.hgetall(order_key)
    pipe.lrange(order_history_key, 0, 0)
    order_data_result, last_history_entries = pipe.execute()

    if not order_data_result:
        print(f"No order found for UUID: {clean_order_uuid}")
        return

    # Parse and prepare new data
    order_data = {k.decode('utf-8'): v.decode('utf-8') for k, v in order_data_result.items()}
    highest_price = float(order_data.get('highest_price', 0))
    stoploss = float(order_data.get('stoploss', 0))
    stopsize = float(order_data.get('stopsize', 0))
    last_update_time = datetime.strptime(order_data.get('timestamp'), "%Y-%m-%dT%H:%M:%S.%fZ")
    is_matched_already = order_data.get('is_matched') == 'True'


    is_matched = order_data.get('is_matched') == 'True'
    price_update_count = int(order_data.get('price_update_count', 0)) + 1
    existing_selling_price = order_data.get('selling_price')

    if not existing_selling_price and new_price <= stoploss:
        selling_price = str(new_price)
        status = 'matched'
        is_matched = 'True'
    else:
        selling_price = existing_selling_price
        status = 'updated' if not is_matched_already else 'matched'
        is_matched = 'True' if is_matched_already else 'False'

    new_timestamp = (last_update_time + timedelta(minutes=30)).isoformat() + 'Z'

    new_data = {
        'market_price': str(new_price),
        'highest_price': str(max(new_price, highest_price)),
        'stoploss': str(max(new_price - stopsize, stoploss)),  # Ensure stoploss doesn't increase with price
        'timestamp': new_timestamp,
        'status': status,
        'selling_price': selling_price if selling_price is not None else '',
        'price_update_count': price_update_count,
        'stopsize': str(stopsize),
        'is_matched': is_matched
    }

    json_new_data = json.dumps(new_data)

    if not last_history_entries or (last_history_entries and last_history_entries[0].decode('utf-8') != json_new_data):
        try:
            pipe.hset(order_key, mapping=new_data)
            pipe.lpush(order_history_key, json_new_data)
            pipe.lpush(chart_data_key, json_new_data)  # Add to chart data list
            if new_price <= stoploss and not is_matched_already:
                pipe.sadd('orders:matched', clean_order_uuid)
                await sio.emit('sell_order_triggered', new_data)
            pipe.execute()
        except Exception as e:
            print(f"Redis pipeline execution error: {e}")


async def main():
    asyncio.create_task(listen_for_price_updates())


if __name__ == '__main__':
    asyncio.run(main())


