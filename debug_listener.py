import asyncio
import logging
from sqlmodel import select
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from app.db.session import engine, AsyncSession
from app.models import TelegramSession
from app.core.config import settings

# Logging
logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.INFO)
logger = logging.getLogger("debug_listener")

async def main():
    print("--- Starting Debug Listener ---")
    
    # 1. Fetch Session
    async with AsyncSession(engine) as session:
        result = await session.execute(select(TelegramSession).where(TelegramSession.is_active == True))
        db_session = result.scalars().first()
        
    if not db_session:
        print("❌ No active session found in DB!")
        return

    print(f"✅ Found session for User: {db_session.user_id}")
    print(f"   Phone: {db_session.phone_number}")

    # 2. Connect Client
    try:
        client = TelegramClient(
            StringSession(db_session.session_string),
            settings.TELEGRAM_API_ID,
            settings.TELEGRAM_API_HASH
        )
        await client.connect()
        
        if not await client.is_user_authorized():
            print("❌ Session is invalid/unauthorized.")
            return
            
        me = await client.get_me()
        print(f"✅ Connected as: {me.first_name} (@{me.username}) ID: {me.id}")
        
        print("\n🎧 Listening for new messages... (Press Ctrl+C to stop)")
        print("Please send a message to any chat/group now.")

        @client.on(events.NewMessage)
        async def handler(event):
            sender = await event.get_sender()
            name = getattr(sender, 'first_name', 'Unknown')
            username = getattr(sender, 'username', 'Unknown')
            chat_id = event.chat_id
            text = event.message.message
            
            print("\n------------------------------------------------")
            print(f"📨 NEW MESSAGE RECEIVED")
            print(f"   Chat ID: {chat_id}")
            print(f"   From: {name} (@{username})")
            print(f"   Text: {text}")
            print("------------------------------------------------")

        await client.run_until_disconnected()

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped.")
