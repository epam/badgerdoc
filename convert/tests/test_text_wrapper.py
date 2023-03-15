import collections
import string

from assets.converters.text.text_to_tokens_converter import (  # noqa: E501
    TextWrapper,
)


def test_pop_beginning_whitespaces_text_begin_with_whitespaces():
    tw = TextWrapper(line_length=50)
    text = collections.deque(string.whitespace + "text" + "  ")

    result = tw.pop_beginning_whitespaces(text)

    assert result == list(string.whitespace)


def test_pop_beginning_whitespaces_not_whitespaces():
    tw = TextWrapper(line_length=50)
    text = collections.deque("text" + "  ")

    result = tw.pop_beginning_whitespaces(text)

    assert result == []


def test_pop_next_word_begin_with_whitespaces():
    tw = TextWrapper(line_length=50)
    text = collections.deque(" " + "text")

    result = tw.pop_next_word(text)

    assert result == []


def test_pop_next_word_text_contains_several_verbs():
    tw = TextWrapper(line_length=50)
    text = collections.deque("word1 word2 word3")

    result = tw.pop_next_word(text)

    assert result == ["w", "o", "r", "d", "1"]


def test_wrap_short_paragraph():
    tw = TextWrapper(line_length=40)
    text = "word1 word2 word3 word4 word5"

    result = tw.wrap_paragraph(text)

    assert result == [text]


def test_wrap_paragraph_started_with_spaces():
    tw = TextWrapper(line_length=20)
    text = "  word1 word2 word3 word4 word5"

    result = tw.wrap_paragraph(text)

    assert result == ["  word1 word2 word3 ", "word4 word5"]


def test_wrap_paragraph_with_long_word():
    tw = TextWrapper(line_length=10)
    text = "word1 very_long_word word2"

    result = tw.wrap_paragraph(text)

    assert result == ["word1 ", "very_long_", "word word2"]


def test_wrap_paragraph_with_long_word_at_the_beginning():
    tw = TextWrapper(line_length=10)
    text = "very_long_word word1 word2"

    result = tw.wrap_paragraph(text)

    assert result == ["very_long_", "word word1 ", "word2"]


def test_wrap_paragraph_with_word_multiple_times_longer_then_string():
    tw = TextWrapper(line_length=10)
    text = "word1 very_long_word_which_can't_be_fitted_even_in_two_or_three_lines word2 word3"  # noqa: E501

    result = tw.wrap_paragraph(text)

    assert result == [
        "word1 ",
        "very_long_",
        "word_which",
        "_can't_be_",
        "fitted_eve",
        "n_in_two_o",
        "r_three_li",
        "nes word2 ",
        "word3",
    ]


def test_wrap_empty_text():
    tw = TextWrapper(line_length=10)
    text = ""

    result = tw.wrap(text)

    assert result == []


def test_wrap_single_paragraph_text():
    tw = TextWrapper(line_length=20)
    text = "Text which contains only one paragraph"

    result = tw.wrap(text)

    assert result == ["Text which contains ", "only one paragraph"]


def test_wrap_text_with_several_paragraphs():
    tw = TextWrapper(line_length=20)
    text = (
        "Text which contains more then one paragraph\n"
        "It is the second paragraph"
    )

    result = tw.wrap(text)
    assert result == [
        "Text which contains ",
        "more then one ",
        "paragraph\n",
        "It is the second ",
        "paragraph",
    ]
