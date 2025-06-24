# backtest.py
import os
import sys

# Import our new components and event system
from event_system import MarketEvent, event_queue
from engine_components import DataHandler

def main():
    """
    Main function to run the backtesting engine.
    """
    print("--- Terminal Backtesting Engine ---")

    # --- Get a unique name for the test run ---
    try:
        run_name = input("Enter a unique name for this test run (e.g., sma_crossover_test_1): ")
        if not run_name.strip():
            print("\nError: Run name cannot be empty. Exiting.")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user. Exiting.")
        sys.exit(0)

    # --- Ensure output directories exist ---
    os.makedirs('logs', exist_ok=True)
    os.makedirs('results', exist_ok=True)

    print(f"\nStarting new test run: '{run_name}'")
    
    #
    # --- Phase 1.3: Data-Driven Event Loop ---
    #
    
    # 1. Initialize the DataHandler with our sample data file
    #    In the future, this filepath will be dynamic.
    data_handler = DataHandler(csv_filepath='data/RELIANCE.NS.csv')

    # 2. The main event loop, now driven by the DataHandler
    while True:
        # Get the next bar of data. This also puts a MarketEvent on the queue.
        timestamp, bar_data = data_handler.stream_next_bar()
        
        # If the DataHandler returns None, the data stream has ended.
        if timestamp is None:
            print("\n--- Backtest Finished: No more market data. ---")
            break

        # Process events from the queue
        while not event_queue.empty():
            try:
                event = event_queue.get()
            except queue.Empty:
                break
            else:
                if event and event.type == 'MARKET':
                    # This is where we will trigger the strategy in the next step
                    print(f"--- Processing Market Event for Timestamp: {timestamp.strftime('%Y-%m-%d')} ---")
                    print(f"Data: Open={bar_data['Open']}, High={bar_data['High']}, Low={bar_data['Low']}, Close={bar_data['Close']}")
                    # In the next step, we will pass this bar_data to our strategy.
    
    print(f"\nTest run '{run_name}' complete.")

if __name__ == "__main__":
    main()