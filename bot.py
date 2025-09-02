import os
import asyncio
import logging
import datetime as dt
from typing import Optional

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.types import Message

import asyncpg
from openai import OpenAI
from dotenv import load_dotenv

# -------------------- Конфигурация --------------------
load_dotenv()
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:0000@localhost:5432/friendbot")

FREE_LIMIT = int(os.getenv("FREE_LIMIT", 5))
SUB_DURATION_DAYS = int(os.getenv("SUB_DURATION_DAYS", 30))
MAX_HISTORY = int(os.getenv("MAX_HISTORY", 10))  # сколько последних сообщений хранить в контексте

SYSTEM_PROMPT = (
    "Ты милая девушка, поддерживающая разговор. Будь доброй, позитивной, тактичной, без 18+."
)

# -------------------- Работа с БД --------------------
USERS_SQL = """
CREATE TABLE IF NOT EXISTS users (
    user_id     BIGINT PRIMARY KEY,
    free_count  INT DEFAULT 0,
    sub_expiry  TIMESTAMP NULL
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

async def get_user(pool: asyncpg.pool.Pool, user_id: int) -> asyncpg.Record:
    async with pool.acquire() as conn:
        rec = await conn.fetchrow("SELECT * FROM users WHERE user_id=$1", user_id)
        if not rec:
            await conn.execute(
                "INSERT INTO users (user_id, free_count, sub_expiry) VALUES ($1, 0, NULL)", user_id
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
    se = rec["sub_expiry"]
    return bool(se and se > dt.datetime.now())

# -------------------- Сообщения --------------------
async def save_message(pool, user_id: int, role: str, content: str):
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO messages (user_id, role, content) VALUES ($1, $2, $3)",
            user_id, role, content
        )

async def get_history(pool, user_id: int, limit: int = MAX_HISTORY):
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT role, content FROM messages WHERE user_id=$1 ORDER BY id DESC LIMIT $2",
            user_id, limit
        )
        return list(reversed(rows))

# -------------------- OpenRouter (DeepSeek) --------------------
class GPT:
    def __init__(self, api_key: str):
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )

    async def reply(self, history: list, user_text: str) -> str:
        def _call() -> str:
            messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history + [
                {"role": "user", "content": user_text}
            ]
            resp = self.client.chat.completions.create(
                model="deepseek/deepseek-r1:free",
                messages=messages,
            )
            return resp.choices[0].message.content
        return await asyncio.to_thread(_call)

# -------------------- Основной runtime --------------------
async def main() -> None:
    bot = Bot(token=TELEGRAM_TOKEN)
    dp = Dispatcher()
    router = Router()
    dp.include_router(router)

    pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)
    logging.info("Подключение к БД установлено")
    await init_db(pool)

    gpt = GPT(api_key=OPENROUTER_KEY)

    @router.message(Command("start"))
    async def cmd_start(message: Message):
        await get_user(pool, message.from_user.id)
        await message.answer(
            "Привет 👋 Я виртуальная подруга!\n"
            f"У тебя {FREE_LIMIT} бесплатных сообщений.\n"
            "Чтобы продолжить потом — оформи подписку /subscribe"
        )

    @router.message(Command("subscribe"))
    async def cmd_subscribe(message: Message):
        user_id = message.from_user.id
        expiry = dt.datetime.now() + dt.timedelta(days=SUB_DURATION_DAYS)
        await set_sub_expiry(pool, user_id, expiry)
        await message.answer(f"✅ Подписка активирована до {expiry.strftime('%d.%m.%Y')}!")

    @router.message(F.text)
    async def on_text(message: Message):
        user_id = message.from_user.id
        rec = await get_user(pool, user_id)

        history = await get_history(pool, user_id)
        history = [dict(r) for r in history]

        if has_active_sub(rec):
            reply = await gpt.reply(history, message.text)
            await save_message(pool, user_id, "user", message.text)
            await save_message(pool, user_id, "assistant", reply)
            await message.answer(reply)
            return

        free_count = rec["free_count"] or 0
        if free_count < FREE_LIMIT:
            reply = await gpt.reply(history, message.text)
            await set_free_count(pool, user_id, free_count + 1)
            await save_message(pool, user_id, "user", message.text)
            await save_message(pool, user_id, "assistant", reply)
            await message.answer(f"(Бесплатно) {reply}")
        else:
            await message.answer("🔒 Бесплатные сообщения закончились!\nОформи подписку 👉 /subscribe")

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        await pool.close()
        logging.info("Пул БД закрыт, бот остановлен")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
