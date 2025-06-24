# engine_components.py
import pandas as pd
from event_system import MarketEvent, event_queue

class DataHandler:
    """
    DataHandler reads market data from a CSV file and provides it to the system
    bar by bar, placing a MarketEvent on the queue for each bar.
    """
    def __init__(self, csv_filepath: str):
        """
        Initializes the data handler by loading data.
        :param csv_filepath: The absolute or relative path to the CSV data file.
        """
        self.csv_filepath = csv_filepath
        # Load the entire data file into a pandas DataFrame.
        # We use 'Date' as the index and parse it as a datetime object.
        self.data = pd.read_csv(
            csv_filepath, 
            index_col='Date', 
            parse_dates=True
        )
        # Create a generator that will yield each row of the DataFrame.
        self._data_generator = self.data.iterrows()
        print(f"DataHandler initialized for {csv_filepath}. {len(self.data)} rows loaded.")

    def stream_next_bar(self) -> tuple[pd.Timestamp, pd.Series] | tuple[None, None]:
        """
        Streams the next bar of data from the file.
        Puts a MarketEvent on the queue and returns the data.
        Returns (None, None) when the data stream is finished.
        """
        try:
            # Get the next bar from our generator
            timestamp, bar_data = next(self._data_generator)
        except StopIteration:
            # This is raised when the generator is exhausted (end of file)
            print("End of data stream reached.")
            return None, None
        else:
            # A new bar of data is available. Put a MarketEvent on the queue.
            # This signals to the rest of the system that a "tick" has occurred.
            event_queue.put(MarketEvent())
            
            # Return the data for the current bar
            return timestamp, bar_data