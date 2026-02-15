from bot.services.llm import explain_word, format_explanation


async def test_explain_word(mock_gigachat):
    result = await explain_word("example")

    assert result.translation == "пример"
    assert len(result.meanings) == 1
    assert len(result.examples) == 1
    assert len(result.collocations) == 1
    assert "example" in result.raw_text
    mock_gigachat.assert_called_once()


def test_format_explanation():
    text = format_explanation(
        word="test",
        translation="тест",
        meanings=[{"meaning": "тест", "explanation": "проверка"}],
        examples=[{"en": "This is a test", "ru": "Это тест"}],
        collocations=[{"en": "test case", "ru": "тестовый случай"}],
    )

    assert "<b>test</b>" in text
    assert "тест" in text
    assert "This is a test" in text
    assert "test case" in text
