import datetime as dt
from typing import Optional, List, Dict, Any

import asyncpg

from .config import MAX_HISTORY

USERS_SQL = """
CREATE TABLE IF NOT EXISTS users (
    user_id     BIGINT PRIMARY KEY,
    free_count  INT DEFAULT 0,
    sub_expiry  TIMESTAMP NULL,
    persona     TEXT NULL
);
"""

MESSAGES_SQL = """
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    user_id BIGINT,
    role TEXT,
    content TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
"""

async def init_db(pool: asyncpg.pool.Pool) -> None:
    async with pool.acquire() as conn:
        await conn.execute(USERS_SQL)
        await conn.execute(MESSAGES_SQL)
        # Ensure persona column exists for older deployments
        await conn.execute("ALTER TABLE IF EXISTS users ADD COLUMN IF NOT EXISTS persona TEXT NULL")

async def set_persona(pool: asyncpg.pool.Pool, user_id: int, persona: str) -> None:
    async with pool.acquire() as conn:
        await conn.execute("UPDATE users SET persona=$1 WHERE user_id=$2", persona, user_id)

async def get_user(pool: asyncpg.pool.Pool, user_id: int) -> asyncpg.Record:
    async with pool.acquire() as conn:
        rec = await conn.fetchrow("SELECT * FROM users WHERE user_id=$1", user_id)
        if not rec:
            await conn.execute(
                "INSERT INTO users (user_id, free_count, sub_expiry, persona) VALUES ($1, 0, NULL, NULL)",
                user_id,
            )
            rec = await conn.fetchrow("SELECT * FROM users WHERE user_id=$1", user_id)
        return rec

async def set_free_count(pool: asyncpg.pool.Pool, user_id: int, count: int) -> None:
    async with pool.acquire() as conn:
        await conn.execute("UPDATE users SET free_count=$1 WHERE user_id=$2", count, user_id)

async def set_sub_expiry(pool: asyncpg.pool.Pool, user_id: int, expiry: Optional[dt.datetime]) -> None:
    async with pool.acquire() as conn:
        await conn.execute("UPDATE users SET sub_expiry=$1 WHERE user_id=$2", expiry, user_id)

def has_active_sub(rec: asyncpg.Record) -> bool:
    se = rec.get("sub_expiry") if isinstance(rec, dict) else rec["sub_expiry"]
    return bool(se and se > dt.datetime.now())

async def save_message(pool: asyncpg.pool.Pool, user_id: int, role: str, content: str) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO messages (user_id, role, content) VALUES ($1, $2, $3)",
            user_id,
            role,
            content,
        )

async def get_history(pool: asyncpg.pool.Pool, user_id: int, limit: int = MAX_HISTORY) -> List[Dict[str, Any]]:
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT role, content FROM messages WHERE user_id=$1 ORDER BY id DESC LIMIT $2",
            user_id,
            limit,
        )
        return list(reversed(rows))

async def trim_history(pool: asyncpg.pool.Pool, user_id: int, limit: int = MAX_HISTORY * 2) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            """
            DELETE FROM messages
            WHERE user_id = $1
              AND id IN (
                  SELECT id FROM messages
                  WHERE user_id = $1
                  ORDER BY id DESC
                  OFFSET $2
              )
            """,
            user_id,
            limit,
        )
