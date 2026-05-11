import logging
import os

from temporalio import activity

logger = logging.getLogger(__name__)

HOST = os.environ.get("HOST_ADDRESS_FOR_MLX", "localhost")


@activity.defn
async def do_mlx_ocr(
    image_url: str,
    port: str,
    model: str,
    prompt: str,
    max_tokens: int = 10000,
) -> str:
    """Send an image to an MLX server and return the raw text response."""
    import openai  # pylint: disable=import-outside-toplevel

    logger.info(
        "do_mlx_ocr: model=%s port=%s image=%s", model, port, image_url
    )

    client = openai.OpenAI(
        base_url=f"http://{HOST}:{port}/v1", api_key="not-needed"
    )
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": image_url, "detail": "high"},
                    },
                ],
            }
        ],
        stream=False,
        max_tokens=max_tokens,
    )

    result = response.choices[0].message.content or ""
    logger.info("do_mlx_ocr: completed, response length=%d", len(result))
    return result


@activity.defn
async def do_mlx_ocr_mineru(
    image_url: str,
    port: str,
    model: str,
) -> list[dict]:
    """Download an image and run MinerU two-step OCR on it.

    Returns a list of block dicts with keys: type, bbox, content.
    """
    import aiohttp  # pylint: disable=import-outside-toplevel
    from io import BytesIO  # pylint: disable=import-outside-toplevel

    from mineru_vl_utils import MinerUClient  # pylint: disable=import-outside-toplevel
    from PIL import Image  # pylint: disable=import-outside-toplevel

    logger.info(
        "do_mlx_ocr_mineru: model=%s port=%s image=%s", model, port, image_url
    )

    async with aiohttp.ClientSession() as session:
        async with session.get(image_url) as resp:
            image_bytes = await resp.read()

    image = Image.open(BytesIO(image_bytes))

    client = MinerUClient(
        backend="http-client",
        model_name=model,
        server_url=f"http://{HOST}:{port}",
    )
    result = await client.aio_two_step_extract(image)

    blocks = [
        {"type": b["type"], "bbox": b["bbox"], "content": b["content"] or ""}
        for b in result
    ]
    logger.info(
        "do_mlx_ocr_mineru: completed, %d block(s) detected", len(blocks)
    )
    return blocks
