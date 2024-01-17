import asyncio
import websockets
import psutil
import json
from datetime import datetime
import logging

connected_clients = set()

peak_cpu_usage = 0
peak_memory_usage = 0
peak_disk_usage = 0

async def collect_and_send_system_metrics():
    global peak_cpu_usage, peak_memory_usage, peak_disk_usage

    while True:
        # Collect system metrics
        current_cpu = psutil.cpu_percent(interval=None)
        current_memory = psutil.virtual_memory().percent
        current_disk = psutil.disk_usage('/').percent

        # Check for peak values
        peak_cpu_usage = max(peak_cpu_usage, current_cpu)
        peak_memory_usage = max(peak_memory_usage, current_memory)
        peak_disk_usage = max(peak_disk_usage, current_disk)


        metrics = {
            'time': datetime.utcnow().isoformat(),
            'cpu': current_cpu,
            'memory': current_memory,
            'disk': current_disk,
            'peak_cpu': peak_cpu_usage,
            'peak_memory': peak_memory_usage,
            'peak_disk': peak_disk_usage
        }

        metrics_json = json.dumps(metrics)
        logging.info(f"Collected Metrics: {metrics_json}")
        print(f"Collected Metrics:{metrics_json}")

        # Send metrics to all connected clients
        if connected_clients:
            await asyncio.wait([client.send(metrics_json) for client in connected_clients])
        
        await asyncio.sleep(1)  # Collect metrics every second

async def register_client(websocket):
    connected_clients.add(websocket)
    try:
        await websocket.wait_closed()
    finally:
        connected_clients.remove(websocket)

async def websocket_server(websocket, path):
    await register_client(websocket)

def log_operation(operation_name, start=True):
    cpu_usage = psutil.cpu_percent()
    memory_usage = psutil.virtual_memory().percent
    logging.info(f"{operation_name} {'Start' if start else 'End'}: CPU: {cpu_usage}%, Memory: {memory_usage}%")

# Example usage
def initiate_orders():
    log_operation("Initiate Orders", start=True)
    # Order initiation logic...
    log_operation("Initiate Orders", start=False)

def update_orders():
    log_operation("Update Orders", start=True)
    # Order update logic...
    log_operation("Update Orders", start=False)

    

# Start the server
start_server = websockets.serve(websocket_server, "localhost", 6789)

# Run the server and metrics collector together
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().create_task(collect_and_send_system_metrics())
asyncio.get_event_loop().run_forever()
