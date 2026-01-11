"""Setup script for Airbnb Price Predictor."""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="airbnb-price-predictor",
    version="1.0.0",
    author="Neeraj Mehta",
    description="Machine Learning system for predicting Airbnb listing prices",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/NeerajMehta15/Airbnb-Price-Predictor",
    packages=find_packages(exclude=["tests", "notebooks"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "airbnb-api=src.api.app:main",
        ],
    },
)
