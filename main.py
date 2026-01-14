from dataclasses import dataclass
from bisect import insort
from collections import deque
import random
import time
'''
order class with two types of orders: buy and sell 
both orders are Limit orders
'''
@dataclass
class Order:
    order_id: int
    side: str
    price: float
    quantity: int

# defining the order book class
'''
has methods to add, cancel orders, get best bid/ask and print the order book
also has private methods to match buy/sell orders and add orders to the book
'''
class OrderBook:
    def __init__(self):
        self.bids = {}
        self.asks = {}

        self.bid_prices = []
        self.ask_prices = []

        self.order_map = {}


    #adding an order
    def add_order(self, order: Order):
        if order.side == "buy":
            self._match_buy(order)
        elif order.side == "sell":
            self._match_sell(order)
        else:
            raise ValueError("side must be 'buy' or 'sell'")

        if order.quantity > 0:
            self._add_to_book(order)

    def cancel_order(self, order_id: int):
        if order_id not in self.order_map:
            return

        side, price = self.order_map.pop(order_id)
        book = self.bids if side == "buy" else self.asks
        prices = self.bid_prices if side == "buy" else self.ask_prices

        queue = book[price]
        queue = deque(o for o in queue if o.order_id != order_id)

        if queue:
            book[price] = queue
        else:
            del book[price]
            prices.remove(price)

    def best_bid(self):
        return self.bid_prices[0] if self.bid_prices else None

    def best_ask(self):
        return self.ask_prices[0] if self.ask_prices else None

    def print_book(self):
        print("\n--- ORDER BOOK ---")

        print("\nAsks (price ↑):")
        for p in self.ask_prices:
            total = sum(o.quantity for o in self.asks[p])
            print(f"{p:.2f} -> {total}")

        print("\nBids (price ↓):")
        for p in self.bid_prices:
            total = sum(o.quantity for o in self.bids[p])
            print(f"{p:.2f} -> {total}")





    def _match_buy(self, order: Order):
        while self.ask_prices and order.quantity > 0:
            best_ask = self.ask_prices[0]

            if order.price < best_ask:
                break

            queue = self.asks[best_ask]
            resting = queue[0]

            trade_qty = min(order.quantity, resting.quantity)
            order.quantity -= trade_qty
            resting.quantity -= trade_qty

            if resting.quantity == 0:
                queue.popleft()
                self.order_map.pop(resting.order_id, None)

                if not queue:
                    del self.asks[best_ask]
                    self.ask_prices.pop(0)

    def _match_sell(self, order: Order):
        while self.bid_prices and order.quantity > 0:
            best_bid = self.bid_prices[0]

            if order.price > best_bid:
                break

            queue = self.bids[best_bid]
            resting = queue[0]

            trade_qty = min(order.quantity, resting.quantity)
            order.quantity -= trade_qty
            resting.quantity -= trade_qty

            if resting.quantity == 0:
                queue.popleft()
                self.order_map.pop(resting.order_id, None)

                if not queue:
                    del self.bids[best_bid]
                    self.bid_prices.pop(0)



    def _add_to_book(self, order: Order):
        if order.side == "buy":
            book = self.bids
            prices = self.bid_prices
        else:
            book = self.asks
            prices = self.ask_prices

        if order.price not in book:
            book[order.price] = deque()
            insort(prices, order.price)

            if order.side == "buy":

                prices.sort(reverse=True)

        book[order.price].append(order)
        self.order_map[order.order_id] = (order.side, order.price)


# =========================
# Demo / Quick Test
# =========================
def random_order(order_id, mid_price=100.0, spread=5.0, max_qty=10):
    side = random.choice(["buy", "sell"])

    if side == "buy":
        price = round(random.uniform(mid_price - spread, mid_price), 2)
    else:
        price = round(random.uniform(mid_price, mid_price + spread), 2)

    quantity = random.randint(1, max_qty)

    return Order(order_id, side, price, quantity)

def stress_test(num_orders=100_000):
    ob = OrderBook()

    start = time.perf_counter()

    for i in range(1, num_orders + 1):
        order = random_order(i)
        ob.add_order(order)

    end = time.perf_counter()

    elapsed = end - start
    ops = num_orders / elapsed


    print(f"no of Orders processed : {num_orders}")
    print(f"Time taken       : {elapsed:.4f} seconds")
    print(f"Orders per second  : {ops:,.5f}")




if __name__ == "__main__":
    stress_test(1_000_000)
