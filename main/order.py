import redis
import uuid
from datetime import datetime
import json
from fastapi import WebSocket
import socketio


r = redis.StrictRedis(host='127.0.0.1',port=6379)


class Order:
    def __init__(self, user_id, market_price, quantity, stopsize, timestamp=None):
        self.user_id = user_id
        self.initial_market_price = float(market_price) # price when order placed
        self.quantity = quantity
        self.stopsize = stopsize
        self.market_price = market_price
        self.highest_price = market_price  
        self.selling_price = None
        self.stoploss = self.market_price - self.stopsize
        self.is_matched = False
        self.uuid = str(uuid.uuid4())
        self.timestamp = timestamp if timestamp else datetime.utcnow().isoformat()
        self.initial_data_saved = False
        self.status = 'pending'
        self.price_update_count = 0 # counter for price updates
        self.selling_price = None
        self.save_to_redis()
    
        
    def save_to_redis(self):
        order_data = {
            'user_id': str(self.user_id),
            'initial_market_price': str(self.market_price),
            'market_price': str(self.market_price),
            'highest_price': str(self.highest_price),
            'quantity': str(self.quantity),
            'stopsize': str(self.stopsize),
            'stoploss': str(self.stoploss),
            'timestamp': self.timestamp,
            'is_matched': str(self.is_matched),
            'status': str(self.status),
            'price_update_count': self.price_update_count
        }
        with r.pipeline() as pipe:
            if not self.initial_data_saved:
                initial_data_key = f"order_initial:{self.uuid}"
                pipe.hmset(initial_data_key, order_data)
                self.initial_data_saved = True

            order_data_serialized = json.dumps(order_data)
            pipe.hmset(f"order:{self.uuid}", order_data)
            pipe.lpush(f"order_history:{self.uuid}", order_data_serialized)
            pipe.execute()

    async def update_order(self, new_price):
        if self.is_matched:
            return
        self.price_update_count += 1
        current_stoploss = float(r.hget(f"order:{self.uuid}","stoploss"))
        highest_price = float(r.hget(f"order:{self.uuid}", "highest_price"))

        with r.pipeline() as pipe:           
            if new_price <= current_stoploss:
                self.is_matched = True
                self.status = 'matched'

                matched_data = {
                    'is_matched': 'True',
                    'market_price': str(new_price),
                    'timestamp': datetime.utcnow().isoformat() + 'Z',
                    'status': self.status,
                    'price_update_count': str(self.price_update_count)
                }
                pipe.hmset(f"order:{self.uuid}", matched_data)
                pipe.sadd('orders:matched', self.uuid)
                pipe.lpush(f"order_history:{self.uuid}", json.dumps(matched_data))
                pipe.publish('orders:executed', self.uuid)

                global sio
                await sio.emit('sell_order_triggered', {
                    'uuid': self.uuid,
                    'market_price': new_price,
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                })
                print(f"Order {self.uuid} triggered for selling at price {new_price}")
                pipe.execute()

            # If the new price is higher than the highest recorded price, update the stop loss.
            elif new_price > highest_price and not self.is_matched:
                new_stop_loss = new_price - self.stopsize
                self.market_price = new_price
                self.highest_price = new_price
                self.stoploss = new_stop_loss
                self.status = 'updated'

                updated_data = {
                    'market_price': str(self.market_price),
                    'highest_price': str(self.highest_price),
                    'stoploss': str(self.stoploss),
                    'timestamp': datetime.utcnow().isoformat() + 'Z',
                    'status': self.status
                }
                pipe.hmset(f"order:{self.uuid}", updated_data)
                pipe.lpush(f"order_history:{self.uuid}", json.dumps(updated_data))
                pipe.execute()

    def record_sell(self, selling_price):
        r.hset(f"order:{self.uuid}", 'selling_price', str(selling_price))

    def evaluate_order(self):
        if self.selling_price is None:
            return None
        return "good" if self.selling_price > self.initial_market_price else "bad"

