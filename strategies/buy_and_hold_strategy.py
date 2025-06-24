# strategies/buy_and_hold_strategy.py
from strategies.base_strategy import BaseStrategy
from event_system import SignalEvent, event_queue

class BuyAndHoldStrategy(BaseStrategy):
    """
    A very simple strategy that buys on the first data bar and holds.
    This serves as a useful benchmark for other strategies.
    """
    def __init__(self, symbol: str, data_handler):
        super().__init__(symbol, data_handler)
        self.bought = False # A flag to ensure we only buy once

    def calculate_signals(self, event_timestamp, latest_bar_data) -> None:
        """
        For "Buy and Hold", we generate a single signal on the first bar
        and then do nothing.
        """
        if not self.bought:
            # Generate a 'LONG' signal on the first bar.
            signal = SignalEvent(
                symbol=self.symbol,
                timestamp=event_timestamp,
                signal_type='LONG'
            )
            # Put the signal onto the central event queue
            event_queue.put(signal)
            print(f"[{event_timestamp.strftime('%Y-%m-%d')}] Strategy generated SIGNAL: LONG for {self.symbol}")
            self.bought = True # Set the flag to true