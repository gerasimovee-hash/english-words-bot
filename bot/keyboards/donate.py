from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def donate_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⭐ 100", callback_data="donate:100"),
                InlineKeyboardButton(text="⭐ 200", callback_data="donate:200"),
                InlineKeyboardButton(text="⭐ 500", callback_data="donate:500"),
            ],
            [
                InlineKeyboardButton(text="Ой, передумал", callback_data="donate:cancel"),
            ],
        ]
    )
