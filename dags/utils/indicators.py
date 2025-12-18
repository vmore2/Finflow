# ================================================
# INDICATORS.PY - Technical Analysis Functions
# ================================================
# These functions calculate financial indicators that traders use
# to predict price movements. We use ONLY the price data - no external APIs.

from typing import List, Dict, Any


def calculate_moving_average(prices: List[float], window: int = 20) -> float:
    """
    Calculate Simple Moving Average (SMA).
    
    WHAT IS IT?
    -----------
    The average closing price over the last 'window' days.
    Traders use this to identify trends:
    - Price ABOVE MA → Uptrend (bullish)
    - Price BELOW MA → Downtrend (bearish)
    
    FORMULA:
    --------
    SMA = (Price_1 + Price_2 + ... + Price_N) / N
    
    PARAMETERS:
    -----------
    - prices: List of closing prices, newest last
    - window: Number of days to average (default: 20)
    
    RETURNS:
    --------
    The moving average value (float)
    
    EXAMPLE:
    --------
    >>> prices = [100, 102, 104, 103, 105]
    >>> calculate_moving_average(prices, window=5)
    102.8
    """
    if len(prices) < window:
        # Not enough data - use what we have
        window = len(prices)
    
    if window == 0:
        return 0.0
    
    # Take the last 'window' prices and calculate average
    recent_prices = prices[-window:]
    return round(sum(recent_prices) / len(recent_prices), 2)


def calculate_rsi(prices: List[float], period: int = 14) -> float:
    """
    Calculate Relative Strength Index (RSI).
    
    WHAT IS IT?
    -----------
    A momentum indicator from 0-100 that shows if an asset is:
    - OVERBOUGHT (RSI > 70): Too many buyers, might drop soon
    - OVERSOLD (RSI < 30): Too many sellers, might rise soon
    - NEUTRAL (30-70): Normal trading range
    
    FORMULA (Step by Step):
    -----------------------
    1. Calculate daily price changes (gains and losses)
    2. Average gains over 'period' days
    3. Average losses over 'period' days
    4. RS = Average Gain / Average Loss
    5. RSI = 100 - (100 / (1 + RS))
    
    PARAMETERS:
    -----------
    - prices: List of closing prices, newest last
    - period: Lookback period (default: 14 days, industry standard)
    
    RETURNS:
    --------
    RSI value between 0 and 100
    
    EXAMPLE:
    --------
    >>> prices = [44, 44.5, 43.5, 44.5, 44, 43.5, 44, 44.5, 45, 45.5, 46, 45, 46.5, 46, 46.5]
    >>> calculate_rsi(prices)
    66.67  # Neutral, leaning bullish
    """
    if len(prices) < period + 1:
        return 50.0  # Not enough data, return neutral
    
    # Step 1: Calculate daily changes
    # We compare each day to the previous day
    gains = []
    losses = []
    
    for i in range(1, len(prices)):
        change = prices[i] - prices[i-1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))  # Losses stored as positive numbers
    
    # Step 2 & 3: Calculate average gains and losses
    # Use only the last 'period' days
    recent_gains = gains[-period:]
    recent_losses = losses[-period:]
    
    avg_gain = sum(recent_gains) / period
    avg_loss = sum(recent_losses) / period
    
    # Step 4 & 5: Calculate RS and RSI
    if avg_loss == 0:
        return 100.0  # No losses means maximum strength
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return round(rsi, 2)


def analyze_asset(symbol: str, prices: List[float]) -> Dict[str, Any]:
    """
    Perform complete technical analysis on an asset.
    
    WHAT THIS DOES:
    ---------------
    Combines all indicators and generates a simple trading signal.
    This is what the DAG will call to get analysis results.
    
    SIGNAL LOGIC:
    -------------
    - BUY: RSI < 30 (oversold) AND price > MA (uptrend starting)
    - SELL: RSI > 70 (overbought) AND price < MA (downtrend starting)
    - HOLD: Everything else
    
    RETURNS:
    --------
    {
        'symbol': 'AAPL',
        'current_price': 150.00,
        'ma_20': 148.50,
        'rsi_14': 45.5,
        'signal': 'HOLD',
        'analysis': 'Price above MA, neutral RSI'
    }
    """
    if not prices or len(prices) < 2:
        return {
            'symbol': symbol,
            'error': 'Insufficient price data'
        }
    
    current_price = prices[-1]
    ma_20 = calculate_moving_average(prices, window=20)
    rsi = calculate_rsi(prices, period=14)
    
    # Generate trading signal
    signal = 'HOLD'
    analysis = []
    
    # Check price vs MA
    if current_price > ma_20:
        analysis.append("Price above 20-day MA (bullish)")
    else:
        analysis.append("Price below 20-day MA (bearish)")
    
    # Check RSI
    if rsi > 70:
        analysis.append(f"RSI {rsi} indicates overbought")
        if current_price < ma_20:
            signal = 'SELL'
    elif rsi < 30:
        analysis.append(f"RSI {rsi} indicates oversold")
        if current_price > ma_20:
            signal = 'BUY'
    else:
        analysis.append(f"RSI {rsi} is neutral")
    
    return {
        'symbol': symbol,
        'current_price': round(current_price, 2),
        'ma_20': ma_20,
        'rsi_14': rsi,
        'signal': signal,
        'analysis': ' | '.join(analysis)
    }


# ================================================
# TEST THE FUNCTIONS
# ================================================
if __name__ == "__main__":
    # Sample price data (simulating 20 days of AAPL prices)
    sample_prices = [
        150.0, 152.5, 151.0, 153.0, 154.5,
        153.0, 155.0, 156.5, 155.0, 157.0,
        158.5, 157.0, 159.0, 160.5, 159.0,
        161.0, 162.5, 161.0, 163.0, 164.5
    ]
    
    print("\n📊 Testing Technical Indicators...")
    print(f"Sample prices: {sample_prices[-5:]} (last 5 days)")
    
    ma = calculate_moving_average(sample_prices, 20)
    print(f"20-day MA: ${ma}")
    
    rsi = calculate_rsi(sample_prices, 14)
    print(f"14-day RSI: {rsi}")
    
    print("\n📈 Full Analysis:")
    analysis = analyze_asset('AAPL', sample_prices)
    for key, value in analysis.items():
        print(f"  {key}: {value}")
