
import pytest

from app.rag.text_processor import TextProcessor


@pytest.fixture
def processor():
    return TextProcessor()


def test_normalizes_line_endings(processor):
    result = processor.clean("Line 1\r\nLine 2\rLine 3")

    assert result == "Line 1\nLine 2\nLine 3"


def test_removes_control_characters(processor):
    result = processor.clean("Hello\x00World\x07")

    assert result == "HelloWorld"


def test_normalizes_excessive_spaces(processor):
    result = processor.clean("Enterprise    AI     Assistant")

    assert result == "Enterprise AI Assistant"


def test_reduces_excessive_blank_lines(processor):
    result = processor.clean("Line 1\n\n\n\nLine 2")

    assert result == "Line 1\n\nLine 2"


def test_preserves_markdown_formatting(processor):
    markdown = """# RAG Knowledge

## Components

- FastAPI
- Azure OpenAI

| Component | Technology |
|---|---|
| API | FastAPI |

```python
def hello():
    print("Hello")
```"""

    result = processor.clean(markdown)

    assert "# RAG Knowledge" in result
    assert "## Components" in result
    assert "- FastAPI" in result
    assert "| Component | Technology |" in result
    assert "```python" in result
    assert '    print("Hello")' in result


def test_rejects_empty_content(processor):
    with pytest.raises(ValueError, match="cannot be empty"):
        processor.clean("   \n  ")


def test_rejects_non_string_content(processor):
    with pytest.raises(TypeError):
        processor.clean(None)
