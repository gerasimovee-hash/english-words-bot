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


def correction_keyboard(corrected: str, original: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"Да, {corrected}",
                    callback_data=f"correct_yes:{corrected[:40]}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"Нет, я имел в виду {original}",
                    callback_data=f"correct_no:{original[:40]}",
                ),
            ],
        ]
    )
