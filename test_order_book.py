import unittest

from order_book import Order, OrderBook


class TestOrderBook(unittest.TestCase):
    def setUp(self):
        self.ob = OrderBook()

    def test_resting_orders_set_best_prices(self):
        self.ob.add_order(Order(1, "buy", 99.0, 5))
        self.ob.add_order(Order(2, "sell", 101.0, 5))
        self.assertEqual(self.ob.best_bid(), 99.0)
        self.assertEqual(self.ob.best_ask(), 101.0)

    def test_empty_book_best_prices_are_none(self):
        self.assertIsNone(self.ob.best_bid())
        self.assertIsNone(self.ob.best_ask())

    def test_invalid_side_raises(self):
        with self.assertRaises(ValueError):
            self.ob.add_order(Order(1, "hold", 100.0, 1))

    def test_non_crossing_orders_rest(self):
        self.ob.add_order(Order(1, "buy", 99.0, 5))
        self.ob.add_order(Order(2, "sell", 101.0, 5))
        # nothing crosses, both remain
        self.assertEqual(self.ob.best_bid(), 99.0)
        self.assertEqual(self.ob.best_ask(), 101.0)

    def test_full_match_removes_resting_order(self):
        self.ob.add_order(Order(1, "sell", 100.0, 5))
        self.ob.add_order(Order(2, "buy", 100.0, 5))
        self.assertIsNone(self.ob.best_ask())
        self.assertIsNone(self.ob.best_bid())

    def test_partial_fill_leaves_remainder_resting(self):
        self.ob.add_order(Order(1, "sell", 100.0, 5))
        # incoming buy bigger than resting -> remainder posts as bid
        self.ob.add_order(Order(2, "buy", 100.0, 8))
        self.assertIsNone(self.ob.best_ask())
        self.assertEqual(self.ob.best_bid(), 100.0)
        self.assertEqual(self.ob.bids[100.0][0].quantity, 3)

    def test_resting_partially_consumed(self):
        self.ob.add_order(Order(1, "sell", 100.0, 10))
        self.ob.add_order(Order(2, "buy", 100.0, 4))
        self.assertEqual(self.ob.best_ask(), 100.0)
        self.assertEqual(self.ob.asks[100.0][0].quantity, 6)

    def test_buy_crosses_multiple_ask_levels(self):
        self.ob.add_order(Order(1, "sell", 100.0, 5))
        self.ob.add_order(Order(2, "sell", 101.0, 5))
        self.ob.add_order(Order(3, "buy", 101.0, 8))
        # consumes all of 100 (5) and 3 of 101, leaving 2 at 101
        self.assertEqual(self.ob.best_ask(), 101.0)
        self.assertEqual(self.ob.asks[101.0][0].quantity, 2)
        self.assertIsNone(self.ob.best_bid())

    def test_price_priority_best_ask_is_lowest(self):
        self.ob.add_order(Order(1, "sell", 103.0, 1))
        self.ob.add_order(Order(2, "sell", 101.0, 1))
        self.ob.add_order(Order(3, "sell", 102.0, 1))
        self.assertEqual(self.ob.best_ask(), 101.0)

    def test_price_priority_best_bid_is_highest(self):
        self.ob.add_order(Order(1, "buy", 97.0, 1))
        self.ob.add_order(Order(2, "buy", 99.0, 1))
        self.ob.add_order(Order(3, "buy", 98.0, 1))
        self.assertEqual(self.ob.best_bid(), 99.0)

    def test_time_priority_fifo_within_price_level(self):
        self.ob.add_order(Order(1, "sell", 100.0, 5))
        self.ob.add_order(Order(2, "sell", 100.0, 5))
        # earliest order (id 1) should be filled first
        self.ob.add_order(Order(3, "buy", 100.0, 5))
        self.assertNotIn(1, self.ob.order_map)
        self.assertIn(2, self.ob.order_map)
        self.assertEqual(self.ob.asks[100.0][0].order_id, 2)

    def test_cancel_removes_order(self):
        self.ob.add_order(Order(1, "buy", 99.0, 5))
        self.ob.add_order(Order(2, "buy", 98.0, 5))
        self.ob.cancel_order(1)
        self.assertNotIn(1, self.ob.order_map)
        self.assertEqual(self.ob.best_bid(), 98.0)

    def test_cancel_only_order_at_level_clears_level(self):
        self.ob.add_order(Order(1, "sell", 100.0, 5))
        self.ob.cancel_order(1)
        self.assertIsNone(self.ob.best_ask())
        self.assertEqual(self.ob.ask_prices, [])

    def test_cancel_unknown_order_is_noop(self):
        self.ob.add_order(Order(1, "buy", 99.0, 5))
        self.ob.cancel_order(999)
        self.assertEqual(self.ob.best_bid(), 99.0)

    def test_cancelled_order_is_skipped_in_matching(self):
        self.ob.add_order(Order(1, "sell", 100.0, 5))
        self.ob.add_order(Order(2, "sell", 100.0, 5))
        self.ob.cancel_order(1)
        # incoming buy should match order 2, not the cancelled order 1
        self.ob.add_order(Order(3, "buy", 100.0, 5))
        self.assertIsNone(self.ob.best_ask())
        self.assertNotIn(2, self.ob.order_map)

    def test_conservation_of_quantity_after_random_run(self):
        import random
        random.seed(42)
        ob = OrderBook()
        for i in range(1, 5001):
            side = random.choice(["buy", "sell"])
            price = round(random.uniform(95.0, 105.0), 2)
            qty = random.randint(1, 10)
            ob.add_order(Order(i, side, price, qty))
        # book invariant: best bid must never exceed best ask
        bb, ba = ob.best_bid(), ob.best_ask()
        if bb is not None and ba is not None:
            self.assertLess(bb, ba)


class TestThroughput(unittest.TestCase):
    def test_engine_processes_over_1m_orders_per_sec(self):
        import time

        from order_book import random_order

        n = 500_000
        # generation is excluded from the timed region
        orders = [random_order(i) for i in range(1, n + 1)]
        ob = OrderBook()
        add_order = ob.add_order

        start = time.perf_counter()
        for order in orders:
            add_order(order)
        ops = n / (time.perf_counter() - start)

        self.assertGreater(
            ops, 1_000_000, f"engine throughput {ops:,.0f}/s below 1M/s target"
        )


if __name__ == "__main__":
    unittest.main()
