# High-Performance Limit Order Book (LOB)

A lightweight, high-performance **limit order book matching engine** implemented in pure Python. This project simulates a real financial exchange, matching buy and sell limit orders using **strict Price-Time Priority**, the same rule enforced by professional trading venues.

Built to be simple, fast, and educational without pretending Python is C++.

---

## Features

* **Price-Time Priority (FIFO)**
  Orders are matched first by best price, then by arrival time.

* **Efficient Data Structures**
  Uses `collections.deque` for *O(1)* FIFO execution and `bisect` to maintain sorted price levels.

* **Constant-Time Order Tracking**
  Internal order map enables *O(1)* lookups and efficient cancellations.

* **High-Volume Stress Testing**
  Built-in simulation benchmarks the engine with **1,000,000+ orders**.

---

## Core Concepts

### 1. Matching Logic

When an order enters the book, the engine checks the opposite side:

* **Buy orders** match against the **lowest available Ask**
* **Sell orders** match against the **highest available Bid**

If the order price **crosses the spread**, trades execute immediately. If not, the order is **posted** as a resting limit order.

---

### 2. Price-Time Priority Queue

The order book enforces fairness and determinism using:

* **Price Priority**
  Maintained via sorted price lists (`bid_prices`, `ask_prices`).

* **Time Priority**
  Each price level stores orders in a `deque`, ensuring FIFO execution.

---

## Architecture Overview

```text
OrderBook
 ├── bids: dict[price -> deque[Order]]
 ├── asks: dict[price -> deque[Order]]
 ├── bid_prices: sorted list (descending)
 ├── ask_prices: sorted list (ascending)
 └── order_map: dict[order_id -> Order]
```

This layout ensures:

* Fast best-bid / best-ask access
* Deterministic matching
* Minimal memory overhead

---

##Technical Stack

| Component     | Implementation      | Purpose                                    |
| ------------- | ------------------- | ------------------------------------------ |
| Order Storage | `dict` + `deque`    | FIFO execution at each price level         |
| Price Sorting | `bisect.insort`     | Maintains Best Bid / Best Ask efficiently  |
| Object Model  | `@dataclass`        | Lightweight, readable order representation |
| Benchmarking  | `time.perf_counter` | High-resolution performance measurement    |

---

## Performance

Designed for **high throughput** on standard hardware:

* **Order Capacity:** 1,000,000+ orders
* **Throughput:** ~480,000 orders/sec

Performance scales linearly with order volume and remains stable under stress tests.

---

## Getting Started

### Prerequisites

* Python **3.7+**

### Run the Engine

Execute the default stress test (1 million orders):

```bash
python order_book.py
```

---

##  Usage Example

```python
from order_book import OrderBook, Order

# Initialize the order book
ob = OrderBook()

# Add a Buy Order
ob.add_order(Order(order_id=1, side="buy", price=100.0, quantity=10))

# Add a Sell Order that matches
ob.add_order(Order(order_id=2, side="sell", price=100.0, quantity=5))

# Query best bid
print(ob.best_bid())
```

---

## Benchmarking

The engine includes a built-in stress test that:

* Generates randomized buy/sell orders
* Measures matching throughput
* Validates correctness under load

Ideal for experimentation and optimization.

---

##  Project Goals

* Demonstrate **exchange-grade matching logic**
* Maintain **clarity over cleverness**
* Serve as a foundation for deeper work in:

  * Market microstructure
  * Quantitative trading systems
  * Low-latency system design

---

## Disclaimer

This project is for **educational and research purposes only**. It is **not** intended for live trading or production use.

---

## 📄 License

MIT License. Do whatever you want, just don’t blame the code when you lose money.
