from typing import List

from setuptools import setup


def get_requirements(path: str) -> List[str]:
    with open(path, "r", encoding="utf-8") as file:
        return [row.strip() for row in file.readlines()]


def get_long_description(path: str) -> str:
    with open(path, "r", encoding="utf-8") as file:
        return file.read()


setup(
    name="filter_lib",
    version="0.2.0",
    description="Package for filtering and sorting sqlalchemy entities",
    long_description=get_long_description("README.md"),
    author="Roman Kuzianov",
    author_email="Roman_Kuzianov@epam.com",
    packages=["filter_lib"],
    package_dir={"filter_lib": "src"},
    install_requires=get_requirements("requirements.txt"),
    extras_require={"dev": get_requirements("requirements-dev.txt")},
)
