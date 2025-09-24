#!/usr/bin/env python3
"""
Setup script for vclip - Command Snippet Manager
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of README file
this_directory = Path(__file__).parent
long_description = ""
readme_path = this_directory / "README.md"
if readme_path.exists():
    long_description = readme_path.read_text(encoding='utf-8')

# Read requirements
requirements = []
req_path = this_directory / "requirements.txt"
if req_path.exists():
    with open(req_path, 'r', encoding='utf-8') as f:
        requirements = [
            line.strip() for line in f
            if line.strip() and not line.startswith('#')
        ]

setup(
    name="vclip",
    version="0.1.0",
    description="Command Snippet Manager with rofi integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="vclip",
    python_requires=">=3.7",
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "vclip=cmd_manager.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        'config': ['*.yaml'],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: X11 Applications",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
    ],
    keywords="cli rofi clipboard commands snippets markdown",
    project_urls={
        "Source": "https://github.com/vclip/vclip",
        "Bug Reports": "https://github.com/vclip/vclip/issues",
    },
)