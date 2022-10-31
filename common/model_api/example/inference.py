import logging
from pathlib import Path
from typing import Any, Dict, Iterator, Tuple

from .config import settings

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class Model:
    def predict(self, image: Any) -> str:
        return str(image)


def get_model() -> Any:
    """Get a model."""
    model = Model()
    return model


def inference(
    model: Any, image_paths: Iterator[Path]
) -> Iterator[Tuple[str, Dict[str, Any]]]:
    """Run inference for several images."""

    for image_path in image_paths:
        yield image_path.name, {
            "category": "latex",
            "data": {"model_data": model.predict(image_path)},
        }
