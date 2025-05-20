# app/api/websocket_server.py
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
import json
from app.core.orderbook import OrderBook

app = FastAPI()
orderbook = OrderBook()

clients = set()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow frontend dev anywhere
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws/orderbook")
async def orderbook_stream(websocket: WebSocket):
    await websocket.accept()
    clients.add(websocket)
    try:
        while True:
            # This can later receive trade simulations too
            await asyncio.sleep(0.1)
    except:
        clients.remove(websocket)

async def broadcast_orderbook():
    while True:
        if clients:
            bid, ask = orderbook.best_bid_ask()
            data = {
                "bid": bid,
                "ask": ask
            }
            for client in clients.copy():
                try:
                    await client.send_text(json.dumps(data))
                except:
                    clients.remove(client)
        await asyncio.sleep(0.25)

def start_ws_server(shared_orderbook: OrderBook):
    global orderbook
    orderbook = shared_orderbook
    loop = asyncio.get_event_loop()
    loop.create_task(broadcast_orderbook())
    uvicorn.run(app, host="0.0.0.0", port=8000)
