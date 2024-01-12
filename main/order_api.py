from datetime import datetime
from fastapi import FastAPI, Form, HTTPException, WebSocket, WebSocketDisconnect
from order import Order
from pydantic import BaseModel
import redis
from fastapi import BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import socketio
import uvicorn
from typing import Optional
import json
from orderWithoutPipeline import orderWithoutPipeline
import random
import time
import kafka_consumer
import kafka_consumerWOPipeline
import kafka_producer
import asyncio
from kafka_producer import producer
from kafka import KafkaProducer

r = redis.StrictRedis(host='localhost',port=6379)
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

# Socket io instance
sio = socketio.AsyncServer(async_mode='asgi',cors_allowed_origins='*')
socketio_app = socketio.ASGIApp(sio, app)
producer = KafkaProducer(bootstrap_servers="localhost:9092", value_serializer=lambda v: json.dumps(v).encode('utf-8'))


# Define a Pydantic model for the Order(data) request
class OrderRequest(BaseModel):
    user_id: Optional[str] = None
    market_price: float
    quantity: int
    stopsize: float
    timestamp: Optional[str] = None
    
# For bulk order created    
class GenerateOrdersRequest(BaseModel):
    number_of_orders: int
    use_pipeline: bool

class PriceModel(BaseModel):
    price: int

# Socket.IO connection events
@sio.event
async def connect(sid, environ):
    print('Client connected', sid)

@sio.event
async def disconnect(sid):
    print('Client disconnected', sid)

@app.post('/orderWithoutPipeline')
async def create_and_process_order_without_pipeline(order_request: OrderRequest, background_tasks: BackgroundTasks):
    def process_order_creation(order_request):
        orderWithoutPipelines = orderWithoutPipeline(order_request.user_id,order_request.market_price, order_request.quantity, order_request.stopsize, order_request.timestamp)
        return orderWithoutPipelines
    background_tasks.add_task(process_order_creation, order_request)
    return {"message": "Order creation for without pipeline version received and is being processed"}


# Endpoints to accept and process order (version with pipeline)
@app.post('/orders/')
async def create_and_process_order(order_request: OrderRequest, background_tasks: BackgroundTasks):
    def process_order_creation(order_request):
        order = Order(order_request.user_id,order_request.market_price, order_request.quantity, order_request.stopsize, order_request.timestamp)
        return order
    background_tasks.add_task(process_order_creation, order_request)
    return {"message": "Order received and is being processed"}




# Endpoint to get an order by UUID
@app.get('/orders/{uuid}',status_code=200)
def get_order_by_uuid(uuid: str):
    order_data = r.hgetall(f'order:{uuid}')
    if not order_data:
        raise HTTPException(status_code=404, detail="Order not found")
    return order_data

@app.get('/orders/{uuid}/chart_data')
def get_order_data(uuid: str):
    order_data_key = f'chart_data:{uuid}'
    order_chart_data_key = r.lrange(order_data_key, 0, -1)
    if not order_data_key:
        print(f"No chart data found for order: {uuid}")  # Debug print
        raise HTTPException(status_code=404, detail="Order history not found")
    order_chart = [json.loads(data) for data in order_chart_data_key]
    return order_chart

@app.get('/orders/{uuid}/history')
def get_order_history(uuid: str):
    order_history_key = f'order_history:{uuid}'
    order_history_data = r.lrange(order_history_key, 0, -1)
    if not order_history_data:
        print(f"No history found for order: {uuid}")  # Debug print
        raise HTTPException(status_code=404, detail="Order history not found")
    order_history = [json.loads(data) for data in order_history_data]
    return order_history



@app.get('/orders/{uuid}/initial')
def get_initial_order_data(uuid: str):
    initial_data_key = f"order_initial:{uuid}"
    initial_order_data = r.hgetall(initial_data_key)
    if not initial_order_data:
        raise HTTPException(status_code=404, detail="Initial order data not found")
    initial_order_data_converted = {k.decode('utf-8'): v.decode('utf-8') for k, v in initial_order_data.items()}
    return initial_order_data_converted

@app.get('/orders/{uuid}/last_state')
def get_order_last_state(uuid: str):
    last_state_data = r.hgetall(f'order_last_state:{uuid}')
    if not last_state_data:
        raise HTTPException(status_code=404, detail="Order last state not found")
    return {k.decode('utf-8'): v.decode('utf-8') for k, v in last_state_data.items()}

@app.get("/orders/{uuid}/status")
async def get_order_status(uuid: str):
    order_data = r.hgetall(f"order:{uuid}")
    if not order_data:
        raise HTTPException(status_code=404, detail="Order not found")

    # Decode byte strings to regular strings
    order_data = {k.decode('utf-8'): v.decode('utf-8') for k, v in order_data.items()}

    print(f"Order data for {uuid}: {order_data}")

    is_matched = order_data.get('is_matched', 'False') == 'True'
    market_price = order_data.get('market_price', '0')

    return {"is_matched": is_matched, "market_price": market_price}



@app.post("/login/{uuid}")
async def login(uuid: str):
    if r.exists(f"user:{uuid}"):
        return {"message": "User authenticated", "uuid": uuid}
    raise HTTPException(status_code=404, detail="User not found")




@app.get("/user/{user_uuid}/orders/stats")
async def get_user_order_stats(user_uuid: str):
    matched_orders = []
    unmatched_orders = []
    for key in r.scan_iter("order:*"):
        order_data = {k.decode('utf-8'): v.decode('utf-8') for k, v in r.hgetall(key).items()}
        print(f"Checking order with key {key.decode('utf-8')}: {order_data}")  # Decode key for print
        
        if order_data.get('user_id') == user_uuid:
            print(f"Order found for user {user_uuid}: {order_data}")  # Debugging print
            is_matched = order_data.get('is_matched') == 'True'
            print(f"Order {key.decode('utf-8')} is_matched: {is_matched}")  # Check is_matched value

            if is_matched:
                matched_orders.append(order_data)
            else:
                unmatched_orders.append(order_data)
    
    return {
        "matched_orders_count": len(matched_orders),
        "unmatched_orders_count": len(unmatched_orders),
        "matched_orders": matched_orders,
        "unmatched_orders": unmatched_orders
    }



@app.get("/user/{user_uuid}/orders")
async def get_user_orders(user_uuid: str):
    user_orders = []
    # Iterate over all keys that match the order pattern
    for key in r.scan_iter("order:*"):
        # Extract the potential order UUID from the key
        order_uuid = key.decode('utf-8').split(':')[1]
        order_data = r.hgetall(key)
        # Decode and check if the order belongs to the user
        if order_data.get(b'user_id', '').decode('utf-8') == user_uuid:
            # Include the order UUID in the response
            order_data_decoded = {k.decode('utf-8'): v.decode('utf-8') for k, v in order_data.items()}
            order_data_decoded['uuid'] = order_uuid
            user_orders.append(order_data_decoded)
    
    if not user_orders:
        raise HTTPException(status_code=404, detail="No orders found for this user")

    return user_orders

# Endpoint to fetch new price count
@app.get('/orders/{uuid}/count_new_price_come', status_code=200)
async def get_price_update_count(uuid: str):
    price_update_count = r.hget(f'order:{uuid}', 'price_update_count')
    if price_update_count is None:
        raise HTTPException(status_code=404, detail="Order not found or price update count not available")

    # Decode the count value
    price_update_count_decoded = price_update_count.decode('utf-8')

    # Return only the price update count
    return {"price_update_count": price_update_count_decoded}

@app.get('/orders/{uuid}/evaluation', status_code=200)
async def get_order_evaluation(uuid: str):
    order_data = r.hgetall(f'order:{uuid}')
    initial_price = r.hget(f'order:{uuid}', 'initial_market_price')
    selling_price = r.hget(f'order:{uuid}', 'selling_price')
    evaluate_result = r.hget(f'order:{uuid}', 'evaluation_result')
    if not initial_price and selling_price and evaluate_result:
        raise HTTPException(status_code=404, detail="Order not found")

    initial_price_decoded = initial_price.decode('utf-8')
    selling_price_decoded = selling_price.decode('utf-8')
    evaluate_result_decoded = evaluate_result.decode('utf-8')

    if evaluate_result_decoded == 'good':
        explanation = f'This order is considered good because it was sold at ${selling_price_decoded}, ' \
                      f'which is higher than the initial price of ${initial_price_decoded}, indicating a profit.'
    elif evaluate_result_decoded == 'bad':
        explanation = f'This order is considered bad because it was sold at ${selling_price_decoded}, ' \
                      f'which is not higher than the initial price of ${initial_price_decoded}, indicating no profit or a loss.'
    else:
        explanation = 'Evaluation result not available.'

    return {"evaluation_result": evaluate_result_decoded, "explanation": explanation}


@app.get("/admin/order-stats")
async def get_order_stats():
    all_order_keys = r.keys("order:*")
    total_orders = len(all_order_keys)
    ended_orders = 0

    for key in all_order_keys:
        order_data = {k.decode('utf-8'): v.decode('utf-8') for k, v in r.hgetall(key).items()}

        if order_data.get('is_matched') == 'True':
            print(f"Ended order found: {key}")  # Debugging print statement
            ended_orders += 1

    ongoing_orders = total_orders - ended_orders

    return {
        "total_orders": total_orders,
        "ended_orders": ended_orders,
        "ongoing_orders": ongoing_orders
    }

@app.post('/generate_orders/')
async def generate_orders(request: GenerateOrdersRequest, background_tasks: BackgroundTasks):
    """Endpoint to generate a specified number of orders."""
    def generate_orders_task():
        start_time = time.time()  # Time in seconds since the epoch
        for _ in range(request.number_of_orders):
            market_price = random.uniform(75, 85)  # Example random market price
            quantity = random.randint(1, 10)
            stopsize = random.uniform(5, 10)
            timestamp = datetime.utcnow().isoformat() + 'Z'
            if request.use_pipeline:
                Order(None, market_price, quantity, stopsize, timestamp)
            else:
                orderWithoutPipeline(None, market_price, quantity, stopsize, timestamp)
        end_time = time.time()
        total_time = end_time - start_time  
        print(f"Time taken to generate {request.number_of_orders} orders: {total_time} seconds")

    background_tasks.add_task(generate_orders_task)
    return {"message": "Orders generation task started"}


@app.post("/start-consumer/")
async def start_consumer(background_tasks: BackgroundTasks, use_pipeline: bool):
    if use_pipeline:
        background_tasks.add_task(start_kafka_consumer)
    else:
        background_tasks.add_task(start_kafka_consumer_without_pipeline)
    return {"message": "Consumer started"}


def start_kafka_consumer():
    asyncio.run(kafka_consumer.main())

def start_kafka_consumer_without_pipeline():
    asyncio.run(kafka_consumerWOPipeline.main())

@app.post("/produce-prices/")
async def produce_prices():
    kafka_producer.producer_prices()
    return {"message": "Prices produced"}

@app.post("/produce-priceV2/")
async def produce_price(price_data: PriceModel):
    producer.send('new_price',{'price':price_data.price})
    producer.flush()
    return {"message": "Price produced to Kafka topic"}


if __name__ == "__main__":
    uvicorn.run(socketio_app, host="0.0.0.0", port=8000)


