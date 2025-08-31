from flask import Flask, jsonify, request
from flask_cors import CORS
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import pytz
import logging
import os
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Enhanced symbol mapping with alternatives and proxies
SYMBOL_ALTERNATIVES = {
    # Australian Markets - multiple formats and ETF proxies
    '^AXJO': {
        'name': 'ASX 200 (Australia)',
        'alternatives': ['^AXJO', 'XJO.AX', 'IOZ.AX'],
        'proxy_symbols': ['^AORD', 'VAS.AX'],
        'market_correlation': 1.0
    },
    '^AXKO': {
        'name': 'ASX 300 (Australia)', 
        'alternatives': ['^AXKO', 'XKO.AX', 'VAS.AX'],
        'proxy_symbols': ['^AXJO', '^AORD', 'IOZ.AX'],
        'market_correlation': 0.95
    },
    '^AFLI': {
        'name': 'ASX 50 (Australia)',
        'alternatives': ['^AFLI', 'XFL.AX'],
        'proxy_symbols': ['^AXJO', 'IOZ.AX'],
        'market_correlation': 0.85
    },
    '^AXMD': {
        'name': 'ASX 100 (Australia)',
        'alternatives': ['^AXMD', 'XTO.AX'],
        'proxy_symbols': ['^AXJO', '^AORD'],
        'market_correlation': 0.90
    },
    '^AXSO': {
        'name': 'ASX Small Cap (Australia)',
        'alternatives': ['^AXSO', 'VSO.AX'],
        'proxy_symbols': ['^AXJO', '^AORD'],
        'market_correlation': 0.70
    },
    
    # Asian Markets - with alternatives
    '^N225': {
        'name': 'Nikkei 225 (Japan)',
        'alternatives': ['^N225', 'NKY', '1321.T'],
        'proxy_symbols': ['EWJ'],
        'market_correlation': 1.0
    },
    '^HSI': {
        'name': 'Hang Seng (Hong Kong)',
        'alternatives': ['^HSI', 'HSI', '2800.HK'],
        'proxy_symbols': ['EWH', 'FXI'],
        'market_correlation': 1.0
    },
    '000001.SS': {
        'name': 'Shanghai Composite (China)',
        'alternatives': ['000001.SS', 'SHCOMP', '510300.SS'],
        'proxy_symbols': ['FXI', 'MCHI'],
        'market_correlation': 1.0
    },
    '^NSEI': {
        'name': 'Nifty 50 (India)',
        'alternatives': ['^NSEI', 'NSEI', '^NSEBANK'],
        'proxy_symbols': ['INDA', 'EPI'],
        'market_correlation': 1.0
    },
    
    # US Markets (these should work reliably)
    '^GSPC': {'name': 'S&P 500 (USA)', 'alternatives': ['^GSPC'], 'proxy_symbols': ['SPY'], 'market_correlation': 1.0},
    '^DJI': {'name': 'Dow Jones (USA)', 'alternatives': ['^DJI'], 'proxy_symbols': ['DIA'], 'market_correlation': 1.0},
    '^IXIC': {'name': 'NASDAQ (USA)', 'alternatives': ['^IXIC'], 'proxy_symbols': ['QQQ'], 'market_correlation': 1.0},
    
    # European Markets
    '^FTSE': {'name': 'FTSE 100 (UK)', 'alternatives': ['^FTSE'], 'proxy_symbols': ['EWU'], 'market_correlation': 1.0},
    '^GDAXI': {'name': 'DAX (Germany)', 'alternatives': ['^GDAXI'], 'proxy_symbols': ['EWG'], 'market_correlation': 1.0},
    '^FCHI': {'name': 'CAC 40 (France)', 'alternatives': ['^FCHI'], 'proxy_symbols': ['EWQ'], 'market_correlation': 1.0},
    
    # Additional Asian Markets
    '^BSESN': {'name': 'BSE Sensex (India)', 'alternatives': ['^BSESN'], 'proxy_symbols': ['INDA'], 'market_correlation': 1.0},
    '^KS11': {'name': 'KOSPI (South Korea)', 'alternatives': ['^KS11'], 'proxy_symbols': ['EWY'], 'market_correlation': 1.0},
    '^TWII': {'name': 'Taiwan Weighted (Taiwan)', 'alternatives': ['^TWII'], 'proxy_symbols': ['EWT'], 'market_correlation': 1.0},
    '^JKSE': {'name': 'Jakarta Composite (Indonesia)', 'alternatives': ['^JKSE'], 'proxy_symbols': ['EIDO'], 'market_correlation': 1.0}
}

def test_symbol_validity(symbol, timeout=5):
    """Quick test if a symbol returns data"""
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="1d", interval="1h", timeout=timeout)
        return not data.empty and len(data) > 0
    except Exception as e:
        logger.debug(f"Symbol {symbol} test failed: {e}")
        return False

def get_multi_strategy_data(symbol, max_hours=24):
    """
    Multi-strategy data fetching with alternatives, proxies, and correlated demo data
    """
    symbol_info = SYMBOL_ALTERNATIVES.get(symbol, {
        'name': symbol,
        'alternatives': [symbol],
        'proxy_symbols': [],
        'market_correlation': 1.0
    })
    
    status = {
        'symbol': symbol,
        'name': symbol_info['name'],
        'attempts': [],
        'data_source': None,
        'warnings': [],
        'proxy_used': False
    }
    
    # Strategy 1: Try primary symbol with multiple periods/intervals
    logger.info(f"Strategy 1: Trying primary symbol {symbol}")
    data = try_primary_symbol(symbol, max_hours)
    if data is not None:
        status['data_source'] = 'primary_symbol'
        status['attempts'].append('primary_success')
        return data, status
    else:
        status['attempts'].append('primary_failed')
    
    # Strategy 2: Try alternative symbol formats
    logger.info(f"Strategy 2: Trying alternative formats for {symbol}")
    for alt_symbol in symbol_info['alternatives'][1:]:  # Skip first (same as primary)
        data = try_primary_symbol(alt_symbol, max_hours)
        if data is not None:
            status['data_source'] = f'alternative_symbol: {alt_symbol}'
            status['attempts'].append(f'alternative_success: {alt_symbol}')
            status['warnings'].append(f'Using alternative symbol {alt_symbol} for {symbol}')
            return data, status
        else:
            status['attempts'].append(f'alternative_failed: {alt_symbol}')
    
    # Strategy 3: Try proxy symbols (ETFs or related indices)
    logger.info(f"Strategy 3: Trying proxy symbols for {symbol}")
    for proxy_symbol in symbol_info['proxy_symbols']:
        data = try_primary_symbol(proxy_symbol, max_hours)
        if data is not None:
            # Apply correlation adjustment
            correlation = symbol_info['market_correlation']
            adjusted_data = apply_correlation_adjustment(data, correlation, symbol)
            status['data_source'] = f'proxy_symbol: {proxy_symbol}'
            status['attempts'].append(f'proxy_success: {proxy_symbol}')
            status['warnings'].append(f'Using proxy {proxy_symbol} for {symbol} (correlation: {correlation})')
            status['proxy_used'] = True
            return adjusted_data, status
        else:
            status['attempts'].append(f'proxy_failed: {proxy_symbol}')
    
    # Strategy 4: Generate correlated demo data based on working market
    logger.info(f"Strategy 4: Generating correlated demo data for {symbol}")
    demo_data = generate_correlated_demo_data(symbol, symbol_info)
    status['data_source'] = 'correlated_demo'
    status['attempts'].append('demo_fallback')
    status['warnings'].append(f'No real data available for {symbol}, using correlated demo data')
    
    return demo_data, status

def try_primary_symbol(symbol, max_hours=24):
    """Try to get data from a symbol using multiple strategies"""
    try:
        ticker = yf.Ticker(symbol)
        
        # Strategy A: 2-day period with 1-minute intervals
        try:
            data = ticker.history(period="2d", interval="1m", prepost=True, repair=True, timeout=10)
            if not data.empty and len(data) > 10:
                return process_market_data(data, symbol, max_hours)
        except Exception as e:
            logger.debug(f"Strategy A failed for {symbol}: {e}")
        
        # Strategy B: 5-day period with 5-minute intervals
        try:
            data = ticker.history(period="5d", interval="5m", prepost=True, repair=True, timeout=10)
            if not data.empty and len(data) > 5:
                return process_market_data(data, symbol, max_hours)
        except Exception as e:
            logger.debug(f"Strategy B failed for {symbol}: {e}")
        
        # Strategy C: 1-month period with 1-hour intervals
        try:
            data = ticker.history(period="1mo", interval="1h", prepost=True, repair=True, timeout=10)
            if not data.empty:
                return process_market_data(data, symbol, max_hours * 2)
        except Exception as e:
            logger.debug(f"Strategy C failed for {symbol}: {e}")
        
        # Strategy D: 5-day period with daily data
        try:
            data = ticker.history(period="5d", interval="1d", prepost=True, repair=True, timeout=10)
            if not data.empty:
                return process_market_data(data, symbol, max_hours * 24, is_daily=True)
        except Exception as e:
            logger.debug(f"Strategy D failed for {symbol}: {e}")
            
    except Exception as e:
        logger.error(f"All strategies failed for {symbol}: {e}")
    
    return None

def apply_correlation_adjustment(data, correlation_factor, target_symbol):
    """Apply correlation adjustment when using proxy data"""
    if correlation_factor == 1.0:
        return data
    
    adjusted_data = []
    for point in data:
        # Apply correlation to price movements
        adjusted_point = point.copy()
        
        # Adjust price volatility based on correlation
        if 'open' in adjusted_point and adjusted_point['open']:
            price_change = (adjusted_point['close'] - adjusted_point['open']) / adjusted_point['open']
            adjusted_change = price_change * correlation_factor
            
            # Recalculate prices with adjusted correlation
            adjusted_point['close'] = adjusted_point['open'] * (1 + adjusted_change)
            adjusted_point['high'] = max(adjusted_point['open'], adjusted_point['close']) * (1 + abs(adjusted_change) * 0.5)
            adjusted_point['low'] = min(adjusted_point['open'], adjusted_point['close']) * (1 - abs(adjusted_change) * 0.5)
        
        adjusted_data.append(adjusted_point)
    
    return adjusted_data

def generate_correlated_demo_data(symbol, symbol_info):
    """Generate demo data that correlates with market patterns"""
    # Try to get a working market as correlation base
    base_data = None
    
    # Try to use S&P 500 as correlation base
    try:
        base_data = try_primary_symbol('^GSPC', 24)
    except:
        pass
    
    if base_data is None:
        # Try other major indices
        for base_symbol in ['^DJI', '^IXIC', '^FTSE']:
            try:
                base_data = try_primary_symbol(base_symbol, 24)
                if base_data:
                    break
            except:
                continue
    
    if base_data and len(base_data) > 0:
        # Create correlated demo data based on real market movements
        correlation = symbol_info.get('market_correlation', 0.7)
        demo_data = create_correlated_data(base_data, correlation, symbol)
        return demo_data
    
    # Fallback to standard demo data generation
    return generate_standard_demo_data(symbol)

def create_correlated_data(base_data, correlation, target_symbol):
    """Create correlated data based on real market movements"""
    correlated_data = []
    base_price = 1000  # Starting price for synthetic data
    
    for i, base_point in enumerate(base_data):
        if i == 0:
            # First point
            correlated_point = {
                'timestamp': base_point['timestamp'],
                'timestamp_raw': base_point['timestamp_raw'],
                'open': base_price,
                'high': base_price * 1.002,
                'low': base_price * 0.998,
                'close': base_price,
                'volume': 1000000
            }
        else:
            # Calculate movement from base data
            prev_base = base_data[i-1]
            base_change = (base_point['close'] - prev_base['close']) / prev_base['close']
            
            # Apply correlation
            correlated_change = base_change * correlation
            
            # Add some randomness
            random_factor = np.random.normal(0, 0.001)  # Small random component
            total_change = correlated_change + random_factor
            
            prev_close = correlated_data[i-1]['close']
            new_close = prev_close * (1 + total_change)
            
            # Calculate OHLC based on close
            volatility = abs(total_change) + 0.005
            high = new_close * (1 + volatility * 0.5)
            low = new_close * (1 - volatility * 0.5)
            open_price = correlated_data[i-1]['close']  # Open is previous close
            
            correlated_point = {
                'timestamp': base_point['timestamp'],
                'timestamp_raw': base_point['timestamp_raw'],
                'open': round(open_price, 2),
                'high': round(high, 2),
                'low': round(low, 2),
                'close': round(new_close, 2),
                'volume': int(np.random.normal(1000000, 200000))
            }
        
        correlated_data.append(correlated_point)
    
    return correlated_data

def generate_standard_demo_data(symbol):
    """Generate standard demo data as ultimate fallback"""
    demo_data = []
    base_price = 1000
    current_time = datetime.now(pytz.timezone('Australia/Sydney'))
    
    # Generate 24 hours of hourly data
    for i in range(24):
        timestamp = current_time - timedelta(hours=23-i)
        
        # Simple random walk
        change = np.random.normal(0, 0.01)
        if i == 0:
            price = base_price
        else:
            price = demo_data[i-1]['close'] * (1 + change)
        
        volatility = 0.005
        high = price * (1 + volatility)
        low = price * (1 - volatility)
        
        demo_data.append({
            'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S %Z'),
            'timestamp_raw': timestamp.isoformat(),
            'open': round(price * 0.999, 2),
            'high': round(high, 2),
            'low': round(low, 2),
            'close': round(price, 2),
            'volume': int(np.random.normal(500000, 100000))
        })
    
    return demo_data

def process_market_data(data, symbol, max_hours, is_daily=False):
    """Process raw market data and filter to recent hours"""
    try:
        if data.empty:
            return None
        
        # Convert index to Australian timezone for filtering
        sydney_tz = pytz.timezone('Australia/Sydney')
        
        if data.index.tz is None:
            data.index = data.index.tz_localize('UTC')
        
        data.index = data.index.tz_convert(sydney_tz)
        
        # Get current time in Sydney
        now_sydney = datetime.now(sydney_tz)
        
        # Filter data to recent timeframe
        if is_daily:
            cutoff_time = now_sydney - timedelta(days=5)
        else:
            cutoff_time = now_sydney - timedelta(hours=max_hours)
        
        recent_data = data[data.index >= cutoff_time]
        
        if recent_data.empty:
            recent_data = data.tail(100)
        
        # Prepare data for frontend
        result = []
        for timestamp, row in recent_data.iterrows():
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
        'service': 'Enhanced Multi-Strategy Global Stock Market Tracker API',
        'version': '3.0 - Multi-Strategy with Proxies',
        'supported_symbols': len(SYMBOL_ALTERNATIVES)
    })

@app.route('/api/symbols', methods=['GET'])
def get_symbols():
    """Get all available stock symbols"""
    symbols = {symbol: info['name'] for symbol, info in SYMBOL_ALTERNATIVES.items()}
    return jsonify({
        'symbols': symbols,
        'count': len(symbols),
        'features': ['alternative_formats', 'proxy_symbols', 'correlated_demo']
    })

@app.route('/api/stock/<symbol>', methods=['GET'])
def get_stock_data(symbol):
    """Get stock data for a single symbol using multi-strategy approach"""
    try:
        logger.info(f"Multi-strategy fetch for symbol: {symbol}")
        
        # Get data using multi-strategy approach
        data, status = get_multi_strategy_data(symbol, max_hours=24)
        
        if data is None or len(data) == 0:
            return jsonify({
                'error': f'No data available for {symbol} with any strategy',
                'symbol': symbol,
                'status': status,
                'data': []
            }), 404
        
        response_data = {
            'symbol': symbol,
            'name': status['name'],
            'data': data,
            'count': len(data),
            'last_updated': datetime.now().isoformat(),
            'data_source': status['data_source'],
            'status': status,
            'timezone': 'Australia/Sydney'
        }
        
        logger.info(f"Successfully returned {len(data)} data points for {symbol} via {status['data_source']}")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error in multi-strategy fetch for {symbol}: {e}")
        return jsonify({
            'error': f'Failed to fetch data for {symbol}: {str(e)}',
            'symbol': symbol,
            'data': []
        }), 500

@app.route('/api/validate/<symbol>', methods=['GET'])
def validate_symbol(symbol):
    """Validate if a symbol can return data"""
    is_valid = test_symbol_validity(symbol)
    alternatives = SYMBOL_ALTERNATIVES.get(symbol, {}).get('alternatives', [])
    
    return jsonify({
        'symbol': symbol,
        'valid': is_valid,
        'alternatives': alternatives,
        'has_proxy': len(SYMBOL_ALTERNATIVES.get(symbol, {}).get('proxy_symbols', [])) > 0
    })

@app.route('/api/bulk', methods=['POST'])
def get_bulk_stock_data():
    """Get stock data for multiple symbols using multi-strategy approach"""
    try:
        request_data = request.get_json()
        if not request_data or 'symbols' not in request_data:
            return jsonify({'error': 'Missing symbols in request body'}), 400
        
        symbols = request_data['symbols']
        logger.info(f"Multi-strategy bulk request for symbols: {symbols}")
        
        results = {}
        for symbol in symbols:
            data, status = get_multi_strategy_data(symbol, max_hours=24)
            
            results[symbol] = {
                'name': status['name'],
                'data': data if data else [],
                'count': len(data) if data else 0,
                'status': status,
                'success': data is not None and len(data) > 0
            }
        
        successful_count = sum(1 for r in results.values() if r['success'])
        
        response = {
            'results': results,
            'total_symbols': len(symbols),
            'successful_symbols': successful_count,
            'timestamp': datetime.now().isoformat(),
            'service': 'Multi-Strategy Enhanced API',
            'timezone': 'Australia/Sydney'
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in multi-strategy bulk request: {e}")
        return jsonify({'error': f'Bulk request failed: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
