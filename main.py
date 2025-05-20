# app/main.py

import asyncio
import logging
import json
import websockets

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.insert(0, project_root)

from app.core.orderbook import OrderBook
from app.websocket.ws_client import WebSocketClient

# -------------------- Setup --------------------
OKX_WS_URL = "wss://ws.okx.com:8443/ws/v5/public"
orderbook = OrderBook()
clients = set()

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# -------------------- FastAPI App --------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow frontend dev anywhere
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------- WebSocket Route --------------------
@app.websocket("/ws/orderbook")
async def orderbook_stream(websocket: WebSocket):
    await websocket.accept()
    clients.add(websocket)
    try:
        while True:
            await asyncio.sleep(1)  # Passive; data is pushed via broadcast
    except:
        clients.remove(websocket)

# -------------------- REST Endpoints --------------------
@app.get("/status")
async def status():
    return {"okx_ws_connected": ws_client.connected}

@app.get("/simulate")
async def simulate():
    result = orderbook.simulate_buy(1.0)
    return result

# -------------------- Broadcast Loop --------------------
async def broadcast_orderbook():
    while True:
        if clients:
            bid, ask = orderbook.best_bid_ask()
            data = {"bid": bid, "ask": ask}
            for client in clients.copy():
                try:
                    await client.send_text(json.dumps(data))
                except:
                    clients.remove(client)
        await asyncio.sleep(0.25)

# -------------------- OKX Message Handler --------------------
async def on_message(data):
    if 'arg' in data and 'data' in data:
        for update in data['data']:
            bids = update.get('bids', [])
            asks = update.get('asks', [])
            orderbook.update(bids, asks)

            top = orderbook.get_top_of_book()
            logging.info(f"Top of Book → Best Bid: {top['best_bid']}, Best Ask: {top['best_ask']}")

            simulated = orderbook.simulate_buy(1.0)
            logging.info(f"Simulated Buy 1 BTC → Avg Price: {simulated['avg_price']:.2f}, Cost: {simulated['cost']:.2f}")
    else:
        logging.warning("⚠️ Unexpected message format")

# -------------------- OKX WS Client --------------------
ws_client = WebSocketClient(OKX_WS_URL, on_message)

async def okx_stream_loop():
    async def subscribe(ws):
        sub_msg = {
            "op": "subscribe",
            "args": [{
                "channel": "books5",
                "instId": "BTC-USDT"
            }]
        }
        await ws.send(json.dumps(sub_msg))
        logging.info("📡 Subscription sent")

    async def wrapped_connect():
        while True:
            try:
                async with websockets.connect(ws_client.url) as websocket:
                    ws_client.connected = True
                    logging.info("✅ Connected to OKX")
                    await subscribe(websocket)
                    while True:
                        msg = await websocket.recv()
                        data = json.loads(msg)
                        await ws_client.on_message(data)
            except Exception as e:
                logging.error(f"WebSocket error: {e}", exc_info=True)
                ws_client.connected = False
                await asyncio.sleep(5)

    await wrapped_connect()

# -------------------- Startup Tasks --------------------
@app.on_event("startup")
async def start_background_tasks():
    asyncio.create_task(okx_stream_loop())
    asyncio.create_task(broadcast_orderbook())

# -------------------- Entry Point --------------------
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
