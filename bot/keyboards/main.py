from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

BTN_DICTIONARY = "📚 Словарь"
BTN_QUIZ = "🎯 Квиз"
BTN_STATS = "📊 Статистика"
BTN_DONATE = "❤️ Поддержать"

BUTTON_TEXTS = {BTN_DICTIONARY, BTN_QUIZ, BTN_STATS, BTN_DONATE}


def main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=BTN_DICTIONARY),
                KeyboardButton(text=BTN_QUIZ),
                KeyboardButton(text=BTN_STATS),
            ],
            [
                KeyboardButton(text=BTN_DONATE),
            ],
        ],
        resize_keyboard=True,
    )
