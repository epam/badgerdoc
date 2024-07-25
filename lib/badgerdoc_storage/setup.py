from typing import List

from setuptools import setup


def get_requirements(path: str) -> List[str]:
    with open(path, "r", encoding="utf-8") as file:
        return [row.strip() for row in file.readlines()]


setup(
    name="badgerdoc_storage",
    version="1.8.2",
    description="Package for working with storage providers",
    author="Ruslan Khyurri",
    author_email="ruslan_khyurri@epam.com",
    packages=["badgerdoc_storage"],
    install_requires=get_requirements("requirements.txt"),
    # extras_require={"dev": get_requirements("requirements-dev.txt")},
)
