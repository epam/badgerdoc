"""A service with a ternary classifier.
"""
import uvicorn

from . import creator
from .config import settings

app = creator.app

if __name__ == "__main__":
    uvicorn.run(
        "__main__:app",
        root_path=settings.root_path,
        host=settings.app_host,
        port=settings.app_port,
    )
