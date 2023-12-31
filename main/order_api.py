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


# Define a Pydantic model for the Order(data) request
class OrderRequest(BaseModel):
    user_id: Optional[str] = None
    market_price: float
    quantity: int
    stopsize: float
    timestamp: Optional[str] = None
    

# Socket.IO connection events
@sio.event
async def connect(sid, environ):
    print('Client connected', sid)

@sio.event
async def disconnect(sid):
    print('Client disconnected', sid)

# Endpoints to accept and process order
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

@app.get('/orders/{uuid}/history')
def get_order_history(uuid: str):
    order_history_data = r.lrange(f'order_history:{uuid}', 0, -1)
    if not order_history_data:
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




if __name__ == "__main__":
    uvicorn.run(socketio_app, host="0.0.0.0", port=8000)


