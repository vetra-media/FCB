#!/usr/bin/env python3
"""
Multi-Market Data Collection Script for FOMO Algorithm Testing
Collects data from Crypto, Forex, Stocks, and Commodities
"""

import ccxt
import pandas as pd
import numpy as np
import yfinance as yf
import requests
import time
from datetime import datetime, timedelta
import os

# Create data directory if it doesn't exist
if not os.path.exists('data'):
    os.makedirs('data')

def collect_crypto_data():
    """
    Collect cryptocurrency data from multiple exchanges
    """
    print("🔄 Collecting cryptocurrency data...")
    
    # Initialize exchanges (no API keys needed for public data)
    exchanges = {}
    
    try:
        exchanges['binance'] = ccxt.binance()
        print("✅ Binance connected")
    except:
        print("❌ Binance failed to connect")
    
    try:
        exchanges['coinbase'] = ccxt.coinbasepro()
        print("✅ Coinbase connected")
    except:
        print("❌ Coinbase failed to connect")
    
    try:
        exchanges['kraken'] = ccxt.kraken()
        print("✅ Kraken connected")
    except:
        print("❌ Kraken failed to connect")
    
    # Top crypto pairs to analyze
    crypto_pairs = [
        'BTC/USDT', 'ETH/USDT', 'ADA/USDT', 'SOL/USDT', 'DOT/USDT',
        'LINK/USDT', 'MATIC/USDT', 'AVAX/USDT', 'ATOM/USDT'
    ]
    
    all_crypto_data = {}
    
    for exchange_name, exchange in exchanges.items():
        print(f"📊 Collecting from {exchange_name}...")
        exchange_data = {}
        
        for pair in crypto_pairs:
            try:
                # Get 2 years of daily data
                ohlcv = exchange.fetch_ohlcv(pair, '1d', limit=730)
                
                if len(ohlcv) > 100:  # Ensure sufficient data
                    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    df['market'] = 'crypto'
                    df['exchange'] = exchange_name
                    df['symbol'] = pair
                    
                    exchange_data[pair] = df
                    print(f"  ✅ {pair}: {len(df)} days")
                else:
                    print(f"  ❌ {pair}: insufficient data")
                    
                time.sleep(0.1)  # Be nice to APIs
                
            except Exception as e:
                print(f"  ❌ {pair}: {str(e)}")
        
        if exchange_data:
            all_crypto_data[exchange_name] = exchange_data
    
    return all_crypto_data

def collect_forex_data():
    """
    Collect forex data using Yahoo Finance
    """
    print("🔄 Collecting forex data...")
    
    # Major currency pairs
    forex_pairs = [
        'EURUSD=X', 'GBPUSD=X', 'USDJPY=X', 'USDCHF=X', 'AUDUSD=X',
        'USDCAD=X', 'NZDUSD=X', 'EURGBP=X', 'EURJPY=X', 'GBPJPY=X'
    ]
    
    forex_data = {}
    
    for pair in forex_pairs:
        try:
            ticker = yf.Ticker(pair)
            hist = ticker.history(period="2y", interval="1d")
            
            if len(hist) > 100:
                df = hist.reset_index()
                df['timestamp'] = df['Date']
                df['open'] = df['Open']
                df['high'] = df['High'] 
                df['low'] = df['Low']
                df['close'] = df['Close']
                df['volume'] = df['Volume']
                df['market'] = 'forex'
                df['exchange'] = 'yahoo'
                df['symbol'] = pair
                
                forex_data[pair] = df[['timestamp', 'open', 'high', 'low', 'close', 'volume', 'market', 'exchange', 'symbol']]
                print(f"  ✅ {pair}: {len(df)} days")
            else:
                print(f"  ❌ {pair}: insufficient data")
                
        except Exception as e:
            print(f"  ❌ {pair}: {str(e)}")
    
    return forex_data

def collect_stock_data():
    """
    Collect stock data from multiple markets
    """
    print("🔄 Collecting stock market data...")
    
    # US Stocks (High volume, diverse sectors)
    us_stocks = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX',
        'JPM', 'JNJ', 'PG', 'UNH', 'HD', 'MA', 'DIS', 'PYPL'
    ]
    
    # UK Stocks (FTSE 100)
    uk_stocks = [
        'LLOY.L', 'BP.L', 'SHEL.L', 'AZN.L', 'RIO.L', 'HSBA.L', 
        'VOD.L', 'ULVR.L', 'GSK.L', 'BT-A.L'
    ]
    
    all_stocks = us_stocks + uk_stocks
    stock_data = {}
    
    for symbol in all_stocks:
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="2y", interval="1d")
            
            if len(hist) > 100:
                df = hist.reset_index()
                df['timestamp'] = df['Date']
                df['open'] = df['Open']
                df['high'] = df['High']
                df['low'] = df['Low'] 
                df['close'] = df['Close']
                df['volume'] = df['Volume']
                df['market'] = 'equity'
                
                # Determine exchange
                if '.L' in symbol:
                    df['exchange'] = 'LSE'
                else:
                    df['exchange'] = 'NYSE/NASDAQ'
                
                df['symbol'] = symbol
                
                stock_data[symbol] = df[['timestamp', 'open', 'high', 'low', 'close', 'volume', 'market', 'exchange', 'symbol']]
                print(f"  ✅ {symbol}: {len(df)} days")
            else:
                print(f"  ❌ {symbol}: insufficient data")
                
        except Exception as e:
            print(f"  ❌ {symbol}: {str(e)}")
        
        time.sleep(0.1)  # Rate limiting
    
    return stock_data

def collect_commodity_data():
    """
    Collect commodity futures data
    """
    print("🔄 Collecting commodity data...")
    
    # Commodity futures symbols
    commodities = {
        'CL=F': 'Crude Oil',
        'GC=F': 'Gold',
        'SI=F': 'Silver', 
        'NG=F': 'Natural Gas',
        'ZC=F': 'Corn',
        'ZS=F': 'Soybeans',
        'ZW=F': 'Wheat',
        'KC=F': 'Coffee'
    }
    
    commodity_data = {}
    
    for symbol, name in commodities.items():
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="2y", interval="1d")
            
            if len(hist) > 100:
                df = hist.reset_index()
                df['timestamp'] = df['Date']
                df['open'] = df['Open']
                df['high'] = df['High']
                df['low'] = df['Low']
                df['close'] = df['Close'] 
                df['volume'] = df['Volume']
                df['market'] = 'commodity'
                df['exchange'] = 'CME/CBOT'
                df['symbol'] = symbol
                df['name'] = name
                
                commodity_data[symbol] = df[['timestamp', 'open', 'high', 'low', 'close', 'volume', 'market', 'exchange', 'symbol']]
                print(f"  ✅ {name} ({symbol}): {len(df)} days")
            else:
                print(f"  ❌ {name} ({symbol}): insufficient data")
                
        except Exception as e:
            print(f"  ❌ {symbol}: {str(e)}")
    
    return commodity_data

def calculate_fomo_score(df, market_type, lookback_days=30):
    """
    Calculate FOMO score adapted for different market types
    """
    df = df.copy()
    
    # Calculate rolling averages
    df['volume_avg_30d'] = df['volume'].rolling(window=lookback_days).mean()
    df['price_volatility_24h'] = df['close'].pct_change().abs()
    
    # Volume spike calculation
    df['volume_spike_ratio'] = df['volume'] / df['volume_avg_30d']
    
    def fomo_score_row(row):
        if pd.isna(row['volume_spike_ratio']) or row['volume_spike_ratio'] == 0:
            return 0
            
        score = 0
        
        # Market-specific volume spike thresholds
        if market_type == 'crypto':
            if row['volume_spike_ratio'] >= 10:
                score += 40
            elif row['volume_spike_ratio'] >= 5:
                score += 30
            elif row['volume_spike_ratio'] >= 3:
                score += 20
        elif market_type == 'forex':
            if row['volume_spike_ratio'] >= 3:
                score += 40
            elif row['volume_spike_ratio'] >= 2:
                score += 30
            elif row['volume_spike_ratio'] >= 1.5:
                score += 20
        elif market_type == 'equity':
            if row['volume_spike_ratio'] >= 5:
                score += 40
            elif row['volume_spike_ratio'] >= 3:
                score += 30
            elif row['volume_spike_ratio'] >= 2:
                score += 20
        elif market_type == 'commodity':
            if row['volume_spike_ratio'] >= 4:
                score += 40
            elif row['volume_spike_ratio'] >= 2.5:
                score += 30
            elif row['volume_spike_ratio'] >= 2:
                score += 20
        
        # Volatility component (market-adjusted)
        volatility_thresholds = {
            'crypto': [0.10, 0.05],    # 10%, 5%
            'forex': [0.03, 0.015],    # 3%, 1.5%
            'equity': [0.05, 0.025],   # 5%, 2.5%
            'commodity': [0.08, 0.04]  # 8%, 4%
        }
        
        high_vol, low_vol = volatility_thresholds.get(market_type, [0.05, 0.025])
        
        if row['price_volatility_24h'] < low_vol:
            score += 20
        elif row['price_volatility_24h'] < high_vol:
            score += 10
        
        # Volume size percentile
        try:
            volume_percentile = df['volume'].rank(pct=True).iloc[row.name]
            if volume_percentile > 0.9:
                score += 20
            elif volume_percentile > 0.7:
                score += 10
        except:
            pass
        
        # Price momentum
        try:
            price_change = row['close'] / df['close'].shift(1).iloc[row.name] - 1
            if market_type == 'crypto' and 0.02 < price_change < 0.15:
                score += 20
            elif market_type == 'forex' and 0.005 < price_change < 0.03:
                score += 20
            elif market_type == 'equity' and 0.01 < price_change < 0.08:
                score += 20
            elif market_type == 'commodity' and 0.015 < price_change < 0.10:
                score += 20
        except:
            pass
        
        return min(score, 100)  # Cap at 100
    
    df['fomo_score'] = df.apply(fomo_score_row, axis=1)
    return df

def analyze_market_data(market_data, market_type):
    """
    Analyze a single market's data and calculate FOMO scores
    """
    print(f"📈 Analyzing {market_type} market...")
    analyzed_data = {}
    
    for symbol, df in market_data.items():
        df_analyzed = calculate_fomo_score(df, market_type)
        analyzed_data[symbol] = df_analyzed
        
        # Count signals by threshold
        signals_85 = len(df_analyzed[df_analyzed['fomo_score'] >= 85])
        signals_90 = len(df_analyzed[df_analyzed['fomo_score'] >= 90])
        signals_95 = len(df_analyzed[df_analyzed['fomo_score'] >= 95])
        
        print(f"  {symbol}: 85%+: {signals_85}, 90%+: {signals_90}, 95%+: {signals_95}")
    
    return analyzed_data

def save_data_to_csv(all_data, filename_prefix='market_data'):
    """
    Save all collected data to CSV files
    """
    print("💾 Saving data to CSV files...")
    
    for market_type, market_data in all_data.items():
        if market_type == 'crypto':
            # Handle nested crypto data structure
            for exchange, exchange_data in market_data.items():
                for symbol, df in exchange_data.items():
                    clean_symbol = symbol.replace('/', '_')
                    filename = f"data/{filename_prefix}_{market_type}_{exchange}_{clean_symbol}.csv"
                    df.to_csv(filename, index=False)
        else:
            # Handle flat data structure
            for symbol, df in market_data.items():
                clean_symbol = symbol.replace('/', '_').replace('=', '_').replace('.', '_')
                filename = f"data/{filename_prefix}_{market_type}_{clean_symbol}.csv"
                df.to_csv(filename, index=False)
    
    print("✅ Data saved to CSV files")

def main():
    """
    Main function to collect and analyze all market data
    """
    print("🚀 Starting Multi-Market Data Collection")
    print("=" * 50)
    
    # Collect data from all markets
    all_data = {}
    
    # Crypto data
    try:
        crypto_data = collect_crypto_data()
        if crypto_data:
            all_data['crypto'] = crypto_data
    except Exception as e:
        print(f"❌ Crypto collection failed: {e}")
    
    # Forex data
    try:
        forex_data = collect_forex_data()
        if forex_data:
            all_data['forex'] = forex_data
    except Exception as e:
        print(f"❌ Forex collection failed: {e}")
    
    # Stock data
    try:
        stock_data = collect_stock_data()
        if stock_data:
            all_data['equity'] = stock_data
    except Exception as e:
        print(f"❌ Stock collection failed: {e}")
    
    # Commodity data
    try:
        commodity_data = collect_commodity_data()
        if commodity_data:
            all_data['commodity'] = commodity_data
    except Exception as e:
        print(f"❌ Commodity collection failed: {e}")
    
    print("\n" + "=" * 50)
    print("📊 Data Collection Summary:")
    
    total_assets = 0
    for market_type, market_data in all_data.items():
        if market_type == 'crypto':
            count = sum(len(exchange_data) for exchange_data in market_data.values())
        else:
            count = len(market_data)
        
        total_assets += count
        print(f"  {market_type.upper()}: {count} assets")
    
    print(f"  TOTAL: {total_assets} assets collected")
    
    # Analyze data and calculate FOMO scores
    print("\n" + "=" * 50)
    analyzed_data = {}
    
    for market_type, market_data in all_data.items():
        if market_type == 'crypto':
            # Flatten crypto data for analysis
            flat_crypto_data = {}
            for exchange, exchange_data in market_data.items():
                for symbol, df in exchange_data.items():
                    flat_crypto_data[f"{exchange}_{symbol}"] = df
            analyzed_data[market_type] = analyze_market_data(flat_crypto_data, market_type)
        else:
            analyzed_data[market_type] = analyze_market_data(market_data, market_type)
    
    # Save data
    save_data_to_csv(all_data)
    
    print("\n" + "=" * 50)
    print("🎉 Data collection and analysis complete!")
    print("📁 Check the 'data' folder for CSV files")
    print("🔍 Next step: Run backtesting analysis")

if __name__ == "__main__":
    main()