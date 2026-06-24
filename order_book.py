from dataclasses import dataclass
from bisect import insort
from collections import deque
import random
import time

'''
order class with two types of orders: buy and sell
both orders are Limit orders
'''
@dataclass(slots=True)
class Order:
    order_id: int
    side: str
    price: float
    quantity: int

# defining the order book class
'''
has methods to add, cancel orders, get best bid/ask and print the order book
also has private methods to match buy/sell orders and add orders to the book

Price levels are stored as deques keyed by price for FIFO (time priority).
Both price lists are kept sorted ascending with bisect.insort:
    - best ask is the first element  (lowest sell price)
    - best bid is the last element   (highest buy price)
Cancellation is O(1): the order is looked up via order_map and marked filled
(quantity 0); the now-dead entry is pruned lazily during matching/inspection.
'''
class OrderBook:
    def __init__(self):
        self.bids = {}
        self.asks = {}

        # both lists kept sorted ascending via bisect.insort
        self.bid_prices = []
        self.ask_prices = []

        self.order_map = {}

    # adding an order
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
        order = self.order_map.pop(order_id, None)
        if order is not None:
            # lazy cancellation: mark dead, prune later. O(1).
            order.quantity = 0

    def best_bid(self):
        self._prune_back(self.bids, self.bid_prices)
        return self.bid_prices[-1] if self.bid_prices else None

    def best_ask(self):
        self._prune_front(self.asks, self.ask_prices)
        return self.ask_prices[0] if self.ask_prices else None

    def print_book(self):
        print("\n--- ORDER BOOK ---")

        print("\nAsks (price ↑):")
        for p in self.ask_prices:
            total = sum(o.quantity for o in self.asks[p])
            if total:
                print(f"{p:.2f} -> {total}")

        print("\nBids (price ↓):")
        for p in reversed(self.bid_prices):
            total = sum(o.quantity for o in self.bids[p])
            if total:
                print(f"{p:.2f} -> {total}")

    # --- pruning helpers -------------------------------------------------
    # Drop cancelled/empty orders (quantity 0) and remove empty price levels.
    def _prune_front(self, book, prices):
        while prices:
            price = prices[0]
            queue = book[price]
            while queue and queue[0].quantity == 0:
                self.order_map.pop(queue[0].order_id, None)
                queue.popleft()
            if queue:
                return
            del book[price]
            prices.pop(0)

    def _prune_back(self, book, prices):
        while prices:
            price = prices[-1]
            queue = book[price]
            while queue and queue[0].quantity == 0:
                self.order_map.pop(queue[0].order_id, None)
                queue.popleft()
            if queue:
                return
            del book[price]
            prices.pop()

    # --- matching --------------------------------------------------------
    # Hot paths: opposite-side book/price-list/order_map are bound to locals
    # to avoid repeated attribute lookups in the inner loop.
    def _match_buy(self, order: Order):
        asks = self.asks
        ask_prices = self.ask_prices
        order_map = self.order_map
        while order.quantity > 0:
            self._prune_front(asks, ask_prices)
            if not ask_prices:
                break

            best_ask = ask_prices[0]
            if order.price < best_ask:
                break

            queue = asks[best_ask]
            resting = queue[0]

            oq = order.quantity
            rq = resting.quantity
            trade_qty = oq if oq < rq else rq
            order.quantity = oq - trade_qty
            resting.quantity = rq - trade_qty

            if resting.quantity == 0:
                queue.popleft()
                order_map.pop(resting.order_id, None)
                if not queue:
                    del asks[best_ask]
                    ask_prices.pop(0)

    def _match_sell(self, order: Order):
        bids = self.bids
        bid_prices = self.bid_prices
        order_map = self.order_map
        while order.quantity > 0:
            self._prune_back(bids, bid_prices)
            if not bid_prices:
                break

            best_bid = bid_prices[-1]
            if order.price > best_bid:
                break

            queue = bids[best_bid]
            resting = queue[0]

            oq = order.quantity
            rq = resting.quantity
            trade_qty = oq if oq < rq else rq
            order.quantity = oq - trade_qty
            resting.quantity = rq - trade_qty

            if resting.quantity == 0:
                queue.popleft()
                order_map.pop(resting.order_id, None)
                if not queue:
                    del bids[best_bid]
                    bid_prices.pop()

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

        book[order.price].append(order)
        self.order_map[order.order_id] = order


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

def stress_test(num_orders=1_000_000):
    ob = OrderBook()

    # Generate the orders up front so the benchmark measures the matching
    # engine itself, not the (much slower) random-order generation.
    orders = [random_order(i) for i in range(1, num_orders + 1)]

    add_order = ob.add_order
    start = time.perf_counter()
    for order in orders:
        add_order(order)
    elapsed = time.perf_counter() - start

    ops = num_orders / elapsed

    print(f"no of Orders processed : {num_orders}")
    print(f"Time taken       : {elapsed:.4f} seconds")
    print(f"Orders per second  : {ops:,.2f}")


if __name__ == "__main__":
    stress_test(1_000_000)
