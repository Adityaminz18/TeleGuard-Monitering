import asyncio
from sqlalchemy import text
from app.db.session import engine

async def check_schema():
    print("--- Checking 'alerts' table schema ---")
    async with engine.connect() as conn:
        # Query postgres information_schema
        result = await conn.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'alerts' AND column_name = 'source_id';
        """))
        row = result.fetchone()
        if row:
            print(f"Column: {row[0]}, Type: {row[1]}")
        else:
            print("Column 'source_id' not found!")

if __name__ == "__main__":
    asyncio.run(check_schema())
