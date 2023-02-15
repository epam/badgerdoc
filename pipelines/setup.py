import setuptools

setuptools.setup(
    name="pipelines",
    version="0.1.0",
    packages=["users"],
    package_dir={"pipelines": "users"},
    entry_points={"console_scripts": ["executor = users.cli:execute"]},
)
