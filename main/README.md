# different between stopsize and stoploss variables

# stop size : user-defined value determine the distance between current market price and

# inital stop loss price

# stop loss : dynamic value that represent the current stop loss price, gets initialized at the beginning

# then updated in trailing

# If market price is 100 and stop size is 10

# in sell: the stoploss would be set at 90, if market price rises to 105, stoploss adjusted at 95

#

#

#

# Updating the Stop Loss: In the update_stop method, the stop loss is updated depending on the market conditions,

# which aligns with the trailing stop loss theory of moving the stop loss with the market price when it's moving favorably,

# but holding it stationary when the price changes direction.

# In a "sell" situation, if the current price (minus stopsize) is greater than the existing stop loss,

# the stop loss is moved upwards. This represents a situation where the market price is increasing,

# hence the stop loss trails the market price. If the market price falls to or below the stop loss,

# the system triggers a sell order and stops running.

# In a "buy" situation, if the current price (plus stopsize) is less than the stop loss

# the stop loss is moved downwards. This mirrors the situation where the market price is decreasing,

# and the stop loss trails behind. If the market price goes up to or above the stop loss, the system triggers a buy order and stops running.

# Running the Process: The run method keeps the trailing stop loss system running.

# It prints the status, updates the stop loss and waits for the defined interval before

# repeating the process. The script runs continuously until a buy or sell order is executed.

# So, this Python script correctly implements the trailing stop loss theory as per your description.

# However, please remember that this is a basic implementation and for a more robust, production-level system,

# you'd likely want to include additional features and error handling capabilities. Always ensure thorough testing

# is conducted in a safe and secure environment before using such scripts for real trading.

# Initialization: When an instance of StopTrail is created, it takes in a market symbol (e.g., "BTC/USD"),

# a type of trade ("buy" or "sell"), the size of the stop (the trailing amount), and an interval in seconds at which to update the stop loss.

# During initialization, the Binance client is set up with your API keys, and the initial stop loss price is set by calling initialize_stop.

# Setting the initial stop loss: The initialize_stop method sets the initial stop loss based on the current market price and the trailing stop size. For a "buy" order, it sets the stop loss above the current price, and for a "sell" order, it sets it below the current price.

# Running the trailing stop loss system: The run method starts the trailing stop loss system.

# As long as the running attribute is True, it prints the current status of the system, updates the stop loss,

# and then waits for the specified interval before repeating the process.

# Updating the stop loss: The update_stop method is where the main logic of the trailing stop loss system is implemented.

# In a "sell" mode, if the current market price (minus the trailing stop size) is greater than the

# existing stop loss, the stop loss is updated to the higher price. If the market price falls to or below the stop loss,

# a sell order is triggered, and the system stops running.

# In a "buy" mode, if the current market price (plus the trailing stop size) is less than the existing stop loss,

# the stop loss is updated to the lower price. If the market price rises to or above the stop loss, a buy order is triggered, and the system stops running.

# Executing a trade: When the market price hits the stop loss, a trade is executed. For a "sell" order,

# it sells your entire balance for the given market. For a "buy" order, it uses all your available balance of

# the quote currency to buy the base currency. After executing the trade, the system stops running.

# So the flow of operations would be:

# Initialize StopTrail with market, type, stopsize, interval ->

# Set initial stop loss based on type ->

# Start running ->

# Print status ->

# Check if stop loss should be updated or a trade should be executed ->

# Wait for the interval ->

# Repeat the process (print status, update stop, wait) until a trade is executed.

# After a trade is executed, you would typically create a new StopTrail instance for the next trade.

# The trailing stop loss becomes active and the stop loss value gets updated within the update_stop method in

# your Python script. Here's how it happens for each condition:

# Sell Type Order:

# If you're selling, the current market price minus the stopsize is checked against the current stoploss.

# If it's greater, that means the market price has risen above the current stop loss level by the stopsize amount.

# The stoploss gets updated to price - stopsize. This is the trailing stop loss moving up with the market price.

# If the market price falls to or below the current stoploss, a sell order is executed, and the running flag is set to False, stopping the system.

# Buy Type Order:

# If you're buying, the current market price plus the stopsize is checked against the current stoploss.

# If it's lower, that means the market price has fallen below the current stop loss level by the stopsize amount.

# The stoploss gets updated to price + stopsize. This is the trailing stop loss moving down with the market price.

# If the market price rises to or above the current stoploss, a buy order is executed, and the running flag is set to False, stopping the system.

# In both cases, the trailing stop loss gets activated when the market price moves in a favorable direction

# by the stopsize amount, and it gets deactivated when the market price moves in an unfavorable direction and hits

# the current stop loss level. The activation price, therefore, would be the market price when the stoploss gets updated,

# plus or minus the stopsize, depending on the order type.
__init__ Method: Initializes the StopTrail object with initial values.
get_balance Method: Returns the current balance.
initialize_stop Method: Sets the initial stop loss based on the type of order ("buy" or "sell").
get_random_price Method: Simulates price fluctuation.
update_data Method: Updates the DataFrame with the latest market price and stop loss.
update_stop Method: Updates the stop loss based on the latest market price and triggers buy/sell if conditions are met.
print_status Method: Prints the current status of the trailing stop loss.
run Method: Keeps the trailing stop loss running and updates it at regular intervals.
buy Method
amount and price: The quantity of the asset to buy and the price at which to buy.
current_balance: Decreases by the total cost of the buy order (amount * price).
asset_balance: Increases by the amount bought.
current_price: Updated to the buy price.
stoploss: Updated using initialize_stop().
data DataFrame: Updated with the new row of market price, stop size, and stop loss.





# test - command
```
    python3 -m unittest -k test_initialize_stop_buy
```

-m unittest: the -m flag tells python to run a module as scripts, unittest is module unit testing framework

-k test_initialize_stop_buy : -k flag allow us to run only the tests whose name matches the pattern providedBackend : handle API requests coming, execute the corresponding operations
starting or stopping the trading bot, updating stop loss value, fetching current status

- Flask : handle HTTP request and send responses in JSON format

Frontend : provide a user interface

 Homepage:
Title: "Trailing Stop Loss Simulator".
Description: A brief explanation of what a trailing stop loss is and how the simulator works.
Input Fields:
Market Symbol: Dropdown or text input for entering the market symbol (e.g., NEO/BTC or NEO/USDT).
Stop Size: Numeric input to specify the stop size.
Trail Type: Dropdown to select either "buy" or "sell".
Interval: Numeric input (with a default value) to specify how often the simulator should check for price changes.
Buttons:
Start Simulation: Begins the trailing stop loss simulation.
Stop Simulation: Halts the simulation.
Real-time Display:
Live Chart: Plotting the simulated asset price over time. Highlight the stop loss level on the same chart.
Current Status Panel: Displaying real-time data such as the current price, stop loss value, and trail type.
Historical Data Table: Displaying a table with columns for 'Market Price', 'Stop Size', and 'Stoploss', updated as the simulation progresses.
2. Backend Interaction:
Endpoints:
Start Endpoint: Triggered when the "Start Simulation" button is clicked. It initializes the trailing stop loss with the provided parameters.
Update Endpoint: Called at regular intervals (specified by the user). It gets the current status, including the simulated market price, updated stop loss, and historical data.
Stop Endpoint: Triggered when the "Stop Simulation" button is clicked. It halts the simulation.
Websockets (Optional but recommended):
For a smoother real-time experience, Websockets can be used to push updates from the backend to the frontend.
3. Notifications & Alerts:
Pop-up or visual notifications on the UI whenever the stop loss is triggered or updated.
4. Styling & Responsiveness:
Use CSS frameworks like Bootstrap to ensure the UI is clean, professional, and responsive (looks good on both desktop and mobile devices).
5. Explanation & Learning Panel (Optional):
A sidebar or section where users can learn more about trailing stop losses. This can include:
What a trailing stop loss is.
How it's different from a regular stop loss.
Why and when traders use it.
A step-by-step explanation of the simulation as it progresses.
