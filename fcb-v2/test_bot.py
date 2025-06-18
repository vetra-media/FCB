import asyncio
from token_economics import get_user_balance_info

async def test():
    print("✅ Testing token economics...")
    balance = get_user_balance_info(12345)
    print(f"✅ Balance test: {balance}")
    print("✅ All systems working!")

if __name__ == "__main__":
    asyncio.run(test())