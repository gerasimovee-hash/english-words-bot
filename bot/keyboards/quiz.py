from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def quiz_keyboard(word_id: int, options: list[str]) -> InlineKeyboardMarkup:
    buttons = []
    for i, option in enumerate(options):
        buttons.append(
            [
                InlineKeyboardButton(
                    text=option,
                    callback_data=f"quiz:{word_id}:{i}",
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=buttons)
