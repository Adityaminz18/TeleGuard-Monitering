import asyncio
from app.db.session import engine
from app.models import ReferralCode
from sqlmodel import Session, select

async def create_code():
    async with engine.begin() as conn:
        pass # ensure schema exists (handled by app startup usually but good to be safe if creating separate script, though engine is shared)

    # Use a sync session for simplicity if possible, but our engine is async.
    # Actually, let's just use the async session pattern from the app.
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.ext.asyncio import AsyncSession
    
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Check if code exists
        statement = select(ReferralCode).where(ReferralCode.code == "WELCOME10")
        result = await session.execute(statement)
        existing = result.scalar_one_or_none()
        
        if existing:
            print(f"Code already exists: {existing.code}")
        else:
            new_code = ReferralCode(
                code="WELCOME10",
                max_uses=100,
                is_active=True
            )
            session.add(new_code)
            await session.commit()
            print(f"Created new code: WELCOME10")

if __name__ == "__main__":
    asyncio.run(create_code())
