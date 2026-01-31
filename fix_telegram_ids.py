import asyncio
from sqlmodel import select
from telethon import TelegramClient
from telethon.sessions import StringSession
from app.db.session import engine, AsyncSession
from app.models import TelegramSession
from app.core.config import settings

async def fix_ids():
    print("Fetching sessions...")
    async with AsyncSession(engine) as session:
        result = await session.execute(select(TelegramSession))
        sessions = result.scalars().all()
        
        for s in sessions:
            if not s.telegram_id and s.session_string:
                print(f"Fixing session for user {s.user_id}...")
                try:
                    client = TelegramClient(StringSession(s.session_string), settings.TELEGRAM_API_ID, settings.TELEGRAM_API_HASH)
                    await client.connect()
                    
                    if not await client.is_user_authorized():
                        print(f"Session invalid for user {s.user_id}")
                        continue
                        
                    me = await client.get_me()
                    s.telegram_id = str(me.id)
                    session.add(s)
                    print(f"Updated telegram_id to {me.id}")
                    
                    await client.disconnect()
                except Exception as e:
                    print(f"Failed to fix session: {e}")
        
        await session.commit()
        print("Database update complete.")

if __name__ == "__main__":
    asyncio.run(fix_ids())
