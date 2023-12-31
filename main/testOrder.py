import pytest 
from order import Order
import redis
from order_api  import get_order_by_uuid

r = redis.StrictRedis(host='localhost',port=6379)

@pytest.fixture
def f_create_and_cleanup_order():
    order = Order(100,100,10)
    yield order

    r.delete(f"order:{order.uuid}")

# @pytest.fixture
# def f_create_and_cleanup_bulk_orders():
#     order_details = [(100 + i, 10, 5) for i in range(100)]  # Creating 100 orders with varying market prices
#     orders = [Order(price, quantity, stoploss) for price, quantity, stoploss in order_details]
#     yield orders  # This will execute the test

#     for order in orders:
#         r.delete(f"order:{order.uuid}")  # Cleanup after test


def test_order1(f_create_and_cleanup_order):
    new_prices = [105,103,105,100,97,95]
    order = f_create_and_cleanup_order
    for price in new_prices:
        order.update_order(price)

    # order.update_order(110)
    assert order.stoploss == 95
    assert order.is_matched is True


def test_huge_order(f_create_and_cleanup_order):
    new_prices = [105,103,105,100,97,95]
    order_list = []
    for i in range (7):
        order = f_create_and_cleanup_order
        order_list.append(order)

    for price in new_prices:
        for order in order_list:
            order.update_order(price)

    assert order_list[1].stoploss == 95
    assert order_list[1].is_matched is True



def test_api_by_uuid():
    order_data = get_order_by_uuid("fbcf39be-69f5-46ae-b76f-f4a8d904df78")
    assert order_data is not None



def test_Order_Update_Sell(f_create_and_cleanup_order):
    order = f_create_and_cleanup_order
    order.update_order(90)

    assert order.is_matched == True

def test_bulk_order_updates(f_create_and_cleanup_bulk_orders):
    orders = f_create_and_cleanup_bulk_orders

    # Simulate updating each order
    for order in orders:
        new_price = order.market_price + 15
        order.update_order(new_price)

    # Verify each order' updated state
    for order in orders:
        updated_order_data = r.hgetall(f"order:{order.uuid}")
        if updated_order_data:
            updated_order = {k.decode("utf-8"): v.decode("utf-8") for k,v in updated_order_data.items()}
            expected_stoploss = float(updated_order["market_price"]) - order.stopsize
            assert float(updated_order["stoploss"]) == expected_stoploss
            

def test_Huge_Order(f_create_and_cleanup_bulk_orders):
    orders = f_create_and_cleanup_bulk_orders
    price_Arr = [80,90,91,75]

    executed_orders = set()
    # Simulate updating each order
    for prices in price_Arr:
        for order in orders:
            if order.uuid not in executed_orders:
                order.update_order(prices)
                if(order.is_matched):
                    executed_orders.add(order.uuid)

    # Verify each order' updated state
    for order in orders:
        if order.uuid not in executed_orders:
            updated_order_data = r.hgetall(f"order:{order.uuid}")
            if updated_order_data:
                updated_order = {k.decode("utf-8"): v.decode("utf-8") for k, v in updated_order_data.items()}
                expected_stoploss = float(updated_order["highest_price"]) - order.stopsize
                assert float(updated_order["stoploss"]) == expected_stoploss, f"Order {order.uuid} has incorrect stop loss"
        else:
            assert not r.exists(f"order:{order.uuid}"), f"Order {order.uuid} should be executed and removed"

