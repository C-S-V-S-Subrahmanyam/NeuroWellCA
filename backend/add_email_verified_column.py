"""
Migration script to add email_verified column to users table
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os
from dotenv import load_dotenv

load_dotenv()

# Use asyncpg driver for async operations
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/neurowell")
# Convert to asyncpg URL if needed
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)


async def add_email_verified_column():
    """Add email_verified column to users table"""
    engine = create_async_engine(DATABASE_URL, echo=True)
    
    async with engine.begin() as conn:
        # Check if column exists
        result = await conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='users' AND column_name='email_verified';
        """))
        
        if result.fetchone() is None:
            # Add column if it doesn't exist
            await conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN email_verified BOOLEAN DEFAULT FALSE;
            """))
            print("✅ Added email_verified column to users table")
            
            # Update existing users to have verified email (backward compatibility)
            await conn.execute(text("""
                UPDATE users 
                SET email_verified = TRUE 
                WHERE email_verified IS NULL;
            """))
            print("✅ Set existing users as email verified")
        else:
            print("ℹ️ email_verified column already exists")
    
    await engine.dispose()
    print("✅ Migration completed successfully")


if __name__ == "__main__":
    asyncio.run(add_email_verified_column())
