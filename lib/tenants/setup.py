from typing import List

from setuptools import setup


def get_requirements(path: str) -> List[str]:
    with open(path, "r", encoding="utf-8") as file:
        return [row.strip() for row in file.readlines()]


def get_long_description(path: str) -> str:
    with open(path, "r", encoding="utf-8") as file:
        return file.read()


setup(
    name="tenants",
    version="0.1.0",
    description="Package for validating and parsing jwt via FastAPI dependency",
    long_description=get_long_description("README.md"),
    author="Roman Kuzianov",
    author_email="Roman_Kuzianov@epam.com",
    packages=["tenants"],
    package_dir={"tenants": "src"},
    install_requires=get_requirements("requirements.txt"),
    extras_require={"dev": get_requirements("requirements-dev.txt")},
)
