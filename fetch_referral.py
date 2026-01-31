import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import select
from app.db.session import engine
from app.models import ReferralCode

async def fetch_code():
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        # Get first active code with remaining uses
        stmt = select(ReferralCode).where(ReferralCode.is_active == True).where(ReferralCode.used_count < ReferralCode.max_uses)
        result = await session.execute(stmt)
        code = result.scalars().first()
        if code:
            print(f"CODE:{code.code}")
        else:
            print("NO_CODE_FOUND")

if __name__ == "__main__":
    asyncio.run(fetch_code())
