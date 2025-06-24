# strategies/base_strategy.py
from abc import ABC, abstractmethod
from event_system import SignalEvent, event_queue

class BaseStrategy(ABC):
    """
    BaseStrategy is an abstract base class providing an interface for all
    subsequent strategy handling objects.

    The goal of a (derived) Strategy object is to generate Signal objects
    for particular symbols based on the inputs of MarketEvents.
    """
    def __init__(self, symbol: str, data_handler):
        """
        Initialize the strategy.
        :param symbol: The stock symbol this strategy instance is responsible for.
        :param data_handler: A reference to the engine's DataHandler.
        """
        self.symbol = symbol
        self.data_handler = data_handler

    @abstractmethod
    def calculate_signals(self, event_timestamp, latest_bar_data) -> None:
        """
        Provides the mechanisms to calculate the list of signals.
        This method is called for each bar of data.

        :param event_timestamp: The timestamp of the current market event.
        :param latest_bar_data: A pandas Series containing the latest bar (OHLCV).
        """
        raise NotImplementedError("Should implement calculate_signals()")