import os
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler

load_dotenv()

async def start(update, context):  # Made this async
    print(f"🔍 START from {update.effective_user.id}")
    await update.message.reply_text("✅ SYNC BOT WORKING!")  # Fixed this line

def main():
    token = os.getenv("TEST_BOT_TOKEN")
    print(f"Token: {token[:20]}...")
    
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    
    print("🚀 Sync bot starting...")
    print("📱 Send /start now!")
    
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()