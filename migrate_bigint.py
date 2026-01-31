import asyncio
from sqlalchemy import text
from app.db.session import engine

async def migrate():
    print("Starting migration: Altering source_id to BIGINT...")
    try:
        async with engine.begin() as conn:
            # Postgres command to change type
            await conn.execute(text("ALTER TABLE alerts ALTER COLUMN source_id TYPE BIGINT;"))
        print("Migration successful: source_id is now BIGINT.")
    except Exception as e:
        print(f"Migration failed or already applied: {e}")

if __name__ == "__main__":
    asyncio.run(migrate())
