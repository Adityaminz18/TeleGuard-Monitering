import asyncio
from sqlalchemy import text
from app.db.session import engine

async def migrate():
    print("Starting migration: Adding telegram_id to telegram_sessions...")
    try:
        async with engine.begin() as conn:
            await conn.execute(text("ALTER TABLE telegram_sessions ADD COLUMN IF NOT EXISTS telegram_id VARCHAR;"))
        print("Migration successful: Added telegram_id column.")
    except Exception as e:
        print(f"Migration failed: {e}")

if __name__ == "__main__":
    asyncio.run(migrate())
