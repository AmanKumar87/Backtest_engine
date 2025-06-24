# event_system.py
import queue

class Event:
    """
    Base class for all event objects.
    """
    pass

class MarketEvent(Event):
    """
    Handles the event of receiving a new market update (a new bar).
    It contains no data itself but signals the system that new data is available.
    """
    def __init__(self):
        self.type = 'MARKET'

class SignalEvent(Event):
    """
    Handles the event of a Strategy object generating a signal.
    It contains the symbol, timestamp, signal direction, and strength.
    """
    def __init__(self, symbol, timestamp, signal_type, strength=1.0):
        self.type = 'SIGNAL'
        self.symbol = symbol
        self.timestamp = timestamp
        self.signal_type = signal_type  # 'LONG', 'SHORT', 'EXIT'
        self.strength = strength

class OrderEvent(Event):
    """
    Handles the event of sending an Order to an execution system.
    The order contains the symbol, order type, quantity, and direction.
    """
    def __init__(self, symbol, order_type, quantity, direction):
        self.type = 'ORDER'
        self.symbol = symbol
        self.order_type = order_type    # 'MKT' (Market) or 'LMT' (Limit)
        self.quantity = quantity
        self.direction = direction      # 'BUY' or 'SELL'

class FillEvent(Event):
    """
    Encapsulates the notion of a filled order, as returned from a brokerage.
    Stores the quantity of an instrument actually filled and at what price.
    Furthermore, it stores the commission of the trade from the brokerage.
    """
    def __init__(self, timestamp, symbol, direction, quantity, fill_price, commission):
        self.type = 'FILL'
        self.timestamp = timestamp
        self.symbol = symbol
        self.direction = direction
        self.quantity = quantity
        self.fill_price = fill_price
        self.commission = commission

# The central event bus for the entire system.
# Components will put events here and other components will pull them out.
event_queue = queue.Queue()