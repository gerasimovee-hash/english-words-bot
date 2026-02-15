from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def save_word_keyboard(word: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📝 Сохранить в словарь",
                    callback_data=f"save:{word[:50]}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="✅ Уже знаю",
                    callback_data="skip",
                ),
            ],
        ]
    )
