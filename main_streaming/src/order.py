from uuid import UUID
from datetime import datetime
import json
import fastapi
from fastapi import WebSocket
import logging
import asyncio
import csv
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
import uuid
import cassandra.util



# Cassandra connection setup
auth_provider = PlainTextAuthProvider(username='admin', password='chitoge1234')
cluster = Cluster(['localhost'], port=9042, auth_provider=auth_provider)
session = cluster.connect('trading_data')


class Order:
    def __init__(self, user_id,market_price, quantity, stopsize, order_uuid=None):
        self.user_id = user_id
        # self.initial_market_price = int(market_price) 
        self.quantity = quantity
        self.stopsize = stopsize
        self.market_price = market_price
        self.highest_price = market_price  
        self.selling_price = None
        self.stoploss = self.market_price - self.stopsize
        self.is_matched = False
        self.uuid = order_uuid if order_uuid else uuid.uuid4()  # Ensure this is a UUID object
        self.initial_data_saved = False
        self.status = 'pending'
        self.price_update_count = 0 
        self.selling_price = None


    @classmethod
    def save_orders_to_cassandra(cls, orders, session):
        insert_stmt = session.prepare("""
            INSERT INTO orders (
                uuid, 
                highest_price, 
                is_matched, 
                market_price, 
                price_update_count, 
                quantity, 
                selling_price, 
                status, 
                stoploss, 
                stopsize, 
                user_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """)
        for order in orders:
            # Directly access attributes instead of using subscript notation
            user_id_uuid = UUID(order.user_id) if isinstance(order.user_id, str) else order.user_id
            session.execute(insert_stmt.bind([
                order.uuid,
                order.highest_price, 
                order.is_matched, 
                order.market_price, 
                order.price_update_count, 
                order.quantity, 
                order.selling_price, 
                order.status, 
                order.stoploss, 
                order.stopsize, 
                user_id_uuid
            ]))

    

    @staticmethod
    def save_history_record(order_uuid, history_record, session):
        if 'user_id' not in history_record:
            print(f"Missing 'user_id' in history_record: {history_record}")
            return
        try:
            order_uuid_obj = uuid.UUID(order_uuid) if isinstance(order_uuid, str) else order_uuid
            user_id_str = history_record.get('user_id')
            # Convert user_id to a UUID object if it's a string
            if user_id_str:
                user_id_obj = uuid.UUID(user_id_str) if isinstance(user_id_str, str) else user_id_str
            else:
                # Handle missing 'user_id' appropriately
                print("Missing 'user_id' in history record.")
                return  # or continue with a default 'user_id', if applicable
            
            prepared_statement = session.prepare("""
                INSERT INTO order_history (
                    uuid, market_price, stoploss, status, evaluation_result, 
                    stopsize, user_id, is_matched, selling_price, price_update_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """)

            # Bind the values, ensuring UUID objects are used for uuid and user_id
            session.execute(prepared_statement.bind([
                order_uuid_obj,
                history_record['market_price'],
                history_record['stoploss'],
                history_record['status'],
                history_record.get('evaluation_result', 'not_evaluated'),  # Providing a default value
                history_record['stopsize'],
                user_id_obj,
                history_record['is_matched'],
                history_record['selling_price'],
                history_record['price_update_count']
            ]))
        except Exception as e:
            print(f"Error saving history record: {e}")