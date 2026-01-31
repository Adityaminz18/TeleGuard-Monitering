import asyncio
from sqlmodel import select
from app.db.session import engine, AsyncSession
from app.models import User, TelegramSession, Alert

async def check_db():
    async with AsyncSession(engine) as session:
        print("--- Checking Users ---")
        users = (await session.execute(select(User))).scalars().all()
        for u in users:
            print(f"User: {u.email}, ID: {u.id}")

        print("\n--- Checking Telegram Sessions ---")
        sessions = (await session.execute(select(TelegramSession))).scalars().all()
        for s in sessions:
            print(f"Session User: {s.user_id}, Active: {s.is_active}, Phone: {s.phone_number}, TelegramID: {s.telegram_id}")

        print("\n--- Checking Alerts ---")
        alerts = (await session.execute(select(Alert))).scalars().all()
        for a in alerts:
            print(f"Alert ID: {a.id}")
            print(f"  - User: {a.user_id}")
            print(f"  - Keywords: {a.keywords}")
            print(f"  - Source ID: {a.source_id} (Type: {type(a.source_id)})")
            print(f"  - Notify: Email={a.notify_email}, Bot={a.notify_bot}")

if __name__ == "__main__":
    asyncio.run(check_db())
