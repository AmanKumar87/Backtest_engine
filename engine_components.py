# engine_components.py
import pandas as pd
import os # <-- THE MISSING IMPORT

from event_system import MarketEvent, SignalEvent, OrderEvent, FillEvent, event_queue

class DataHandler:
    """
    DataHandler reads market data from a CSV file and provides it to the system
    bar by bar, placing a MarketEvent on the queue for each bar.
    """
    def __init__(self, csv_filepath: str):
        self.csv_filepath = csv_filepath
        self.data = pd.read_csv(
            csv_filepath,
            header=0,
            skiprows=[1, 2],
            index_col=0,
            parse_dates=True
        )
        self.data.index.name = 'Date'
        self._data_generator = self.data.iterrows()
        print(f"DataHandler initialized for {csv_filepath}. {len(self.data)} rows loaded successfully.")

    def stream_next_bar(self) -> tuple[pd.Timestamp, pd.Series] | tuple[None, None]:
        try:
            timestamp, bar_data = next(self._data_generator)
        except StopIteration:
            print("End of data stream reached.")
            return None, None
        else:
            event_queue.put(MarketEvent())
            return timestamp, bar_data

class Portfolio:
    """
    The Portfolio class handles the positions and market value of all
    instruments at a resolution of a "bar".
    """
    def __init__(self, initial_capital: float = 100000.0):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions = {}
        print(f"Portfolio initialized with Capital: {self.initial_capital:.2f}")

    def on_signal(self, signal: SignalEvent) -> None:
        if signal.signal_type == 'LONG' and signal.symbol not in self.positions:
            order = OrderEvent(
                symbol=signal.symbol,
                order_type='MKT',
                quantity=10,
                direction='BUY'
            )
            event_queue.put(order)
            print(f"Portfolio generated ORDER: BUY 10 units of {signal.symbol}")
        elif signal.signal_type == 'EXIT' and signal.symbol in self.positions:
            quantity_to_sell = self.positions[signal.symbol]
            order = OrderEvent(
                symbol=signal.symbol,
                order_type='MKT',
                quantity=quantity_to_sell,
                direction='SELL'
            )
            event_queue.put(order)
            print(f"Portfolio generated ORDER: SELL {quantity_to_sell} units of {signal.symbol}")

    def on_fill(self, fill: FillEvent) -> None:
        if fill.direction == 'BUY':
            self.cash -= (fill.fill_price * fill.quantity) + fill.commission
            self.positions[fill.symbol] = self.positions.get(fill.symbol, 0) + fill.quantity
        elif fill.direction == 'SELL':
            self.cash += (fill.fill_price * fill.quantity) - fill.commission
            self.positions.pop(fill.symbol, None)
        print(f"Portfolio updated on FILL: Cash is now {self.cash:.2f}")


# engine_components.py (LoggingHandler update)

class LoggingHandler:
    """
    The LoggingHandler is responsible for writing all events (trades and signals)
    to log files for later analysis.
    """
    def __init__(self, run_name: str, log_dir: str = 'logs'):
        self.log_dir = log_dir
        self.run_name = run_name
        
        # --- Setup for Trade Log ---
        self.trade_log_path = os.path.join(self.log_dir, f"{self.run_name}_trades.log")
        with open(self.trade_log_path, 'w') as f:
            f.write("Execution_Timestamp|Symbol|Action|Quantity|Price|Commission|P/L\n")
        print(f"Trade log initialized at: {self.trade_log_path}")
        
        # --- NEW: Setup for Signal Log ---
        self.signal_log_path = os.path.join(self.log_dir, f"{self.run_name}_signals.log")
        with open(self.signal_log_path, 'w') as f:
            f.write("Signal_Timestamp|Symbol|Signal_Type|Notes\n")
        print(f"Signal log initialized at: {self.signal_log_path}")

    def on_fill(self, fill_event: FillEvent) -> None:
        """ Takes a FillEvent and writes its contents to the trade log. """
        pnl = 0.0 # Placeholder for now
        log_line = (
            f"{fill_event.timestamp.strftime('%Y-%m-%d %H:%M:%S')}|"
            f"{fill_event.symbol}|"
            f"{fill_event.direction}|"
            f"{fill_event.quantity}|"
            f"{fill_event.fill_price:.2f}|"
            f"{fill_event.commission:.2f}|"
            f"{pnl:.2f}\n"
        )
        with open(self.trade_log_path, 'a') as f:
            f.write(log_line)
    
    # --- NEW: Method to log signals ---
    def on_signal(self, signal_event: SignalEvent, notes: str = "") -> None:
        """ Takes a SignalEvent and writes its contents to the signal log. """
        log_line = (
            f"{signal_event.timestamp.strftime('%Y-%m-%d %H:%M:%S')}|"
            f"{signal_event.symbol}|"
            f"{signal_event.signal_type}|"
            f"{notes}\n"
        )
        with open(self.signal_log_path, 'a') as f:
            f.write(log_line)
# engine_components.py (continued)
import random

class ExecutionHandler:
    """
    The ExecutionHandler simulates the interaction with a brokerage.
    It takes OrderEvents and produces FillEvents, incorporating costs
    like commission and slippage.
    """
    def __init__(self, commission_rate: float = 0.001, slippage_pct: float = 0.0005):
        """
        Initializes the handler with a commission rate and slippage model.
        :param commission_rate: A fractional commission per trade (e.g., 0.001 for 0.1%).
        :param slippage_pct: A fractional slippage percentage.
        """
        self.commission_rate = commission_rate
        self.slippage_pct = slippage_pct
        print(f"ExecutionHandler initialized with Commission: {self.commission_rate*100:.3f}%, Slippage: {self.slippage_pct*100:.3f}%")

    def execute_order(self, order_event: OrderEvent, latest_bar_data) -> None:
        """
        Takes an OrderEvent and simulates its execution.
        Puts a FillEvent onto the event queue.
        """
        # --- Slippage Simulation ---
        # Slippage is the difference between the expected price and the actual fill price.
        # We simulate it as a random percentage of the closing price.
        # For a BUY order, slippage is positive (we pay more).
        # For a SELL order, slippage is negative (we get less).
        if order_event.direction == 'BUY':
            slippage = latest_bar_data['Close'] * self.slippage_pct * random.random()
        else: # SELL
            slippage = -latest_bar_data['Close'] * self.slippage_pct * random.random()
        
        fill_price = latest_bar_data['Close'] + slippage

        # --- Commission Calculation ---
        commission = fill_price * order_event.quantity * self.commission_rate

        # --- Create the Fill Event ---
        # The fill occurs at the same timestamp as the market data bar that triggered it.
        fill_event = FillEvent(
            timestamp=latest_bar_data.name, # .name gives the index (timestamp) of the Series
            symbol=order_event.symbol,
            direction=order_event.direction,
            quantity=order_event.quantity,
            fill_price=fill_price,
            commission=commission
        )
        
        # Put the new FillEvent onto the queue for the Portfolio to process
        event_queue.put(fill_event)
        print(f"ExecutionHandler generated FILL: {order_event.direction} {order_event.quantity} {order_event.symbol} at ~{fill_price:.2f}")