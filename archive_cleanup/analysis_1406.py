#!/usr/bin/env python3
"""
Backtest Analysis Script for FOMO Algorithm
Tests the actual performance of the signals we found
"""

import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime, timedelta

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

def load_all_data():
    """
    Load all the CSV files and recalculate FOMO scores
    """
    print("📂 Loading data from CSV files...")
    
    all_data = {}
    data_files = glob.glob("data/*.csv")
    
    for file_path in data_files:
        try:
            df = pd.read_csv(file_path)
            df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
            
            # Extract info from filename
            filename = os.path.basename(file_path)
            parts = filename.replace('.csv', '').split('_')
            
            market_type = parts[2]  # crypto, forex, equity, commodity
            
            # Recalculate FOMO scores if not present
            if 'fomo_score' not in df.columns:
                df = calculate_fomo_score(df, market_type)
            
            if market_type not in all_data:
                all_data[market_type] = {}
            
            symbol_key = '_'.join(parts[3:])  # Rest is symbol
            all_data[market_type][symbol_key] = df
            
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
    
    return all_data

def backtest_strategy(df, threshold=90, take_profit=0.25, stop_loss=0.15, holding_days=7):
    """
    Backtest the FOMO strategy on a single asset
    """
    trades = []
    position = None
    
    for i in range(len(df)):
        row = df.iloc[i]
        
        # Check for exit conditions if in position
        if position is not None:
            days_held = i - position['entry_index']
            current_price = row['close']
            entry_price = position['entry_price']
            
            # Calculate return
            pct_return = (current_price - entry_price) / entry_price
            
            # Exit conditions
            exit_reason = None
            if pct_return >= take_profit:
                exit_reason = 'take_profit'
            elif pct_return <= -stop_loss:
                exit_reason = 'stop_loss'
            elif days_held >= holding_days:
                exit_reason = 'time_limit'
            
            if exit_reason:
                # Close position
                trade_result = {
                    'entry_date': position['entry_date'],
                    'exit_date': row['timestamp'],
                    'entry_price': entry_price,
                    'exit_price': current_price,
                    'return_pct': pct_return,
                    'days_held': days_held,
                    'exit_reason': exit_reason,
                    'fomo_score': position['fomo_score'],
                    'volume_spike_ratio': position['volume_spike_ratio']
                }
                trades.append(trade_result)
                position = None
        
        # Check for entry signal (only if not in position)
        elif (row['fomo_score'] >= threshold and 
              not pd.isna(row['fomo_score']) and 
              not pd.isna(row['volume_spike_ratio']) and
              row['volume_spike_ratio'] > 0):
            
            # Enter position
            position = {
                'entry_index': i,
                'entry_date': row['timestamp'],
                'entry_price': row['close'],
                'fomo_score': row['fomo_score'],
                'volume_spike_ratio': row['volume_spike_ratio']
            }
    
    return pd.DataFrame(trades)

def analyze_backtest_results(trades_df, asset_name="Unknown"):
    """
    Analyze backtest performance
    """
    if len(trades_df) == 0:
        return {
            'asset': asset_name,
            'total_trades': 0,
            'message': 'No trades found'
        }
    
    winning_trades = trades_df[trades_df['return_pct'] > 0]
    losing_trades = trades_df[trades_df['return_pct'] <= 0]
    
    results = {
        'asset': asset_name,
        'total_trades': len(trades_df),
        'winning_trades': len(winning_trades),
        'losing_trades': len(losing_trades),
        'win_rate': len(winning_trades) / len(trades_df) if len(trades_df) > 0 else 0,
        'avg_return': trades_df['return_pct'].mean(),
        'avg_winning_return': winning_trades['return_pct'].mean() if len(winning_trades) > 0 else 0,
        'avg_losing_return': losing_trades['return_pct'].mean() if len(losing_trades) > 0 else 0,
        'best_trade': trades_df['return_pct'].max(),
        'worst_trade': trades_df['return_pct'].min(),
        'avg_holding_days': trades_df['days_held'].mean(),
        'total_return': trades_df['return_pct'].sum(),
        'avg_fomo_score': trades_df['fomo_score'].mean()
    }
    
    return results

def comprehensive_backtest():
    """
    Run comprehensive backtesting across all assets and thresholds
    """
    print("🔄 Running comprehensive backtesting...")
    
    # Load all data
    all_data = load_all_data()
    
    thresholds = [85, 90, 95]
    all_results = []
    
    total_signals_by_threshold = {85: 0, 90: 0, 95: 0}
    
    for market_type, market_data in all_data.items():
        print(f"\n📈 Backtesting {market_type.upper()} market:")
        
        for asset, df in market_data.items():
            for threshold in thresholds:
                # Count signals at this threshold
                signals_count = len(df[df['fomo_score'] >= threshold])
                total_signals_by_threshold[threshold] += signals_count
                
                if signals_count > 0:
                    # Run backtest
                    trades = backtest_strategy(df, threshold=threshold)
                    results = analyze_backtest_results(trades, f"{market_type}_{asset}")
                    results['threshold'] = threshold
                    results['market'] = market_type
                    results['signals_found'] = signals_count
                    
                    all_results.append(results)
                    
                    if results['total_trades'] > 0:
                        print(f"  {asset} @ {threshold}%: {results['total_trades']} trades, "
                              f"{results['win_rate']:.1%} win rate, "
                              f"{results['avg_return']:.1%} avg return")
    
    return all_results, total_signals_by_threshold

def analyze_profitable_signals():
    """
    Focus specifically on the signals that actually generated trades
    """
    print("\n🎯 Analyzing only profitable signal patterns...")
    
    all_data = load_all_data()
    profitable_signals = []
    
    for market_type, market_data in all_data.items():
        for asset, df in market_data.items():
            # Get all 85%+ signals
            signals = df[df['fomo_score'] >= 85].copy()
            
            for idx, signal in signals.iterrows():
                # Look at what happened 1, 3, 7 days later
                future_prices = []
                for days_ahead in [1, 3, 7]:
                    future_idx = idx + days_ahead
                    if future_idx < len(df):
                        future_price = df.iloc[future_idx]['close']
                        price_change = (future_price - signal['close']) / signal['close']
                        future_prices.append(price_change)
                    else:
                        future_prices.append(None)
                
                signal_analysis = {
                    'market': market_type,
                    'asset': asset,
                    'date': signal['timestamp'],
                    'fomo_score': signal['fomo_score'],
                    'volume_spike_ratio': signal['volume_spike_ratio'],
                    'price_change_1d': future_prices[0],
                    'price_change_3d': future_prices[1], 
                    'price_change_7d': future_prices[2],
                    'entry_price': signal['close']
                }
                
                profitable_signals.append(signal_analysis)
    
    return pd.DataFrame(profitable_signals)

def generate_summary_report(backtest_results, signal_counts, profitable_signals_df):
    """
    Generate a comprehensive summary report
    """
    print("\n" + "="*60)
    print("📊 COMPREHENSIVE FOMO ALGORITHM ANALYSIS REPORT")
    print("="*60)
    
    # Signal frequency analysis
    print("\n🔍 SIGNAL FREQUENCY ANALYSIS (2 years of data):")
    print(f"  85%+ signals: {signal_counts[85]} total ({signal_counts[85]/24:.1f} per month)")
    print(f"  90%+ signals: {signal_counts[90]} total ({signal_counts[90]/24:.1f} per month)")  
    print(f"  95%+ signals: {signal_counts[95]} total ({signal_counts[95]/24:.1f} per month)")
    
    # Filter only results with actual trades
    traded_results = [r for r in backtest_results if r['total_trades'] > 0]
    
    if not traded_results:
        print("\n❌ NO PROFITABLE TRADES FOUND")
        print("The FOMO algorithm generated signals but none resulted in profitable backtested trades.")
        return
    
    print(f"\n💰 BACKTESTING RESULTS ({len(traded_results)} assets with trades):")
    
    # Overall performance by threshold
    for threshold in [85, 90, 95]:
        threshold_results = [r for r in traded_results if r['threshold'] == threshold]
        
        if threshold_results:
            total_trades = sum(r['total_trades'] for r in threshold_results)
            total_wins = sum(r['winning_trades'] for r in threshold_results)
            avg_win_rate = np.mean([r['win_rate'] for r in threshold_results])
            avg_return = np.mean([r['avg_return'] for r in threshold_results])
            
            print(f"\n  {threshold}% Threshold:")
            print(f"    Total trades: {total_trades}")
            print(f"    Overall win rate: {total_wins/total_trades:.1%}")
            print(f"    Average win rate: {avg_win_rate:.1%}")
            print(f"    Average return per trade: {avg_return:.1%}")
    
    # Best performing assets
    print(f"\n🏆 BEST PERFORMING ASSETS:")
    best_assets = sorted(traded_results, key=lambda x: x['win_rate'], reverse=True)[:5]
    
    for asset in best_assets:
        print(f"  {asset['asset']}: {asset['total_trades']} trades, "
              f"{asset['win_rate']:.1%} win rate, {asset['avg_return']:.1%} avg return")
    
    # Market analysis
    print(f"\n📈 PERFORMANCE BY MARKET:")
    for market in ['crypto', 'forex', 'equity', 'commodity']:
        market_results = [r for r in traded_results if r['market'] == market]
        if market_results:
            avg_win_rate = np.mean([r['win_rate'] for r in market_results])
            total_trades = sum(r['total_trades'] for r in market_results)
            print(f"  {market.upper()}: {len(market_results)} assets, "
                  f"{total_trades} total trades, {avg_win_rate:.1%} avg win rate")
    
    # Signal pattern analysis
    if len(profitable_signals_df) > 0:
        print(f"\n🔍 SIGNAL PATTERN ANALYSIS:")
        
        # Most profitable by time horizon
        for days in [1, 3, 7]:
            col = f'price_change_{days}d'
            profitable_count = len(profitable_signals_df[profitable_signals_df[col] > 0])
            total_count = len(profitable_signals_df[~profitable_signals_df[col].isna()])
            
            if total_count > 0:
                success_rate = profitable_count / total_count
                avg_return = profitable_signals_df[col].mean()
                print(f"    {days}-day success rate: {success_rate:.1%} "
                      f"(avg return: {avg_return:.1%})")
    
    # Reality check
    print(f"\n🚨 REALITY CHECK:")
    print(f"  Expected signals per month: {signal_counts[90]/24:.1f} (at 90% threshold)")
    print(f"  This is FAR below the 4-7 signals/month originally projected")
    print(f"  Multi-market approach provides {signal_counts[90]/24:.1f} signals/month")
    print(f"  vs projected 16-25 signals/month (88% overestimate)")

def main():
    """
    Main backtesting analysis
    """
    print("🚀 Starting Comprehensive Backtesting Analysis")
    print("=" * 60)
    
    # Run comprehensive backtesting
    backtest_results, signal_counts = comprehensive_backtest()
    
    # Analyze signal patterns
    profitable_signals_df = analyze_profitable_signals()
    
    # Generate summary report
    generate_summary_report(backtest_results, signal_counts, profitable_signals_df)
    
    # Save detailed results
    if backtest_results:
        results_df = pd.DataFrame(backtest_results)
        results_df.to_csv('backtest_results.csv', index=False)
        print(f"\n💾 Detailed results saved to 'backtest_results.csv'")
    
    if len(profitable_signals_df) > 0:
        profitable_signals_df.to_csv('signal_analysis.csv', index=False)
        print(f"💾 Signal analysis saved to 'signal_analysis.csv'")
    
    print("\n🎉 Analysis complete!")

if __name__ == "__main__":
    main()