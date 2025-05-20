# tests/test_ws_client.py
import asyncio
import logging

import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
sys.path.insert(0, project_root)

# Now you can import from `app.websocket`
from app.websocket.ws_client import WebSocketClient


logging.basicConfig(level=logging.INFO)

async def handle_orderbook(data):
    asks = data.get("asks", [])
    bids = data.get("bids", [])
    if asks and bids:
        best_ask = asks[0]
        best_bid = bids[0]
        print(f"🟢 Best Ask: {best_ask} | 🔴 Best Bid: {best_bid}")

async def main():
    url = "wss://ws.gomarket-cpp.goquant.io/ws/l2-orderbook/okx/BTC-USDT-SWAP"
    client = WebSocketClient(url, handle_orderbook)
    await client.connect()

if __name__ == "__main__":
    asyncio.run(main())
