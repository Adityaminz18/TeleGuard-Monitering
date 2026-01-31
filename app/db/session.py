from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel, select
from app.core.config import settings
from app.models import ReferralCode

# Engine
# Note: asyncpg requires the URL to start with postgresql+asyncpg://
# asyncpg also doesn't support 'sslmode' in the query string; we must use connect_args.
import urllib.parse

db_url = settings.DATABASE_URL
connect_args = {}

if db_url and db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

# Handle sslmode for asyncpg
if "sslmode" in db_url:
    parsed = urllib.parse.urlparse(db_url)
    query_params = urllib.parse.parse_qs(parsed.query)
    
    if "sslmode" in query_params:
        ssl_mode = query_params.pop("sslmode", [None])[0]
        if ssl_mode == "require":
             connect_args["ssl"] = "require"



        # Reconstruct URL without sslmode
        new_query = urllib.parse.urlencode(query_params, doseq=True)
        db_url = urllib.parse.urlunparse(parsed._replace(query=new_query))


# Disable statement cache to prevent protocol errors with poolers or schema changes
connect_args["statement_cache_size"] = 0

engine = create_async_engine(
    db_url, 
    echo=False, 
    future=True, 
    connect_args=connect_args,
    pool_pre_ping=True
)

async_session_factory = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def init_db():
    async with engine.begin() as conn:
        # await conn.run_sync(SQLModel.metadata.drop_all) # WARNING: DELETES DATA
        await conn.run_sync(SQLModel.metadata.create_all)
    
    # Seed invite code from env
    if settings.INVITE:
        async with async_session_factory() as session:
            statement = select(ReferralCode).where(ReferralCode.code == settings.INVITE)
            result = await session.execute(statement)
            existing = result.scalar_one_or_none()
            
            if not existing:
                new_code = ReferralCode(
                    code=settings.INVITE,
                    max_uses=999999, # Unlimited for env code
                    is_active=True
                )
                session.add(new_code)
                await session.commit()
                print(f"Seeded invite code from env: {settings.INVITE}")

async def get_db():
    async with async_session_factory() as session:
        yield session
