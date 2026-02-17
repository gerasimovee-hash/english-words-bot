"""Pre-built word bank for onboarding quiz. No LLM calls needed."""

import random

WORD_BANK: list[dict[str, str | list[str]]] = [
    {
        "word": "ambiguous",
        "translation": "двусмысленный",
        "distractors": ["амбициозный", "древний", "враждебный"],
    },
    {
        "word": "reluctant",
        "translation": "неохотный",
        "distractors": ["надёжный", "уместный", "блестящий"],
    },
    {
        "word": "endeavor",
        "translation": "стремление",
        "distractors": ["выносливость", "препятствие", "снаряжение"],
    },
    {
        "word": "scrutiny",
        "translation": "тщательная проверка",
        "distractors": ["безопасность", "жертва", "скульптура"],
    },
    {
        "word": "concede",
        "translation": "признать",
        "distractors": ["скрывать", "заключить", "осудить"],
    },
    {
        "word": "resilient",
        "translation": "стойкий",
        "distractors": ["резкий", "блестящий", "отталкивающий"],
    },
    {
        "word": "contemplate",
        "translation": "размышлять",
        "distractors": ["созерцать", "презирать", "соревноваться"],
    },
    {
        "word": "ubiquitous",
        "translation": "вездесущий",
        "distractors": ["уникальный", "неоднозначный", "бесполезный"],
    },
    {
        "word": "meticulous",
        "translation": "скрупулёзный",
        "distractors": ["мелодичный", "величественный", "мистический"],
    },
    {
        "word": "disparity",
        "translation": "неравенство",
        "distractors": ["отчаяние", "исчезновение", "несогласие"],
    },
    {
        "word": "articulate",
        "translation": "чётко выражать",
        "distractors": ["наполнять", "торговать", "украшать"],
    },
    {
        "word": "benevolent",
        "translation": "доброжелательный",
        "distractors": ["благородный", "воинственный", "безразличный"],
    },
    {
        "word": "ephemeral",
        "translation": "мимолётный",
        "distractors": ["вечный", "призрачный", "эпический"],
    },
    {
        "word": "pragmatic",
        "translation": "прагматичный",
        "distractors": ["проблемный", "восторженный", "драматичный"],
    },
    {
        "word": "tenacious",
        "translation": "упорный",
        "distractors": ["нежный", "тревожный", "осторожный"],
    },
    {
        "word": "eloquent",
        "translation": "красноречивый",
        "distractors": ["элегантный", "равнодушный", "эффектный"],
    },
    {
        "word": "alleviate",
        "translation": "облегчить",
        "distractors": ["обвинить", "обогатить", "ускорить"],
    },
    {
        "word": "detrimental",
        "translation": "вредный",
        "distractors": ["решающий", "второстепенный", "непреклонный"],
    },
    {
        "word": "inherent",
        "translation": "присущий",
        "distractors": ["унаследованный", "внутренний", "неприемлемый"],
    },
    {
        "word": "proficient",
        "translation": "умелый",
        "distractors": ["прибыльный", "щедрый", "глубокий"],
    },
    {
        "word": "vindicate",
        "translation": "оправдать",
        "distractors": ["отомстить", "нарушить", "победить"],
    },
    {
        "word": "candid",
        "translation": "откровенный",
        "distractors": ["кандидатский", "случайный", "скрытный"],
    },
    {
        "word": "complacent",
        "translation": "самодовольный",
        "distractors": ["сочувствующий", "покорный", "сложный"],
    },
    {
        "word": "diligent",
        "translation": "усердный",
        "distractors": ["деликатный", "умный", "ленивый"],
    },
    {
        "word": "feasible",
        "translation": "осуществимый",
        "distractors": ["праздничный", "гибкий", "надёжный"],
    },
    {
        "word": "compelling",
        "translation": "убедительный",
        "distractors": ["принудительный", "конкурентный", "жалобный"],
    },
    {
        "word": "obsolete",
        "translation": "устаревший",
        "distractors": ["очевидный", "незаметный", "необычный"],
    },
    {
        "word": "pinnacle",
        "translation": "вершина",
        "distractors": ["частица", "перегородка", "пинцет"],
    },
    {
        "word": "conducive",
        "translation": "способствующий",
        "distractors": ["проводящий", "убедительный", "скромный"],
    },
    {
        "word": "volatile",
        "translation": "изменчивый",
        "distractors": ["добровольный", "объёмный", "ценный"],
    },
    {
        "word": "exacerbate",
        "translation": "обострить",
        "distractors": ["преувеличить", "освободить", "исследовать"],
    },
    {
        "word": "procurement",
        "translation": "закупка",
        "distractors": ["продвижение", "производство", "защита"],
    },
    {
        "word": "impediment",
        "translation": "препятствие",
        "distractors": ["улучшение", "инструмент", "требование"],
    },
    {
        "word": "proliferate",
        "translation": "распространяться",
        "distractors": ["процветать", "запрещать", "откладывать"],
    },
    {
        "word": "substantiate",
        "translation": "обосновать",
        "distractors": ["заменить", "подчинить", "существовать"],
    },
    {
        "word": "prevail",
        "translation": "преобладать",
        "distractors": ["предотвращать", "предсказывать", "притворяться"],
    },
    {
        "word": "repercussion",
        "translation": "последствие",
        "distractors": ["повторение", "восстановление", "обсуждение"],
    },
    {
        "word": "stringent",
        "translation": "строгий",
        "distractors": ["нитевидный", "сильный", "странный"],
    },
    {
        "word": "exemplary",
        "translation": "образцовый",
        "distractors": ["исключительный", "освобождённый", "измученный"],
    },
    {
        "word": "gratuitous",
        "translation": "безосновательный",
        "distractors": ["благодарный", "бесплатный", "великодушный"],
    },
    {
        "word": "precarious",
        "translation": "ненадёжный",
        "distractors": ["предшествующий", "драгоценный", "осторожный"],
    },
    {
        "word": "perpetuate",
        "translation": "увековечить",
        "distractors": ["совершить", "раздражать", "переставить"],
    },
    {
        "word": "eminent",
        "translation": "выдающийся",
        "distractors": ["неизбежный", "излучающий", "эмоциональный"],
    },
    {"word": "nuance", "translation": "нюанс", "distractors": ["помеха", "новинка", "досада"]},
    {
        "word": "leverage",
        "translation": "рычаг воздействия",
        "distractors": ["уровень", "свобода", "наследство"],
    },
    {
        "word": "relinquish",
        "translation": "отказаться",
        "distractors": ["наслаждаться", "пополнить", "различать"],
    },
    {
        "word": "exquisite",
        "translation": "изысканный",
        "distractors": ["истощённый", "чрезмерный", "существующий"],
    },
    {
        "word": "vehement",
        "translation": "яростный",
        "distractors": ["транспортный", "ядовитый", "величавый"],
    },
    {
        "word": "curtail",
        "translation": "сократить",
        "distractors": ["занавесить", "ухаживать", "свернуть"],
    },
    {
        "word": "impeccable",
        "translation": "безупречный",
        "distractors": ["невозможный", "непроницаемый", "нетерпеливый"],
    },
]


def get_random_words(count: int = 30, exclude: list[str] | None = None) -> list[dict]:
    """Get random words from the bank, excluding already shown ones."""
    exclude_set = {w.lower() for w in (exclude or [])}
    available = [w for w in WORD_BANK if w["word"].lower() not in exclude_set]
    random.shuffle(available)
    return available[:count]
