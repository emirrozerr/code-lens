from setuptools import find_packages, setup

setup(
    name="codelens",
    version="0.1.0",
    packages=find_packages(),
    install_requires=["click>=8.0"],
    entry_points={"console_scripts": ["codelens=cli.main:cli"]},
)
