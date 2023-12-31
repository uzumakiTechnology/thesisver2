from kafka import KafkaConsumer
import matplotlib.pyplot as plt
import json

# Initialze Kafka consumer
consumer = KafkaConsumer("new_price", bootstrap_servers="localhost:9092")

# Data for plotting
time_stamps = []
market_prices = []

plt.ion() # interactive mode
fig, ax = plt.subplots()
line, = ax.plot([], [], label='Market Price')

ax.set_xlabel('Time')
ax.set_ylabel('Market Price')
ax.legend()

# Update the plot
def update_plot(timestamp, market_price):
    time_stamps.append(timestamp)
    market_prices.append(market_price)

    line.set_xdata(time_stamps)
    line.set_ydata(market_prices)

    plt.draw()
    plt.pause(0.1) # Update time

def listen_for_price_updates():
    for message in consumer:
        message_json = json.loads(message.value)
        time_stamps = message.time_stamps
        market_prices = message_json['price']

        # Process new price and update the plot
        process_new_price(time_stamps, market_prices)

def process_new_price(timestamp, market_price):
    # Update plot
    update_plot(timestamp, market_price)

if __name__ == '__main__':
    listen_for_price_updates()