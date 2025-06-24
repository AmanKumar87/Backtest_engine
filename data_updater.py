# data_updater.py
import yfinance as yf
import os
import time

# List of NIFTY 50 tickers for Yahoo Finance (as of June 2024)
# The '.NS' suffix is crucial for National Stock Exchange listings.
NIFTY50_TICKERS = [
    'ADANIENT.NS', 'ADANIPORTS.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 
    'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 
    'BPCL.NS', 'BHARTIARTL.NS', 'BRITANNIA.NS', 'CIPLA.NS', 'COALINDIA.NS', 
    'DIVISLAB.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'GRASIM.NS', 'HCLTECH.NS', 
    'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 
    'HINDUNILVR.NS', 'ICICIBANK.NS', 'ITC.NS', 'INDUSINDBK.NS', 'INFY.NS', 
    'JSWSTEEL.NS', 'KOTAKBANK.NS', 'LTIM.NS', 'LT.NS', 'M&M.NS', 
    'MARUTI.NS', 'NTPC.NS', 'NESTLEIND.NS', 'ONGC.NS', 'POWERGRID.NS', 
    'RELIANCE.NS', 'SBILIFE.NS', 'SBIN.NS', 'SUNPHARMA.NS', 'TCS.NS', 
    'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATASTEEL.NS', 'TECHM.NS', 
    'TITAN.NS', 'ULTRACEMCO.NS', 'WIPRO.NS', 'SHRIRAMFIN.NS'
]

# Define the data directory
DATA_DIR = 'data/stocks'

def download_nifty50_data():
    """
    Downloads historical daily data for all NIFTY 50 stocks
    and saves them as individual CSV files.
    """
    print("--- Starting Download of NIFTY 50 Historical Data ---")
    
    # Ensure the target directory exists
    os.makedirs(DATA_DIR, exist_ok=True)
    
    failed_tickers = []

    for i, ticker in enumerate(NIFTY50_TICKERS):
        print(f"Downloading ({i+1}/{len(NIFTY50_TICKERS)}): {ticker}...")
        
        try:
            # Download data from 2010 to the present day
            data = yf.download(
                ticker,
                start='2010-01-01',
                end=None, # None means up to the latest available data
                interval='1d', # Daily data
                progress=False # Suppress the progress bar for a cleaner log
            )

            if data.empty:
                print(f"No data found for {ticker}. Skipping.")
                failed_tickers.append(ticker)
                continue

            # CRITICAL: Clean the data by forward-filling missing values
            # This prevents gaps in our data which can break the backtester
            data.ffill(inplace=True)
            data.bfill(inplace=True)

            # Define the output path
            output_path = os.path.join(DATA_DIR, f"{ticker}.csv")
            
            # Save the data to a CSV file
            data.to_csv(output_path)
            
            print(f"Successfully saved to {output_path}")

        except Exception as e:
            print(f"!!! FAILED to download {ticker}: {e}")
            failed_tickers.append(ticker)
        
        # Be polite to Yahoo's servers by adding a small delay
        time.sleep(1)

    print("\n--- Data Download Complete ---")
    if failed_tickers:
        print("\nThe following tickers failed to download:")
        for ticker in failed_tickers:
            print(f"- {ticker}")

if __name__ == "__main__":
    download_nifty50_data()