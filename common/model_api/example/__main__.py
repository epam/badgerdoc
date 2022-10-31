from pathlib import Path

import uvicorn
from model_api.common.minio_utils import MinioCommunicator
from model_api.creator import create_app
from model_api import config

from .config import settings
from .inference import get_model, inference

app = create_app(get_model=get_model,
                 inference=inference,
                 bucket=settings.data_bucket,
                 model_files=None,
                 destination=Path(settings.volume_path) / settings.model_path,
                 loader=MinioCommunicator()
                 )
# download_model(loader=MinioCommunicator())

config.settings = settings

if __name__ == "__main__":
    uvicorn.run(
        "__main__:app",
        root_path=config.settings.root_path,
        host=config.settings.app_host,
        port=config.settings.app_port,
    )
