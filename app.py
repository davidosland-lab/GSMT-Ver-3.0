from flask import Flask, jsonify, request
from flask_cors import CORS
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import pytz
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Global stock symbols with their full names
# NOTE: Only including symbols that are confirmed to work with YFinance
STOCK_SYMBOLS = {
    # Australian Indices (YFinance Confirmed)
    '^AXJO': 'ASX 200 (Australia)',
    '^AORD': 'All Ordinaries (Australia)',  # Alternative Australian index
    # Note: ^AXKO, ^AFLI, ^AXMD, ^AXSO may not exist in YFinance
    
    # US Indices
    '^GSPC': 'S&P 500 (USA)',
    '^DJI': 'Dow Jones (USA)',
    '^IXIC': 'NASDAQ (USA)',
    
    # European Indices
    '^FTSE': 'FTSE 100 (UK)',
    '^GDAXI': 'DAX (Germany)',
    '^FCHI': 'CAC 40 (France)',
    
    # Asian Indices (YFinance Confirmed)
    '^N225': 'Nikkei 225 (Japan)',
    '^HSI': 'Hang Seng (Hong Kong)',
    '000001.SS': 'Shanghai Composite (China)',
    '^NSEI': 'Nifty 50 (India)',
    '^BSESN': 'BSE Sensex (India)',
    '^KS11': 'KOSPI (South Korea)',
    '^TWII': 'Taiwan Weighted (Taiwan)',
    '^JKSE': 'Jakarta Composite (Indonesia)'
}

def get_recent_market_data(symbol, max_hours=24):
    """
    Get the most recent market data for a symbol, covering the last 24-48 hours.
    Uses multiple fallback strategies to ensure data availability.
    """
    try:
        ticker = yf.Ticker(symbol)
        
        # Strategy 1: Try 2-day period with 1-minute intervals for maximum recent data
        try:
            logger.info(f"Attempting Strategy 1 for {symbol}: 2d period, 1m interval")
            data = ticker.history(period="2d", interval="1m", prepost=True, repair=True)
            if not data.empty and len(data) > 10:
                logger.info(f"Strategy 1 successful for {symbol}: {len(data)} data points")
                return process_market_data(data, symbol, max_hours)
        except Exception as e:
            logger.warning(f"Strategy 1 failed for {symbol}: {e}")
        
        # Strategy 2: Try 5-day period with 5-minute intervals
        try:
            logger.info(f"Attempting Strategy 2 for {symbol}: 5d period, 5m interval")
            data = ticker.history(period="5d", interval="5m", prepost=True, repair=True)
            if not data.empty and len(data) > 5:
                logger.info(f"Strategy 2 successful for {symbol}: {len(data)} data points")
                return process_market_data(data, symbol, max_hours)
        except Exception as e:
            logger.warning(f"Strategy 2 failed for {symbol}: {e}")
        
        # Strategy 3: Try 1-month period with 15-minute intervals
        try:
            logger.info(f"Attempting Strategy 3 for {symbol}: 1mo period, 15m interval")
            data = ticker.history(period="1mo", interval="15m", prepost=True, repair=True)
            if not data.empty:
                logger.info(f"Strategy 3 successful for {symbol}: {len(data)} data points")
                return process_market_data(data, symbol, max_hours)
        except Exception as e:
            logger.warning(f"Strategy 3 failed for {symbol}: {e}")
        
        # Strategy 4: Try 1-month period with 1-hour intervals (most reliable)
        try:
            logger.info(f"Attempting Strategy 4 for {symbol}: 1mo period, 1h interval")
            data = ticker.history(period="1mo", interval="1h", prepost=True, repair=True)
            if not data.empty:
                logger.info(f"Strategy 4 successful for {symbol}: {len(data)} data points")
                return process_market_data(data, symbol, max_hours * 2)  # Allow more hours for hourly data
        except Exception as e:
            logger.warning(f"Strategy 4 failed for {symbol}: {e}")
        
        # Strategy 5: Last resort - daily data for context
        try:
            logger.info(f"Attempting Strategy 5 for {symbol}: 5d period, 1d interval")
            data = ticker.history(period="5d", interval="1d", prepost=True, repair=True)
            if not data.empty:
                logger.info(f"Strategy 5 successful for {symbol}: {len(data)} data points")
                return process_market_data(data, symbol, max_hours * 24, is_daily=True)
        except Exception as e:
            logger.warning(f"Strategy 5 failed for {symbol}: {e}")
        
        logger.error(f"All strategies failed for {symbol}")
        return None
        
    except Exception as e:
        logger.error(f"Critical error fetching data for {symbol}: {e}")
        return None

def process_market_data(data, symbol, max_hours, is_daily=False):
    """
    Process raw market data and filter to recent hours.
    """
    try:
        if data.empty:
            return None
        
        # Convert index to Australian timezone for filtering
        sydney_tz = pytz.timezone('Australia/Sydney')
        
        if data.index.tz is None:
            # If no timezone info, assume UTC
            data.index = data.index.tz_localize('UTC')
        
        # Convert to Sydney time
        data.index = data.index.tz_convert(sydney_tz)
        
        # Get current time in Sydney
        now_sydney = datetime.now(sydney_tz)
        
        # For daily data, we want the last few days
        if is_daily:
            cutoff_time = now_sydney - timedelta(days=5)
        else:
            # For intraday data, filter to recent hours
            cutoff_time = now_sydney - timedelta(hours=max_hours)
        
        # Filter data to recent timeframe
        recent_data = data[data.index >= cutoff_time]
        
        if recent_data.empty:
            logger.warning(f"No recent data found for {symbol} after filtering")
            # If no recent data, take the most recent available data
            recent_data = data.tail(100)  # Last 100 data points
        
        logger.info(f"Processed {len(recent_data)} data points for {symbol}")
        
        # Prepare data for frontend
        result = []
        for timestamp, row in recent_data.iterrows():
            # Convert timestamp to Australian time string
            au_time = timestamp.strftime('%Y-%m-%d %H:%M:%S %Z')
            
            data_point = {
                'timestamp': au_time,
                'timestamp_raw': timestamp.isoformat(),
                'open': float(row['Open']) if pd.notna(row['Open']) else None,
                'high': float(row['High']) if pd.notna(row['High']) else None,
                'low': float(row['Low']) if pd.notna(row['Low']) else None,
                'close': float(row['Close']) if pd.notna(row['Close']) else None,
                'volume': int(row['Volume']) if pd.notna(row['Volume']) and row['Volume'] > 0 else 0
            }
            
            # Only add data points with valid price data
            if data_point['close'] is not None:
                result.append(data_point)
        
        return result if result else None
        
    except Exception as e:
        logger.error(f"Error processing data for {symbol}: {e}")
        return None

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'Enhanced Global Stock Market Tracker API',
        'version': '2.0 - 24H Coverage'
    })

@app.route('/api/symbols', methods=['GET'])
def get_symbols():
    """Get all available stock symbols"""
    return jsonify({
        'symbols': STOCK_SYMBOLS,
        'count': len(STOCK_SYMBOLS)
    })

@app.route('/api/stock/<symbol>', methods=['GET'])
def get_stock_data(symbol):
    """
    Get stock data for a single symbol.
    Ignores date parameters and returns the most recent 24 hours of data.
    """
    try:
        logger.info(f"Fetching enhanced data for symbol: {symbol}")
        
        # Get recent market data (ignoring any date parameters)
        data = get_recent_market_data(symbol, max_hours=24)
        
        if data is None or len(data) == 0:
            logger.warning(f"No data available for {symbol}")
            return jsonify({
                'error': f'No recent market data available for {symbol}',
                'symbol': symbol,
                'data': []
            }), 404
        
        # Get symbol name
        symbol_name = STOCK_SYMBOLS.get(symbol, symbol)
        
        response_data = {
            'symbol': symbol,
            'name': symbol_name,
            'data': data,
            'count': len(data),
            'last_updated': datetime.now().isoformat(),
            'data_source': 'YFinance Enhanced 24H',
            'timezone': 'Australia/Sydney'
        }
        
        logger.info(f"Successfully returned {len(data)} data points for {symbol}")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error in get_stock_data for {symbol}: {e}")
        return jsonify({
            'error': f'Failed to fetch data for {symbol}: {str(e)}',
            'symbol': symbol,
            'data': []
        }), 500

@app.route('/api/bulk', methods=['POST'])
def get_bulk_stock_data():
    """
    Get stock data for multiple symbols.
    Expects JSON body with 'symbols' array.
    Returns recent 24-hour data for all symbols.
    """
    try:
        request_data = request.get_json()
        if not request_data or 'symbols' not in request_data:
            return jsonify({'error': 'Missing symbols in request body'}), 400
        
        symbols = request_data['symbols']
        if not isinstance(symbols, list):
            return jsonify({'error': 'Symbols must be an array'}), 400
        
        logger.info(f"Bulk request for symbols: {symbols}")
        
        results = {}
        for symbol in symbols:
            logger.info(f"Processing bulk request for: {symbol}")
            data = get_recent_market_data(symbol, max_hours=24)
            
            if data and len(data) > 0:
                results[symbol] = {
                    'name': STOCK_SYMBOLS.get(symbol, symbol),
                    'data': data,
                    'count': len(data),
                    'status': 'success'
                }
                logger.info(f"Bulk: Successfully processed {len(data)} points for {symbol}")
            else:
                results[symbol] = {
                    'name': STOCK_SYMBOLS.get(symbol, symbol),
                    'data': [],
                    'count': 0,
                    'status': 'no_data'
                }
                logger.warning(f"Bulk: No data available for {symbol}")
        
        response = {
            'results': results,
            'total_symbols': len(symbols),
            'successful_symbols': len([r for r in results.values() if r['status'] == 'success']),
            'timestamp': datetime.now().isoformat(),
            'data_source': 'YFinance Enhanced 24H',
            'timezone': 'Australia/Sydney'
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in bulk request: {e}")
        return jsonify({'error': f'Bulk request failed: {str(e)}'}), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get API status and test a few symbols"""
    try:
        test_symbols = ['^AXJO', '^GSPC', '^DJI']
        status_results = {}
        
        for symbol in test_symbols:
            try:
                data = get_recent_market_data(symbol, max_hours=24)
                status_results[symbol] = {
                    'status': 'success' if data and len(data) > 0 else 'no_data',
                    'data_points': len(data) if data else 0
                }
            except Exception as e:
                status_results[symbol] = {
                    'status': 'error',
                    'error': str(e),
                    'data_points': 0
                }
        
        return jsonify({
            'api_status': 'operational',
            'timestamp': datetime.now().isoformat(),
            'test_results': status_results,
            'total_symbols_available': len(STOCK_SYMBOLS),
            'version': 'Enhanced 24H Coverage v2.0'
        })
        
    except Exception as e:
        return jsonify({
            'api_status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)