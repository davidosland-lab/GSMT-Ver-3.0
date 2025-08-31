#!/usr/bin/env python3
"""
Global Markets Tracker - Python Backend with YFinance (Improved)
Provides real stock market data with fallback to recent trading days
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd
import logging
import os
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Index definitions with YFinance symbols
INDEX_SYMBOLS = {
    # Australian Indices
    '^AXJO': 'ASX 200',
    '^AXKO': 'ASX 300', 
    '^AFLI': 'ASX 50',
    '^AXMD': 'ASX 100',
    '^AXSO': 'ASX Small Cap',
    # Asian Indices
    '^N225': 'Nikkei 225',
    '^HSI': 'Hang Seng',
    '000001.SS': 'SSE Composite',
    '^NSEI': 'NIFTY 50',
    # European Indices
    '^FTSE': 'FTSE 100',
    '^GDAXI': 'DAX',
    '^FCHI': 'CAC 40',
    # US Indices
    '^GSPC': 'S&P 500',
    '^DJI': 'Dow Jones',
    '^IXIC': 'NASDAQ'
}

def find_recent_trading_day(target_date: datetime, max_days_back: int = 7) -> datetime:
    """
    Find the most recent trading day (weekday) before or on target_date
    """
    current_date = target_date
    for _ in range(max_days_back):
        # Check if it's a weekday (Monday=0, Sunday=6)
        if current_date.weekday() < 5:  # Monday to Friday
            return current_date
        current_date -= timedelta(days=1)
    return target_date  # Fallback to original date

def get_market_data(symbol: str, interval: str, date: str) -> List[Dict]:
    """
    Fetch market data using YFinance with fallback to recent trading days
    
    Args:
        symbol: Stock symbol (e.g., '^AXJO')
        interval: Time interval ('5m', '15m', '30m', '1h', '1d')
        date: Date in YYYY-MM-DD format
        
    Returns:
        List of OHLCV data points
    """
    try:
        logger.info(f"Fetching data for {symbol}, interval: {interval}, date: {date}")
        
        # Create ticker object
        ticker = yf.Ticker(symbol)
        
        # Parse target date
        target_date = datetime.strptime(date, '%Y-%m-%d')
        
        # Try the requested date first, then fallback to recent trading days
        for days_back in range(7):  # Try up to 7 days back
            try_date = target_date - timedelta(days=days_back)
            
            # Skip weekends for intraday data
            if interval in ['5m', '15m', '30m', '1h'] and try_date.weekday() >= 5:
                continue
                
            start_date = try_date
            end_date = try_date + timedelta(days=1)
            
            # For intraday data, get recent period and filter
            if interval in ['5m', '15m', '30m', '1h']:
                # Get last 5 days of intraday data
                hist = ticker.history(period='5d', interval=interval)
                
                # Filter to target date if data exists
                if not hist.empty:
                    # Try to filter to specific date
                    date_filtered = hist[hist.index.date == try_date.date()]
                    if not date_filtered.empty:
                        hist = date_filtered
                        logger.info(f"Found intraday data for {symbol} on {try_date.date()}")
                        break
                    elif days_back == 0:
                        # If no data for exact date, use most recent data
                        hist = hist.tail(50)  # Get last 50 data points
                        logger.info(f"Using recent intraday data for {symbol}")
                        break
            else:
                # For daily data, try specific date range
                hist = ticker.history(start=start_date, end=end_date, interval=interval)
                if not hist.empty:
                    logger.info(f"Found daily data for {symbol} on {try_date.date()}")
                    break
        
        # If still no data, try getting any recent data
        if 'hist' not in locals() or hist.empty:
            logger.warning(f"No data found for specific dates, trying recent data for {symbol}")
            if interval in ['5m', '15m', '30m', '1h']:
                hist = ticker.history(period='2d', interval=interval)
            else:
                hist = ticker.history(period='5d', interval=interval)
        
        if hist.empty:
            logger.warning(f"No data found for {symbol}")
            return []
        
        # Convert to list of dictionaries
        data = []
        for timestamp, row in hist.iterrows():
            # Handle timezone-aware timestamps
            if hasattr(timestamp, 'tz_localize'):
                timestamp = timestamp.tz_localize(None) if timestamp.tz is None else timestamp.tz_convert(None)
            
            data.append({
                'time': timestamp.isoformat(),
                'open': float(row['Open']) if pd.notna(row['Open']) else None,
                'high': float(row['High']) if pd.notna(row['High']) else None,
                'low': float(row['Low']) if pd.notna(row['Low']) else None,
                'close': float(row['Close']) if pd.notna(row['Close']) else None,
                'volume': int(row['Volume']) if pd.notna(row['Volume']) else None,
                'value': float(row['Close']) if pd.notna(row['Close']) else None
            })
        
        logger.info(f"Retrieved {len(data)} data points for {symbol}")
        return data
        
    except Exception as e:
        logger.error(f"Error fetching data for {symbol}: {str(e)}")
        return []

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'message': 'Global Markets Tracker Backend is running'
    })

@app.route('/api/symbols', methods=['GET'])
def get_symbols():
    """Get list of available symbols"""
    return jsonify({
        'symbols': INDEX_SYMBOLS,
        'count': len(INDEX_SYMBOLS)
    })

@app.route('/api/stock/<symbol>', methods=['GET'])
def get_stock_data(symbol: str):
    """
    Get stock data for a specific symbol
    
    Query parameters:
        - interval: '5m', '15m', '30m', '1h', '1d' (default: '5m')
        - date: YYYY-MM-DD format (default: today)
    """
    try:
        # Get query parameters
        interval = request.args.get('interval', '5m')
        date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        # Validate interval
        valid_intervals = ['5m', '15m', '30m', '1h', '1d']
        if interval not in valid_intervals:
            return jsonify({
                'error': f'Invalid interval. Must be one of: {valid_intervals}'
            }), 400
        
        # Validate date format
        try:
            datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            return jsonify({
                'error': 'Invalid date format. Use YYYY-MM-DD'
            }), 400
        
        # Validate symbol
        if symbol not in INDEX_SYMBOLS:
            logger.warning(f"Unknown symbol requested: {symbol}")
        
        # Fetch data
        data = get_market_data(symbol, interval, date)
        
        return jsonify({
            'symbol': symbol,
            'name': INDEX_SYMBOLS.get(symbol, 'Unknown'),
            'interval': interval,
            'date': date,
            'data': data,
            'count': len(data)
        })
        
    except Exception as e:
        logger.error(f"Error in get_stock_data: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@app.route('/api/bulk', methods=['POST'])
def get_bulk_data():
    """
    Get data for multiple symbols at once
    
    JSON payload:
    {
        "symbols": ["^AXJO", "^GSPC"],
        "interval": "5m",
        "date": "2024-01-15"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        symbols = data.get('symbols', [])
        interval = data.get('interval', '5m')
        date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        if not symbols:
            return jsonify({'error': 'No symbols provided'}), 400
        
        # Fetch data for all symbols
        results = {}
        for symbol in symbols:
            results[symbol] = {
                'name': INDEX_SYMBOLS.get(symbol, 'Unknown'),
                'data': get_market_data(symbol, interval, date)
            }
        
        return jsonify({
            'results': results,
            'interval': interval,
            'date': date,
            'requested_symbols': len(symbols),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in get_bulk_data: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@app.route('/', methods=['GET'])
def serve_frontend():
    """Serve API information"""
    return jsonify({
        'message': 'Global Markets Tracker API Server',
        'version': '1.1.0',
        'status': 'healthy',
        'endpoints': {
            'health': '/api/health',
            'symbols': '/api/symbols',
            'single_stock': '/api/stock/<symbol>?interval=5m&date=2025-08-27',
            'bulk_data': '/api/bulk (POST)'
        },
        'note': 'Improved version with fallback to recent trading days',
        'documentation': 'See README.md for full API documentation'
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Endpoint not found',
        'available_endpoints': [
            '/api/health',
            '/api/symbols', 
            '/api/stock/<symbol>',
            '/api/bulk'
        ]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Internal server error',
        'message': 'Please check server logs for details'
    }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting Global Markets Tracker Backend on port {port}")
    logger.info(f"Debug mode: {debug}")
    logger.info(f"Available symbols: {len(INDEX_SYMBOLS)}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)