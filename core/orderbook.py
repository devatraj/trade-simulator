# app/core/orderbook.py

import bisect

class OrderBook:
    def __init__(self):
        self.bids = []  # Max-heap like: highest price first
        self.asks = []  # Min-heap like: lowest price first

    def update(self, bids, asks):
        self.bids = sorted(
            [(float(p), float(q)) for p, q, *_ in bids if float(q) > 0],
            key=lambda x: -x[0]
        )
        self.asks = sorted(
            [(float(p), float(q)) for p, q, *_ in asks if float(q) > 0],
            key=lambda x: x[0]
        )


    def simulate_buy(self, quantity):
        return self._simulate(self.asks, quantity)

    def simulate_sell(self, quantity):
        return self._simulate(self.bids, quantity)

    def _simulate(self, book_side, quantity):
        """
        Simulate market order by consuming depth from book_side.
        """
        total_cost = 0.0
        qty_left = quantity

        for price, avail_qty in book_side:
            if qty_left <= 0:
                break
            trade_qty = min(avail_qty, qty_left)
            total_cost += trade_qty * price
            qty_left -= trade_qty

        avg_price = total_cost / quantity if quantity > 0 else 0
        return {
            "quantity": quantity,
            "avg_price": avg_price,
            "cost": total_cost,
            "unfilled_qty": qty_left
        }

    def get_top_of_book(self):
        return {
            "best_bid": self.bids[0] if self.bids else None,
            "best_ask": self.asks[0] if self.asks else None
        }
