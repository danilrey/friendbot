from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def persona_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👩 Девушка", callback_data="persona_girl"),
                InlineKeyboardButton(text="👨 Парень", callback_data="persona_boy"),
            ]
        ]
    )

