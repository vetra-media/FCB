#!/usr/bin/env python3
"""
FCB v2 - Clean, Simple Bot
Main entry point for bot startup and scanner launch
"""

import asyncio
import logging
import signal
import sys
from telegram.ext import Application
from config import BOT_TOKEN, validate_config
from database import init_user_db
from handlers import setup_handlers
from scanner import start_scanner

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class FCBBot:
    """FCB v2 Bot Manager"""
    
    def __init__(self):
        self.app = None
        self.scanner_task = None
        self.running = False
    
    async def start(self):
        """Start the bot and scanner"""
        try:
            # Validate configuration
            validate_config()
            logger.info("✅ Configuration validated")
            
            # Initialize database
            init_user_db()
            logger.info("✅ Database initialized")
            
            # Create bot application
            self.app = Application.builder().token(BOT_TOKEN).build()
            logger.info("✅ Bot application created")
            
            # Setup command handlers
            setup_handlers(self.app)
            logger.info("✅ Handlers setup complete")
            
            # Initialize application
            await self.app.initialize()
            await self.app.start()
            
            # Start scanner in background
            self.scanner_task = asyncio.create_task(start_scanner(self.app.bot))
            logger.info("✅ Scanner started")
            
            # Start polling
            await self.app.updater.start_polling(drop_pending_updates=True)
            self.running = True
            
            logger.info("🚀 FCB v2 is now running!")
            
        except Exception as e:
            logger.error(f"❌ Bot startup failed: {e}")
            await self.stop()
            raise
    
    async def stop(self):
        """Stop the bot and scanner gracefully"""
        logger.info("🛑 Stopping FCB v2...")
        self.running = False
        
        try:
            # Stop scanner
            if self.scanner_task and not self.scanner_task.done():
                self.scanner_task.cancel()
                try:
                    await self.scanner_task
                except asyncio.CancelledError:
                    pass
                logger.info("✅ Scanner stopped")
            
            # Stop bot
            if self.app:
                await self.app.updater.stop()
                await self.app.stop()
                await self.app.shutdown()
                logger.info("✅ Bot stopped")
                
        except Exception as e:
            logger.error(f"❌ Error during shutdown: {e}")
    
    async def run_forever(self):
        """Run the bot until stopped"""
        await self.start()
        
        try:
            # Keep running until interrupted
            while self.running:
                await asyncio.sleep(1)
                
        except asyncio.CancelledError:
            logger.info("🔄 Bot cancelled")
        finally:
            await self.stop()

async def main():
    """Main function"""
    bot = FCBBot()
    
    # Setup signal handlers for graceful shutdown
    def signal_handler():
        logger.info("📡 Received shutdown signal")
        asyncio.create_task(bot.stop())
    
    # Handle SIGINT (Ctrl+C) and SIGTERM
    if sys.platform != "win32":
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, signal_handler)
    
    try:
        await bot.run_forever()
    except KeyboardInterrupt:
        logger.info("🛑 Bot interrupted by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)