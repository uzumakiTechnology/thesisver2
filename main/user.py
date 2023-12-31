import redis
import uuid

class User:
    def __init__(self, user_uuid=None):
        self.uuid = str(uuid.uuid4()) if user_uuid is None else user_uuid
        self.r = redis.StrictRedis(host='localhost', port=6379, decode_responses=True)

    def save_to_redis(self):
        self.r.set(f"user:{self.uuid}", self.uuid)

# Script to create 100 users
if __name__ == "__main__":
    for _ in range(100):
        user = User()
        user.save_to_redis()
