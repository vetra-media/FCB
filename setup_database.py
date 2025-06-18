#!/usr/bin/env python3
"""Setup Elite Analysis Database Schema"""

import sqlite3
import os
from datetime import datetime

def setup_database():
    """Setup elite analysis schema in main database"""
    
    print("🚀 Setting up Elite Analysis database schema...")
    
    # Connect to main bot database
    conn = sqlite3.connect('fomo_bot.db')
    cursor = conn.cursor()
    
    # Create analysis results table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analysis_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            coin_id TEXT NOT NULL,
            symbol TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            
            -- Core scores
            fomo_score REAL NOT NULL,
            signal TEXT NOT NULL,
            analysis TEXT NOT NULL,
            confidence TEXT NOT NULL,
            risk_level TEXT NOT NULL,
            
            -- Component breakdown
            order_flow_score REAL DEFAULT 0,
            timing_score REAL DEFAULT 0,
            risk_reward_score REAL DEFAULT 0,
            sentiment_score REAL DEFAULT 0,
            liquidity_score REAL DEFAULT 0,
            
            -- Market data snapshot
            price REAL NOT NULL,
            volume_24h REAL NOT NULL,
            market_cap REAL DEFAULT 0,
            change_1h REAL DEFAULT 0,
            change_24h REAL DEFAULT 0,
            change_7d REAL DEFAULT 0,
            volume_change REAL DEFAULT 0,
            
            -- Performance tracking
            analysis_version TEXT DEFAULT 'elite_v1',
            processing_time_ms INTEGER DEFAULT 0
        )
    ''')
    
    # Create indexes for performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_symbol_timestamp ON analysis_results(symbol, timestamp)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_fomo_score ON analysis_results(fomo_score DESC)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON analysis_results(timestamp DESC)')
    
    # User query tracking
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            fomo_score REAL,
            signal TEXT,
            query_type TEXT DEFAULT 'manual'
        )
    ''')
    
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_timestamp ON user_queries(user_id, timestamp DESC)')
    
    conn.commit()
    conn.close()
    
    print("✅ Elite Analysis database setup complete!")

if __name__ == "__main__":
    setup_database()
