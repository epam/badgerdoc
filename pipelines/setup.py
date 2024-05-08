import setuptools

setuptools.setup(
    name="pipelines",
    version="0.1.0",
    packages=["pipelines"],
    package_dir={"pipelines": "pipelines"},
    entry_points={"console_scripts": ["executor = pipelines.cli:execute"]},
)
