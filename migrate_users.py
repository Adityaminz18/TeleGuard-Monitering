
import asyncio
import os
from sqlalchemy import text
from app.db.session import engine

async def migrate():
    async with engine.begin() as conn:
        print("Migrating: Adding full_name to users table...")
        try:
            await conn.execute(text("ALTER TABLE users ADD COLUMN full_name VARCHAR"))
            print("✅ Column added successfully.")
        except Exception as e:
            if "duplicate column" in str(e):
                print("⚠️ Column already exists. Skipping.")
            else:
                print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(migrate())
