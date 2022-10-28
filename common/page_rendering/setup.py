# -*- coding: utf-8 -*-
from setuptools import setup

packages = ["page_rendering"]

package_data = {"": ["*"]}

install_requires = [
    "minio>=7.1.1,<8.0.0",
    "pdfplumber>=0.5.28,<0.6.0",
    "pydantic>=1.8.2,<2.0.0",
]

entry_points = {
    "console_scripts": [
        "add-logging = commands:add_logger",
        "get-setup = commands:get_setup",
    ]
}

setup_kwargs = {
    "name": "page-rendering",
    "version": "0.1.0",
    "description": "",
    "long_description": None,
    "author": None,
    "author_email": None,
    "maintainer": None,
    "maintainer_email": None,
    "url": None,
    "packages": packages,
    "package_data": package_data,
    "install_requires": install_requires,
    "entry_points": entry_points,
    "python_requires": ">=3.8,<4.0",
}


setup(**setup_kwargs)
