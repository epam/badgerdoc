import asyncio
from pathlib import Path
import os
import sys
from importlib import import_module
from uvicorn.config import Config
from uvicorn.server import Server
from uvicorn.supervisors import ChangeReload, Multiprocess

ROOT_PATH = Path(__file__).parent.parent.parent.parent


class RunnerRegistry(type):
    RUNNERS: dict[str, type]

    def __new__(mcs, name, bases, attrs):
        new_class = super().__new__(mcs, name, bases, attrs)
        if not hasattr(mcs, "RUNNERS"):
            mcs.RUNNERS = {}
        elif new_class.__name__ != "BaseRunner":
            mcs.RUNNERS[new_class.PACKAGE_NAME] = new_class
        return new_class

    @classmethod
    def get_runners(mcs) -> dict[str, type]:
        return mcs.RUNNERS

    @classmethod
    async def run(mcs, services: tuple[str]):
        if not services:
            services = mcs.get_runners().keys()
        runners: [BaseRunner] = []
        for runner in mcs.get_runners().values():
            if runner.IS_ACTIVE and runner.PACKAGE_NAME in services:
                service = runner().run_app_async()
                service.__name__ = runner.PACKAGE_NAME
                runners.append(service)
        done, pending = await asyncio.wait([service for service in runners], return_when=asyncio.FIRST_COMPLETED)
        for task in pending:
            task.cancel()


class BaseRunner(metaclass=RunnerRegistry):
    PACKAGE_NAME: str
    APP_NAME: str = "app"
    MODULE_NAME: str = "main"
    PORT: int
    HOST: str = "localhost"
    DB_CREDENTIALS: dict = {}
    ENVIRONMENT: dict = {}
    IS_ACTIVE: bool = True

    def __init__(self, *args, **kwargs):
        for attr in ["PACKAGE_NAME", "PORT"]:
            if not hasattr(self, attr):
                raise NotImplementedError(f"{attr} is not set")
        super().__init__(*args, **kwargs)

    def run(self):
        self.setup_env()
        self.run_app()

    @staticmethod
    def _default_db_credentials() -> dict[str, str]:
        return {
            "POSTGRES_USER": "postgres",
            "POSTGRES_PASSWORD": "",
            "POSTGRES_HOST": "localhost",
            "POSTGRES_PORT": "5432",
            "POSTGRES_DB": "postgres"
        }

    @staticmethod
    def _default_environment() -> dict[str, str]:
        return {
            "ANNOTATION_NO_AUTH": "True",
        }

    def setup_env(self):
        db_credentials = self._default_db_credentials()
        db_credentials.update(self.DB_CREDENTIALS)
        environment = self._default_environment()
        environment.update(self.ENVIRONMENT)
        os.environ.update(environment)
        os.environ.update(db_credentials)

    def create_server(self):
        print(f"Starting {self.PACKAGE_NAME} on port {self.PORT}")
        self.setup_env()
        sys.path.append(str(ROOT_PATH / self.PACKAGE_NAME))
        app = import_module(f"{self.APP_NAME}.{self.MODULE_NAME}").app
        sys.path = sys.path[:-1]

        config = Config(app, host=self.HOST, port=self.PORT, reload=True)  # TODO: check additional folders for reloading
        server = Server(config=config)

        if config.should_reload:
            sock = config.bind_socket()
            ChangeReload(config, target=server.run, sockets=[sock]).run()
        elif config.workers > 1:
            sock = config.bind_socket()
            Multiprocess(config, target=server.run, sockets=[sock]).run()
        else:
            return server
        if config.uds:
            os.remove(config.uds)

    def run_app(self):
        self.create_server().run()

    async def run_app_async(self):
        await self.create_server().serve()
