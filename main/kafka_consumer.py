# poll price back
# Responsible for fetching new price, information and updating each relevant order
from kafka import KafkaConsumer
import redis
from order import Order
import json
import socketio
import asyncio
from datetime import datetime, timedelta
import pytz
from orderWithoutPipeline import orderWithoutPipeline

vietnam_tz = pytz.timezone('Asia/Ho_Chi_Minh')

# Set up a Socket.IO server
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
app = socketio.ASGIApp(sio)


socket_app = socketio.ASGIApp(sio, app)

# Socket.IO events
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

    # Start a Redis pipeline
    pipe = r.pipeline()
    pipe.hgetall(order_key)
    order_data_result = pipe.execute()

    if order_data_result[0]:
        order_data = order_data_result[0]
        order_data = {k.decode('utf-8'): float(v.decode('utf-8')) if k.decode('utf-8') in ['market_price', 'highest_price', 'stopsize', 'stoploss'] else v.decode('utf-8') for k, v in order_data.items()}
        highest_price = order_data.get('highest_price')
        stopsize = order_data.get('stopsize')
        stoploss = order_data.get('stoploss')
        is_matched = order_data.get('is_matched') == 'True'
        status = order_data.get('status','pending')
        price_update_count = int(order_data.get('price_update_count', 0)) + 1

        if new_price <= stoploss and not is_matched:
            pipe.hset(order_key, 'selling_price', str(new_price))
            initial_price = float(order_data.get('market_price',0))
            evaluate_result = "good" if new_price > initial_price else "bad"            
            matched_data = {
                'is_matched': 'True',
                'market_price': str(new_price),
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'price_update_count': price_update_count,
                'selling_price': str(new_price),  
                'evaluation_result': evaluate_result
            }
            pipe.hmset(f"order:{clean_order_uuid}", matched_data)
            pipe.hmset(f"order_last_state:{clean_order_uuid}", matched_data)
            pipe.hmset(order_key, matched_data)
            # pipe.lpush(order_history_key, json.dumps(matched_data))
            pipe.hset(order_key,'status','matched')
            pipe.hset(order_key, 'price_update_count', price_update_count)  # Save the count to Redis
            status = 'matched'
            pipe.sadd('orders:matched', clean_order_uuid)
            await sio.emit('sell_order_triggered', matched_data)
            return
        
        update_required = False
        if new_price > highest_price and not is_matched:
            highest_price = new_price
            stoploss = new_price - stopsize
            update_required = True

        if new_price != order_data['market_price']:
            update_required = True

            if update_required:
                existing_timestamp = parse_datetime_with_fallback(order_data['timestamp'])
                if existing_timestamp is None:
                    print(f"Failed to parse timestamp for order {order_uuid}. Skipping update.")
                    return
                existing_timestamp_vn = existing_timestamp.astimezone(vietnam_tz)
                new_timestamp = existing_timestamp_vn + timedelta(minutes=30)
                new_timestamp_str = new_timestamp.astimezone(pytz.utc).isoformat().replace('+00:00', 'Z')
                updated_order_data = {
                    'market_price': new_price,
                    'highest_price': highest_price,
                    'stoploss': stoploss,
                    'timestamp': new_timestamp_str,
                    'stopsize': stopsize,
                    'price_update_count': price_update_count
                }
                pipe.hmset(order_key, updated_order_data)
                # pipe.lpush(order_history_key, json.dumps(updated_order_data))
                if status != 'matched':
                    pipe.hset(order_key, 'status', 'updated')
                print(f"Emitting price_update for order {order_uuid} with data: {updated_order_data}")
                await sio.emit('order_update', {'order_uuid': clean_order_uuid, 'data': updated_order_data})
        pipe.execute()
    else:
        print(f"No order found for UUID: {clean_order_uuid}")
         

async def main():
    asyncio.create_task(listen_for_price_updates())


if __name__ == '__main__':
    asyncio.run(main())