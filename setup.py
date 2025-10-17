#!/usr/bin/env python3
"""
Setup script for the observables package.
This is a fallback for tools that don't support pyproject.toml.
"""

from setuptools import setup, find_packages

# Read the README file
def read_readme() -> str:
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements() -> list[str]:
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

# Read version
def read_version() -> str:
    try:
        with open("observables/_version.py", "r", encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("__version__"):
                    return line.split("=")[1].strip().strip('"\'')
        raise FileNotFoundError("Version file not found")
    except FileNotFoundError:
        return "4.1.9"  # fallback version

setup(
    name="observables",
    version=read_version(),
    author="Benedikt Axel Brandes",
    author_email="benedikt.brandes@gmail.com",
    description="Centralized Reactive Programming - A Python library for creating observable objects with centralized value storage and automatic transitive binding",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/benediktbrandes/observables",
    project_urls={
        "Bug Tracker": "https://github.com/benediktbrandes/observables/issues",
        "Documentation": "https://github.com/benediktbrandes/observables#readme",
        "Source Code": "https://github.com/benediktbrandes/observables",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: User Interfaces",
        "Topic :: Software Development :: Object Brokering",
    ],
    python_requires=">=3.12",
    install_requires=[],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "docs": [
            "sphinx>=6.0.0",
            "sphinx-rtd-theme>=1.0.0",
            "myst-parser>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "observables-demo=observables.examples.demo:main",
        ],
    },
    package_data={
        "observables": ["py.typed", "_version.py"],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="observable, binding, reactive, event-driven, observer-pattern",
)
