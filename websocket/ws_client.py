# app/websocket/ws_client.py

import asyncio
import websockets
import json
import logging

import sys
import os

# Setup path to import app modules
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
sys.path.insert(0, project_root)

from app.core.orderbook import OrderBook

class WebSocketClient:
    def __init__(self, url, on_message=None):
        """
        :param url: WebSocket URL to connect to
        :param on_message: Optional callback function to process incoming message
        """
        self.url = url
        self.on_message = on_message
        self.connected = False
        self.orderbook = OrderBook()

    async def process_message(self, data):
        """
        Default message processor if no external callback is provided.
        Updates the orderbook and prints top of book.
        """
        if "bids" in data and "asks" in data:
            self.orderbook.update(data["bids"], data["asks"])

            best_bid = self.orderbook.get_best_bid()
            best_ask = self.orderbook.get_best_ask()

            print(f"\n📉 Best Bid: {best_bid}")
            print(f"📈 Best Ask: {best_ask}")
        else:
            logging.debug("Received message without bids/asks:", data)

    async def connect(self):
        while True:
            try:
                async with websockets.connect(self.url) as websocket:
                    self.connected = True
                    logging.info(f"✅ Connected to {self.url}")
                    while True:
                        message = await websocket.recv()
                        data = json.loads(message)

                        if self.on_message:
                            await self.on_message(data)
                        else:
                            await self.process_message(data)

            except (websockets.exceptions.ConnectionClosedError, ConnectionRefusedError) as e:
                logging.warning(f"🔄 Reconnecting due to error: {e}")
                self.connected = False
                await asyncio.sleep(5)
            except Exception as e:
                logging.error(f"Unhandled exception: {e}", exc_info=True)
                break
    async def connect_and_subscribe(self, channel, inst_id, on_message=None):

        self.on_message = on_message or self.process_message

        try:
            async with websockets.connect(self.url) as websocket:
                self.connected = True
                print(f"✅ Connected to {self.url}")

                # Send subscription message
                sub_msg = {
                    "op": "subscribe",
                    "args": [{"channel": channel, "instId": inst_id}]
                }
                await websocket.send(json.dumps(sub_msg))
                print(f"📡 Subscribed to {channel}:{inst_id}")

                # Message loop
                while True:
                    message = await websocket.recv()
                    data = json.loads(message)
                    await self.on_message(data)

        except Exception as e:
            print(f"⚠️ Connection error: {e}")