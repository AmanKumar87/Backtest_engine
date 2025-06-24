# backtest.py
import os
import sys
import queue

from event_system import MarketEvent, SignalEvent, OrderEvent, FillEvent, event_queue
from engine_components import DataHandler, Portfolio, LoggingHandler, ExecutionHandler
from statistics import Statistics
from strategies.buy_and_hold_strategy import BuyAndHoldStrategy

def main():
    print("--- Terminal Backtesting Engine ---")

    # --- Configuration ---
    run_name = "phase3_advanced_plot"
    symbol = 'RELIANCE.NS'
    initial_capital = 100000.0
    csv_filepath = os.path.join('data', 'stocks', f'{symbol}.csv')
    commission_rate = 0.001
    slippage_pct = 0.0005
    
    print(f"\nStarting new test run: '{run_name}' on {symbol}")
    
    # --- Initialization ---
    data_handler = DataHandler(csv_filepath=csv_filepath)
    portfolio = Portfolio(initial_capital=initial_capital)
    execution_handler = ExecutionHandler(commission_rate=commission_rate, slippage_pct=slippage_pct)
    strategy = BuyAndHoldStrategy(symbol=symbol, data_handler=data_handler)
    logger = LoggingHandler(run_name=run_name)

    # --- Main Event Loop ---
    while True:
        timestamp, bar_data = data_handler.stream_next_bar()
        if timestamp is None:
            break
        while not event_queue.empty():
            try:
                event = event_queue.get(False)
            except queue.Empty:
                break
            else:
                if event:
                    if event.type == 'MARKET':
                        strategy.calculate_signals(timestamp, bar_data)
                    elif event.type == 'SIGNAL':
                        logger.on_signal(event)
                        portfolio.on_signal(event)
                    elif event.type == 'ORDER':
                        execution_handler.execute_order(event, bar_data)
                    elif event.type == 'FILL':
                        portfolio.on_fill(event)
                        logger.on_fill(event)
    
    print("\n--- Backtest Finished: Generating Report & Chart ---")

    # --- Post-Backtest Analysis ---
    stats = Statistics(
        trades_log_path=logger.trade_log_path,
        portfolio=portfolio,
        data_handler=data_handler
    )
    report_data = stats.generate_report()
    
    # Print report
    print("\n" + "="*50)
    print(f"      PERFORMANCE REPORT for '{run_name}'")
    print("="*50)
    for key, value in report_data.items():
        print(f"{key:<35} | {value}")
    print("="*50)

    # Save report to file
    report_path = os.path.join('results', f'{run_name}_report.txt')
    with open(report_path, 'w') as f:
        for key, value in report_data.items():
            f.write(f"{key}: {value}\n")
    print(f"\nReport saved to {report_path}")

    # --- NEW: Generate and save the single advanced chart ---
    chart_path = os.path.join('results', f'{run_name}_analysis_chart.png')
    stats.plot_advanced_charts(
        output_path=chart_path, 
        title=f"Performance Analysis for '{run_name}' on {symbol}"
    )
    interactive_chart_path = os.path.join('results', f'{run_name}_interactive_chart.html')
    stats.plot_interactive_ohlc_chart(
        output_path=interactive_chart_path,
        title=f"Interactive Trade Chart for '{run_name}' on {symbol}"
    )
    print(f"Log files saved in the /logs directory.")

if __name__ == "__main__":
    main()