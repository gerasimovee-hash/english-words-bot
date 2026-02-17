from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

BTN_DICTIONARY = "📚 Словарь"
BTN_QUIZ = "🎯 Квиз"
BTN_STATS = "📊 Статистика"

BUTTON_TEXTS = {BTN_DICTIONARY, BTN_QUIZ, BTN_STATS}


def main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=BTN_DICTIONARY),
                KeyboardButton(text=BTN_QUIZ),
                KeyboardButton(text=BTN_STATS),
            ],
        ],
        resize_keyboard=True,
    )
