from nltk.tokenize import sent_tokenize
import nltk

def concat_page_text(page_chars: list) -> list:
    """
    Collect all OCR characters for page and joins them into sentences.
    `after` is an indicator of next word (space,dot or else)
    """

    text = ""
    for obj in page_chars:
        text += obj["text"]
        if "after" in obj:
            text += obj["after"]
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt')
    return sent_tokenize(text)
