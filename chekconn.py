import asyncio
import asyncpg
from friendbot.config import DATABASE_URL

async def test_connection():
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        print("✅ Успешное подключение к базе данных!")
        result = await conn.fetch("SELECT 1;")
        print("Результат тестового запроса:", result)
        await conn.close()
    except Exception as e:
        print("❌ Ошибка подключения к базе данных:", e)

if __name__ == "__main__":
    asyncio.run(test_connection())
