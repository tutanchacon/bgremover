#!/usr/bin/env python3
"""
Setup script para Background Remover Package
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="bgremover-preserve",
    version="1.0.0",
    author="Tu Nombre",
    author_email="tu.email@ejemplo.com",
    description="Professional background remover with element preservation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tutanchacon/bgremover",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Multimedia :: Graphics :: Graphics Conversion",
        "Topic :: Scientific/Engineering :: Image Processing",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "bgremover=bgremover_package.cli:main",
        ],
    },
    keywords="background removal, image processing, computer vision, rembg",
    project_urls={
        "Bug Reports": "https://github.com/tutanchacon/bgremover/issues",
        "Source": "https://github.com/tutanchacon/bgremover",
    },
)
