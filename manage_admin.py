import asyncio
import argparse
import sys
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import select

from app.db.session import engine
from app.models import User

async def manage_admin(email: str, promote: bool):
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        statement = select(User).where(User.email == email)
        result = await session.execute(statement)
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"❌ User with email {email} not found.")
            return

        if promote:
            if user.role == "admin":
                print(f"ℹ️  User {email} is already an admin.")
            else:
                user.role = "admin"
                session.add(user)
                await session.commit()
                await session.refresh(user)
                print(f"✅ User {email} has been promoted to ADMIN.")
        else:
            if user.role != "admin":
                print(f"ℹ️  User {email} is not an admin.")
            else:
                user.role = "user"
                session.add(user)
                await session.commit()
                await session.refresh(user)
                print(f"✅ User {email} has been demoted to USER.")

def main():
    parser = argparse.ArgumentParser(description="Manage Admin Users")
    parser.add_argument("email", help="Email of the user to manage")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--promote", action="store_true", help="Promote user to admin")
    group.add_argument("--demote", action="store_true", help="Demote user to regular user")
    
    args = parser.parse_args()
    
    try:
        asyncio.run(manage_admin(args.email, args.promote))
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
