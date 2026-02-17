from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def onboarding_choice_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📝 Буду добавлять сам",
                    callback_data="onboard_self",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🎯 Проверь мой словарный запас",
                    callback_data="onboard_test",
                ),
            ],
        ]
    )


def word_check_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Знаю ✅",
                    callback_data="onboard_know",
                ),
                InlineKeyboardButton(
                    text="Не знаю ❓",
                    callback_data="onboard_dont_know",
                ),
            ],
        ]
    )


def onboarding_next_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Далее ➡️",
                    callback_data="onboard_next",
                ),
            ],
        ]
    )
