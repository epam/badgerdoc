import base64
import json
import logging
import math
import os
import re
from io import BytesIO

from openai import AsyncOpenAI
from PIL import Image

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "rednote-hilab/dots.ocr"
VLLM_BASE_URL = os.getenv("DOTS_OCR_ENDPOINT")

DEFAULT_PROMPT = """Please output the layout information from the PDF image, including each layout element's bbox, its category, and the corresponding text content within the bbox.

1. Bbox format: [x1, y1, x2, y2]

2. Layout Categories: The possible categories are ['Caption', 'Footnote', 'Formula', 'List-item', 'Page-footer', 'Page-header', 'Picture', 'Section-header', 'Table', 'Text', 'Title'].

3. Text Extraction & Formatting Rules:
    - Picture: For the 'Picture' category, the text field should be omitted.
    - Formula: Format its text as LaTeX.
    - Table: Format its text as HTML.
    - All Others (Text, Title, etc.): Format their text as Markdown.

4. Constraints:
    - The output text must be the original text from the image, with no translation.
    - All layout elements must be sorted according to human reading order.

5. Final Output: The entire output must be a single JSON object.
"""

_JSON_DICT_RE = re.compile(
    r'\{[^{}]*?"bbox"\s*:\s*\[[^\]]*?\][^{}]*?\}', re.DOTALL
)


def _to_base64(image: Image.Image, format: str = "PNG") -> str:
    """Encodes PIL image to base64 data URI."""
    buffered = BytesIO()
    image.save(buffered, format=format)
    base64_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return f"data:image/{format.lower()};base64,{base64_str}"


def _round_by_factor(number: float, factor: int) -> int:
    return round(number / factor) * factor


def _ceil_by_factor(number: float, factor: int) -> int:
    return math.ceil(number / factor) * factor


def _floor_by_factor(number: float, factor: int) -> int:
    return math.floor(number / factor) * factor


def resize_to_fit(
    height: int,
    width: int,
    factor: int = 28,
    min_pixels: int = 3136,
    max_pixels: int = 11289600,
):
    if max(height, width) / min(height, width) > 200:
        raise ValueError(
            f"absolute aspect ratio must be smaller than 200, got {max(height, width) / min(height, width)}"
        )
    h_bar = max(factor, _round_by_factor(height, factor))
    w_bar = max(factor, _round_by_factor(width, factor))
    if h_bar * w_bar > max_pixels:
        beta = math.sqrt((height * width) / max_pixels)
        h_bar = max(factor, _floor_by_factor(height / beta, factor))
        w_bar = max(factor, _floor_by_factor(width / beta, factor))
    elif h_bar * w_bar < min_pixels:
        beta = math.sqrt(min_pixels / (height * width))
        h_bar = _ceil_by_factor(height * beta, factor)
        w_bar = _ceil_by_factor(width * beta, factor)
        if h_bar * w_bar > max_pixels:
            beta = math.sqrt((h_bar * w_bar) / max_pixels)
            h_bar = max(factor, _floor_by_factor(h_bar / beta, factor))
            w_bar = max(factor, _floor_by_factor(w_bar / beta, factor))
    return h_bar, w_bar


def prepare_image(
    image: Image.Image,
) -> Image.Image:
    if image.mode != "RGB":
        image = image.convert("RGB")

    h, w = resize_to_fit(image.height, image.width)
    if h != image.height or w != image.width:
        image = image.resize((w, h))

    return image


def _clean_model_output(model_output: str) -> str:
    try:
        json.loads(model_output)
        return model_output
    except json.JSONDecodeError:
        matches = _JSON_DICT_RE.findall(model_output)
        if not matches:
            return model_output

        cleaned_items = []
        for match in matches:
            try:
                item = json.loads(match)
                cleaned_items.append(item)
            except json.JSONDecodeError:
                continue

        return json.dumps(cleaned_items, ensure_ascii=False)


async def infer_layout(
    image: Image.Image,
    prompt: str = DEFAULT_PROMPT,
    temperature: float = 0.1,
    top_p: float = 1.0,
) -> str:
    client = AsyncOpenAI(api_key="no-key", base_url=VLLM_BASE_URL)
    base64_image = _to_base64(image)
    vllm_prompt = f"<|img|><|imgpad|><|endofimg|>{prompt}"

    try:
        response = await client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": base64_image},
                        },
                        {"type": "text", "text": vllm_prompt},
                    ],
                }
            ],
            temperature=temperature,
            top_p=top_p,
            max_tokens=16384,
        )

        raw_output = response.choices[0].message.content
        if not raw_output:
            return "[]"

        return _clean_model_output(raw_output)

    except Exception as e:
        logger.error("Error during vLLM inference: %s", e)
        raise
