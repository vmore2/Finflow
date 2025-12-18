# ================================================
# FETCHERS.PY - Data Ingestion Functions
# ================================================
# This file contains all functions that FETCH data from external sources.
# We keep them separate from the DAG for cleaner code (best practice).

import yfinance as yf
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any


def fetch_stock_prices(symbols: List[str], period: str = "1mo") -> Dict[str, Any]:
    """
    Fetch stock prices using yfinance (Yahoo Finance API wrapper).
    
    WHAT THIS DOES:
    - Downloads historical price data for given stock symbols
    - Returns a dictionary with symbol -> price data
    
    PARAMETERS:
    - symbols: List of stock tickers, e.g., ['AAPL', 'GOOGL']
    - period: How far back to look. Options: '1d', '5d', '1mo', '3mo', '1y'
    
    RETURNS:
    {
        'AAPL': {'prices': [...], 'current_price': 150.25, 'change_pct': 2.5},
        'GOOGL': {...}
    }
    """
    results = {}
    
    for symbol in symbols:
        try:
            # Download stock data - yfinance handles all the API calls
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)
            
            if hist.empty:
                print(f"Warning: No data for {symbol}")
                continue
            
            # Extract the data we care about
            prices = hist['Close'].tolist()  # Closing prices as a list
            current_price = prices[-1] if prices else 0
            
            # Calculate percentage change from first to last price
            if len(prices) >= 2:
                change_pct = ((prices[-1] - prices[0]) / prices[0]) * 100
            else:
                change_pct = 0
            
            results[symbol] = {
                'prices': prices,
                'current_price': round(current_price, 2),
                'change_pct': round(change_pct, 2),
                'fetched_at': datetime.now().isoformat()
            }
            
            print(f"✅ Fetched {symbol}: ${current_price:.2f} ({change_pct:+.2f}%)")
            
        except Exception as e:
            print(f"❌ Error fetching {symbol}: {e}")
            results[symbol] = {'error': str(e)}
    
    return results


def fetch_crypto_prices(symbols: List[str] = None) -> Dict[str, Any]:
    """
    Fetch cryptocurrency prices from CoinGecko (FREE, no API key needed).
    
    WHAT THIS DOES:
    - Calls CoinGecko's free API
    - Gets current price, 24h change, and market cap
    
    PARAMETERS:
    - symbols: List of crypto IDs, e.g., ['bitcoin', 'ethereum']
              (Note: CoinGecko uses full names, not symbols like 'BTC')
    
    RETURNS:
    {
        'bitcoin': {'price': 45000, 'change_24h': 2.5, 'market_cap': 850000000000},
        'ethereum': {...}
    }
    """
    if symbols is None:
        symbols = ['bitcoin', 'ethereum']
    
    # CoinGecko API endpoint - completely free, no key required
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        'ids': ','.join(symbols),
        'vs_currencies': 'usd',
        'include_24hr_change': 'true',
        'include_market_cap': 'true'
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()  # Raises error if request failed
        data = response.json()
        
        results = {}
        for symbol in symbols:
            if symbol in data:
                coin_data = data[symbol]
                results[symbol] = {
                    'price': coin_data.get('usd', 0),
                    'change_24h': round(coin_data.get('usd_24h_change', 0), 2),
                    'market_cap': coin_data.get('usd_market_cap', 0),
                    'fetched_at': datetime.now().isoformat()
                }
                print(f"✅ Fetched {symbol}: ${results[symbol]['price']:,.2f} ({results[symbol]['change_24h']:+.2f}%)")
        
        return results
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching crypto prices: {e}")
        return {'error': str(e)}


# ================================================
# TEST THE FUNCTIONS (when running this file directly)
# ================================================
if __name__ == "__main__":
    print("\n📈 Testing Stock Fetcher...")
    stocks = fetch_stock_prices(['AAPL', 'GOOGL', 'MSFT'])
    print(f"Stock data: {stocks}")
    
    print("\n🪙 Testing Crypto Fetcher...")
    crypto = fetch_crypto_prices(['bitcoin', 'ethereum'])
    print(f"Crypto data: {crypto}")
