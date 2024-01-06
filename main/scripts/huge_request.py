import requests
import random
from datetime import datetime, timedelta
import uuid

def create_sample_orders(n,start_time,end_time):
    url = "http://127.0.0.1:8000/orders/"

    for i in range(n):

        # Market price starts at 80, then fluctuation by up to 0.3 %
        fluctuation = random.uniform(-0.003, 0.003)
        market_price = 80 * (1 + fluctuation)

        # Random quantity
        quantity = random.randint(1, 10)

        # random stop size
        stopsize = random.uniform(5, 10)

        order_uuid = str(uuid.uuid4())

        # random timestamp from now and three hours from now
        random_seconds = random.randint(0, int((end_time - start_time).total_seconds()))
        timestamp = start_time + timedelta(seconds=random_seconds)
        timestamp_str = timestamp.isoformat() + 'Z'

        order_data = {
            "market_price": market_price, 
            "quantity": quantity,
            "stopsize": stopsize,
            "stoploss": market_price - stopsize,
            "timestamp":timestamp_str
        }

        response = requests.post(url, json=order_data)
        if response.status_code == 200:
            order_uuid = order_uuid
            print(f"Order created: {order_uuid}")
        else:
            print(f"Failed to create order {i+1}: {response.status_code} {response.text}")


start_time = datetime.now().replace(hour=1, minute=30, second=0, microsecond=0)
end_time = datetime.now().replace(hour=3, minute=0, second=0, microsecond=0)

start_time_for_measurement = datetime.now()
create_sample_orders(1000, start_time, end_time) # Gen 1000 orders
end_time_for_measurement = datetime.now()
elapsed_time = end_time_for_measurement - start_time_for_measurement
print(f"Time taken to create 10000 orders: {elapsed_time}")
