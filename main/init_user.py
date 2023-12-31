from user import User

# Scripts to create 100 users

def create_users(number_of_users):
    users = []
    for _ in range(number_of_users):
        user = User()
        user.save_to_redis()
        users.append(user)
    return users

if __name__ == "__main__":
    create_users(100)