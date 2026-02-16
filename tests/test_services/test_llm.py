from bot.services.llm import explain_word, format_explanation


async def test_explain_word(mock_gigachat):
    result = await explain_word("example")

    assert result.translation == "пример"
    assert result.translations == ["пример", "образец", "экземпляр"]
    assert result.corrected_word is None  # same word, no correction
    assert len(result.meanings) == 1
    assert len(result.examples) == 1
    assert len(result.collocations) == 1
    assert "example" in result.raw_text
    mock_gigachat.assert_called_once()


async def test_explain_word_with_correction(mock_gigachat):
    """Test that corrected_word is set when LLM returns a different spelling."""
    from unittest.mock import MagicMock

    # Override mock to return corrected spelling
    mock_instance = mock_gigachat.return_value
    actual_client = mock_instance.__aenter__.return_value

    mock_message = MagicMock()
    mock_message.content = (
        '{"corrected_word": "example", '
        '"translation": "пример", '
        '"translations": ["пример"], '
        '"meanings": [], "examples": [], "collocations": []}'
    )
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    actual_client.achat.return_value = mock_response

    result = await explain_word("exapmle")  # typo
    assert result.corrected_word == "example"


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
