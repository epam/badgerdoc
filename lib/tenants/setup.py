from typing import List

from setuptools import setup


def get_requirements(path: str) -> List[str]:
    with open(path, "r", encoding="utf-8") as file:
        return [row.strip() for row in file.readlines()]


def get_long_description(path: str) -> str:
    with open(path, "r", encoding="utf-8") as file:
        return file.read()


setup(
    name="tenant_dependency",
    version="0.1.3",
    description="Package for validating and parsing jwt via FastAPI dependency",  # noqa
    long_description=get_long_description("README.md"),
    author="Roman Kuzianov",
    author_email="Roman_Kuzianov@epam.com",
    packages=["tenant_dependency"],
    package_dir={"tenant_dependency": "src"},
    install_requires=get_requirements("requirements.txt"),
    extras_require={"dev": get_requirements("requirements-dev.txt")},
)
