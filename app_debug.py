#!/usr/bin/env python3
"""
Global Markets Tracker - Debug Version with Extensive Logging
"""

from flask import Flask, jsonify, request
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
CORS(app)

INDEX_SYMBOLS = {
    '^AXJO': 'ASX 200',
    '^GSPC': 'S&P 500',
    '^DJI': 'Dow Jones',
    '^IXIC': 'NASDAQ',
    '^N225': 'Nikkei 225',
    '^FTSE': 'FTSE 100'
}

def get_market_data_debug(symbol: str, interval: str = '1d') -> List[Dict]:
    """
    Debug version with extensive logging and multiple fallback strategies
    """
    try:
        logger.info(f"=== DEBUGGING DATA FETCH FOR {symbol} ===")
        
        ticker = yf.Ticker(symbol)
        
        # Strategy 1: Try recent period (most reliable)
        logger.info("Strategy 1: Trying period='5d'")
        try:
            hist = ticker.history(period='5d', interval=interval)
            logger.info(f"Period 5d result: {len(hist)} rows")
            if not hist.empty:
                logger.info(f"Date range: {hist.index[0]} to {hist.index[-1]}")
                logger.info(f"Sample data: {hist.tail(1).to_dict()}")
                return convert_to_json(hist)
        except Exception as e:
            logger.error(f"Period 5d failed: {e}")
        
        # Strategy 2: Try 1 month
        logger.info("Strategy 2: Trying period='1mo'")
        try:
            hist = ticker.history(period='1mo', interval='1d')
            logger.info(f"Period 1mo result: {len(hist)} rows")
            if not hist.empty:
                return convert_to_json(hist.tail(20))  # Last 20 days
        except Exception as e:
            logger.error(f"Period 1mo failed: {e}")
        
        # Strategy 3: Try specific date range
        logger.info("Strategy 3: Trying specific date range")
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            hist = ticker.history(start=start_date, end=end_date, interval='1d')
            logger.info(f"Date range result: {len(hist)} rows")
            if not hist.empty:
                return convert_to_json(hist)
        except Exception as e:
            logger.error(f"Date range failed: {e}")
        
        # Strategy 4: Try basic info
        logger.info("Strategy 4: Checking ticker info")
        try:
            info = ticker.info
            logger.info(f"Ticker info available: {bool(info)}")
            if info:
                logger.info(f"Symbol: {info.get('symbol', 'N/A')}")
                logger.info(f"Name: {info.get('longName', 'N/A')}")
        except Exception as e:
            logger.error(f"Ticker info failed: {e}")
        
        logger.warning(f"All strategies failed for {symbol}")
        return []
        
    except Exception as e:
        logger.error(f"Complete failure for {symbol}: {str(e)}")
        return []

def convert_to_json(hist_data) -> List[Dict]:
    """Convert pandas DataFrame to JSON format"""
    if hist_data.empty:
        return []
    
    data = []
    for timestamp, row in hist_data.iterrows():
        if hasattr(timestamp, 'tz_localize'):
            timestamp = timestamp.tz_localize(None) if timestamp.tz is None else timestamp.tz_convert(None)
        
        data.append({
            'time': timestamp.isoformat(),
            'open': float(row['Open']) if pd.notna(row['Open']) else None,
            'high': float(row['High']) if pd.notna(row['High']) else None,
            'low': float(row['Low']) if pd.notna(row['Low']) else None,
            'close': float(row['Close']) if pd.notna(row['Close']) else None,
            'volume': int(row['Volume']) if pd.notna(row['Volume']) else 0,
            'value': float(row['Close']) if pd.notna(row['Close']) else None
        })
    
    logger.info(f"Converted {len(data)} data points")
    return data

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'message': 'Debug version with extensive logging'
    })

@app.route('/api/debug/<symbol>', methods=['GET'])
def debug_symbol(symbol: str):
    """Debug endpoint with detailed logging"""
    logger.info(f"DEBUG REQUEST for symbol: {symbol}")
    
    data = get_market_data_debug(symbol)
    
    return jsonify({
        'symbol': symbol,
        'name': INDEX_SYMBOLS.get(symbol, 'Unknown'),
        'data': data,
        'count': len(data),
        'message': 'Check server logs for detailed debug info',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/stock/<symbol>', methods=['GET'])
def get_stock_data(symbol: str):
    """Standard endpoint with fallback to debug mode"""
    interval = request.args.get('interval', '1d')  # Default to daily
    
    # For now, use debug mode for all requests
    data = get_market_data_debug(symbol, interval)
    
    return jsonify({
        'symbol': symbol,
        'name': INDEX_SYMBOLS.get(symbol, 'Unknown'),
        'interval': interval,
        'date': datetime.now().strftime('%Y-%m-%d'),
        'data': data,
        'count': len(data)
    })

@app.route('/api/symbols', methods=['GET'])
def get_symbols():
    return jsonify({
        'symbols': INDEX_SYMBOLS,
        'count': len(INDEX_SYMBOLS)
    })

@app.route('/', methods=['GET'])
def root():
    return jsonify({
        'message': 'Global Markets Tracker API - Debug Version',
        'version': '1.2.0-debug',
        'endpoints': {
            'health': '/api/health',
            'symbols': '/api/symbols',
            'stock': '/api/stock/<symbol>',
            'debug': '/api/debug/<symbol> (with detailed logging)'
        },
        'note': 'Check Railway logs for debug information'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)