from datetime import datetime
import fastapi
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from fastapi import BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from typing import Optional
import json
import random
import time
import asyncio
import logging
import uuid
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from order import Order
import socketio
from uuid import UUID



app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
socketio_app = socketio.ASGIApp(sio, app)



auth_provider = PlainTextAuthProvider(username='admin', password='chitoge1234')
cluster = Cluster(['localhost'], port=9042, auth_provider=auth_provider)
session = cluster.connect('trading_data')

@sio.event
async def connect(sid, environ):
    await sio.emit('my_message', {'response': 'Connected'})


class GenerateOrdersRequest(BaseModel):
    number_of_orders: int


@app.get('/orders/{uuid}', status_code=200)
def get_order_by_uuid(uuid: str):
    try:
        uuid_obj = UUID(uuid)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")
    
    query = "SELECT * FROM orders WHERE uuid = %s"
    result = session.execute(query, [uuid_obj])
    order_data = result.one()
    
    if not order_data:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Assuming order_data is a Row object that can be treated as a dict
    return order_data if isinstance(order_data, dict) else order_data._asdict()

@app.get("/orders/{uuid}/status")
async def get_order_status(uuid: str):
    query = "SELECT is_matched, selling_price FROM orders WHERE uuid = %s"
    result = session.execute(query, [UUID(uuid)])
    order_data = result.one()
    
    if not order_data:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return {"is_matched": order_data.is_matched, "selling_price": order_data.selling_price}

@app.post("/login/{user_id}")
async def login(user_id: str):
    query = "SELECT uuid FROM orders WHERE user_id = %s ALLOW FILTERING"
    try:
        user_id_obj = UUID(user_id)  # Ensuring user_id is in UUID format
        result = session.execute(query, [user_id_obj])
        user_data = result.one()
        if user_data:
            return {"message": "User authenticated", "user_id": user_id}
        else:
            raise HTTPException(status_code=404, detail="User not found")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")
    

@app.get("/user/{user_uuid}/orders/stats")
async def get_user_order_stats(user_uuid: str):
    query = """
    SELECT is_matched, COUNT(*) as count 
    FROM orders 
    WHERE user_id = %s 
    GROUP BY uuid
    ALLOW FILTERING
    """
    try:
        user_uuid_obj = UUID(user_uuid)
        result = session.execute(query, [user_uuid_obj])
        matched_orders_count = 0
        unmatched_orders_count = 0
        for row in result:
            if row.is_matched:
                matched_orders_count += row.count
            else:
                unmatched_orders_count += row.count

        return {
            "matched_orders_count": matched_orders_count,
            "unmatched_orders_count": unmatched_orders_count,
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")


@app.get("/user/{user_uuid}/orders")
async def get_user_orders(user_uuid: str):
    query = "SELECT * FROM orders WHERE user_id = %s ALLOW FILTERING"
    try:
        user_uuid_obj = UUID(user_uuid)
        result = session.execute(query, [user_uuid_obj])
        orders = []
        for row in result:
            order = {column: getattr(row, column) for column in row._fields}
            orders.append(order)
        
        if not orders:
            raise HTTPException(status_code=404, detail="No orders found for this user")
        
        return orders
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")


@app.get('/orders/{uuid}/count_new_price_come', status_code=200)
async def get_price_update_count(uuid: str):
    try:
        valid_uuid = UUID(uuid)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    query = "SELECT price_update_count FROM orders WHERE uuid = %s"
    result = session.execute(query, [valid_uuid])
    order_data = result.one()

    if not order_data:
        raise HTTPException(status_code=404, detail="Order not found or price update count not available")

    return {"price_update_count": order_data.price_update_count}


@app.get('/orders/{uuid}/evaluation', status_code=200)
async def get_order_evaluation(uuid: str):
    try:
        valid_uuid = UUID(uuid)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    query = "SELECT initial_market_price, selling_price, evaluation_result FROM orders WHERE uuid = %s"
    result = session.execute(query, [valid_uuid])
    order_data = result.one()

    if not order_data:
        raise HTTPException(status_code=404, detail="Order not found")

    initial_price = float(order_data.initial_market_price or 0)
    selling_price = float(order_data.selling_price or 0)
    evaluate_result = order_data.evaluation_result

    if evaluate_result is None and selling_price:
        evaluate_result = "good" if selling_price > initial_price else "bad"
        # Update Cassandra with the new evaluation result. Ensure you have an update statement prepared for this.

    explanation = "Evaluation result not available."
    if evaluate_result == 'good':
        explanation = f'This order is considered good because it was sold at ${selling_price}, which is higher than the initial price of ${initial_price}, indicating a profit.'
    elif evaluate_result == 'bad':
        explanation = f'This order is considered bad because it was sold at ${selling_price}, which is not higher than the initial price of ${initial_price}, indicating no profit or a loss.'

    return {"evaluation_result": evaluate_result, "explanation": explanation}


@app.get("/admin/order-stats")
async def get_order_stats():
    # Query to count total orders
    total_orders_query = "SELECT COUNT(*) FROM orders"
    total_orders_result = session.execute(total_orders_query)
    total_orders = total_orders_result.one()[0]

    # Query to count ended orders (assuming is_matched indicates an order has ended)
    ended_orders_query = "SELECT COUNT(*) FROM orders WHERE is_matched = True ALLOW FILTERING"
    ended_orders_result = session.execute(ended_orders_query)
    ended_orders = ended_orders_result.one()[0]

    # Calculate ongoing orders
    ongoing_orders = total_orders - ended_orders

    return {
        "total_orders": total_orders,
        "ended_orders": ended_orders,
        "ongoing_orders": ongoing_orders
    }


@app.post('/generate_orders/')
async def generate_orders(request: GenerateOrdersRequest, background_tasks: BackgroundTasks):
    """Endpoint to generate a specified number of orders."""
    async def create_order_async(user_id, market_price, quantity, stopsize):
        user_id = user_id if user_id else str(uuid.uuid4())
        order_uuid = uuid.uuid4()
        market_price = int(round(market_price))
        return Order(user_id, market_price, quantity, stopsize, order_uuid)
    async def generate_orders_task():
        start_time = time.time()  

        tasks = []
        for _ in range(request.number_of_orders):
            market_price = round(random.uniform(75, 85))
            quantity = random.randint(1, 10)
            stopsize = round(random.uniform(5, 10))

            task = create_order_async(None, market_price, quantity, stopsize)
            tasks.append(task)

        orders = await asyncio.gather(*tasks)  
        Order.save_orders_to_cassandra(orders, session)  

        end_time = time.time()  
        total_time = end_time - start_time  
        print(f"Generated and saved {request.number_of_orders} orders in {total_time:.2f} seconds")

    try:
        background_tasks.add_task(generate_orders_task)
        return {"message": "Orders generation task started"}
    except Exception as e:
        logging.exception("Failed to start orders generation task.")
        raise HTTPException(status_code=500, detail=str(e))



@app.post('/price_update/')
async def price_update(request: Request):
    data = await request.json()
    await sio.emit('price_updated', data)
    return {"message": "Price update signal received"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
