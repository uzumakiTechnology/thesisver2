import hazelcast

client = hazelcast.HazelcastClient(
    cluster_members=[
        "127.0.0.1:5701"  # Replace with the address of your Hazelcast cluster members
    ]
)


class orderWithHazelcast:
    def __init__(self, user_id, market_price, quantity, stopsize, timestamp=None):
        
        pass