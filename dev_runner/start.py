import asyncio
from pathlib import Path

import click
from dotenv import load_dotenv

from dev_runner.runners.base_runner import RunnerRegistry
from dev_runner.runners.annotation_runner import AnnotationRunner
from dev_runner.runners.assets_runner import AssetsRunner
from dev_runner.runners.convert_runner import ConvertRunner
from dev_runner.runners.jobs_runner import JobsRunner
from dev_runner.runners.models_runner import ModelsRunner
from dev_runner.runners.pipelines_runner import PipelinesRunner
from dev_runner.runners.processing_runner import ProcessingRunner
from dev_runner.runners.scheduler_runner import SchedulerRunner
from dev_runner.runners.search_runner import SearchRunner
from dev_runner.runners.taxonomy_runner import TaxonomyRunner
from dev_runner.runners.users_runner import UsersRunner


ROOT_DIR = Path(__file__).parent
SHARED_DOT_ENV = ROOT_DIR / "conf" / "shared.env"


def _info(message):
    click.echo(click.style(message, fg="green"))


@click.command()
@click.argument("services", nargs=-1, type=click.Choice(RunnerRegistry.get_runners().keys()))
def cli(services):
    _info(f"Starting {services or 'all'} service{'s' if not services or len(services) > 1 else ''}...")
    load_dotenv(SHARED_DOT_ENV)
    asyncio.run(RunnerRegistry.run(services))


if __name__ == "__main__":
    cli()
