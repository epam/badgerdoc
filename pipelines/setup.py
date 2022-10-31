import setuptools

setuptools.setup(
    name="pipelines",
    version="0.1.0",
    packages=["src"],
    package_dir={"pipelines": "src"},
    entry_points={"console_scripts": ["executor = src.cli:execute"]},
)
