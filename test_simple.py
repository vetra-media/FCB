import os, asyncio
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler

load_dotenv()

async def start(update, context):
    print(f"🔍 START from {update.effective_user.id}")
    await update.message.reply_text("✅ SIMPLE BOT WORKING!")

async def main():
    token = os.getenv("TEST_BOT_TOKEN") 
    print(f"Token: {token[:20]}...")
    
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    
    print("🚀 Simple bot starting...")
    await app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    asyncio.run(main())