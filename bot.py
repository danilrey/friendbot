import asyncio
import logging
import datetime as dt

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

import asyncpg

from friendbot import (
    TELEGRAM_TOKEN,
    OPENROUTER_KEY,
    DATABASE_URL,
    FREE_LIMIT,
    SUB_DURATION_DAYS,
    init_db,
    set_persona,
    get_user,
    set_free_count,
    set_sub_expiry,
    has_active_sub,
    save_message,
    get_history,
    trim_history,
    GPT,
    get_persona_prompt,
    persona_keyboard,
)


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
            f"Выбери, кто будет с тобой общаться:",
            reply_markup=persona_keyboard(),
        )

    @router.callback_query(F.data.startswith("persona_"))
    async def cb_persona(callback: CallbackQuery):
        persona = callback.data.split("_", 1)[1]  # "girl" или "boy"
        await set_persona(pool, callback.from_user.id, persona)
        if persona == "girl":
            await callback.message.edit_text("✅ Теперь я твоя виртуальная подруга 👩")
        else:
            await callback.message.edit_text("✅ Теперь я твой виртуальный друг 👨")
        await callback.answer()

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

        history_rows = await get_history(pool, user_id)
        history = [dict(r) for r in history_rows]

        system_prompt = await get_persona_prompt(pool, user_id)

        if has_active_sub(rec):
            reply = await gpt.reply(
                user_text=message.text,
                system_prompt=system_prompt,
                history=history,
            )
            await save_message(pool, user_id, "user", message.text)
            await save_message(pool, user_id, "assistant", reply)
            await trim_history(pool, user_id)
            await message.answer(reply, parse_mode=None)
            return

        free_count = rec["free_count"] or 0
        if free_count < FREE_LIMIT:
            reply = await gpt.reply(
                user_text=message.text,
                system_prompt=system_prompt,
                history=history,
            )
            await set_free_count(pool, user_id, free_count + 1)
            await save_message(pool, user_id, "user", message.text)
            await save_message(pool, user_id, "assistant", reply)
            await trim_history(pool, user_id)
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
