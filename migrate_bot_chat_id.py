
import asyncio
from sqlalchemy import text
from app.db.session import engine

async def migrate():
    async with engine.begin() as conn:
        print("Migrating: Adding bot_chat_id to users...")
        try:
            await conn.execute(text("ALTER TABLE users ADD COLUMN bot_chat_id BIGINT;"))
            print("Migration successful: Added bot_chat_id column.")
        except Exception as e:
            if "already exists" in str(e):
                print("Column bot_chat_id already exists.")
            else:
                print(f"Migration failed: {e}")

if __name__ == "__main__":
    asyncio.run(migrate())
