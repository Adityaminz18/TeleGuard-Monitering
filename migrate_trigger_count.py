import asyncio
from sqlalchemy import text
from app.db.session import engine

async def migrate():
    print("Starting migration: Adding trigger_count to alerts...")
    try:
        async with engine.begin() as conn:
            await conn.execute(text("ALTER TABLE alerts ADD COLUMN IF NOT EXISTS trigger_count INTEGER DEFAULT 0;"))
        print("Migration successful: Added trigger_count column.")
    except Exception as e:
        print(f"Migration failed: {e}")

if __name__ == "__main__":
    asyncio.run(migrate())
