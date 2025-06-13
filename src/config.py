import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Telegram Bot
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    
    # API Keys
    COINGECKO_API_KEY = os.getenv('COINGECKO_API_KEY')
    
    # FCB Token
    FCB_TOKEN_CONTRACT = os.getenv('FCB_TOKEN_CONTRACT')
    
    # Monetization
    AFFILIATE_TRACKING_ID = os.getenv('AFFILIATE_TRACKING_ID')
    
    # Bot Settings
    MAX_SCAN_REQUESTS_PER_DAY = int(os.getenv('MAX_SCAN_REQUESTS_PER_DAY', 100))
    FOMO_THRESHOLD_SCORE = int(os.getenv('FOMO_THRESHOLD_SCORE', 75))
    
    # Development
    DEBUG_MODE = os.getenv('DEBUG_MODE', 'False').lower() == 'true'
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    @classmethod
    def validate(cls):
        """Validate required environment variables"""
        required_vars = [
            'TELEGRAM_BOT_TOKEN',
            'COINGECKO_API_KEY'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")