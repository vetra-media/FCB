print("Testing imports one by one...")

print("1. Testing config...")
from config import validate_config
print("✅ Config OK")

print("2. Testing database...")
from database import init_user_db
print("✅ Database OK")

print("3. Testing formatters...")
from formatters import format_fomo_message
print("✅ Formatters OK")

print("4. Testing scanner...")
from scanner import add_user_to_notifications
print("✅ Scanner OK")

print("5. Testing handlers...")
from handlers import setup_handlers
print("✅ Handlers OK")

print("All imports successful!")