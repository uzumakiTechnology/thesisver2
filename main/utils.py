import redis

# Initialize Redis connection
r = redis.StrictRedis(host='127.0.0.1', port=6379, db=0)

def get_all_order_uuids():
    # Retrieve all order UUIDs from Redis
    # For example, if you use a Redis Set to keep track of order UUIDs
    return r.smembers('order_uuids')

# Additional utility functions as needed
