🚀 FOMO Crypto Bot (FCB)

FOMO Crypto Bot (FCB) is a Telegram-based crypto signals bot that helps users detect early-stage breakout coins before they trend. It uses real-time market analysis to generate FOMO and risk scores for individual coins, allowing users to act on pre-hype signals. Access to premium scans is gated by the FCB utility token.

🧠 Features

📈 Real-Time Coin Scanning – Detects price action, volume spikes, and unusual trends
🧮 FOMO & Risk Scores – Measures upside potential and downside risk
🪙 FCB Token System – Tokens are used to unlock scan requests
🔗 Affiliate Monetisation – "Buy Coin" buttons link to partner exchanges
💬 Telegram Interface – Easy-to-use commands and inline buttons for interaction
📁 Project Structure

FCB/ ├── .env # Secret keys and config (excluded from Git) ├── .gitignore # Git ignore rules for venv, cache, DB, etc. ├── main.py # Bot entry point ├── config.py # API keys, environment vars, and constants ├── database.py # Token ledger, rate limits, and user balances ├── api_client.py # Market data fetchers (CoinGecko) ├── analysis.py # FOMO signal calculations (volume, price, momentum) ├── scanner.py # Core scanning logic ├── handlers.py # Telegram bot command and message handlers ├── formatters.py # Telegram message formatting ├── cache.py # Simple result caching ├── diagnostic_main.py # Script for local testing ├── targeted_diagnostic.py # Focused scan runner for dev use ├── fomo_variety_history.csv # Optional CSV for pattern research ├── fcb_users.db # Local user/token storage (excluded from Git) ├── subscriptions.pkl # Subscription data cache (excluded from Git) ├── TEST_DEBUG/ # Test/debug scripts (optional)