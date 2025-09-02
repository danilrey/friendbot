import asyncio
import asyncpg

async def test_connection():
    DB_URL = "postgresql://postgres:0000@localhost/friendbot"  # Убедитесь, что здесь правильные данные
    try:
        # Подключение к базе данных
        conn = await asyncpg.connect(DB_URL)
        print("✅ Успешное подключение к базе данных!")

        # Выполнение тестового запроса
        result = await conn.fetch("SELECT 1;")
        print("Результат тестового запроса:", result)

        # Закрытие соединения
        await conn.close()
    except Exception as e:
        print("❌ Ошибка подключения к базе данных:", e)

# Запуск проверки
asyncio.run(test_connection())