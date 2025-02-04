"""qureed installation configuration"""

import os

from setuptools import find_packages, setup

current_dir = os.path.abspath(os.path.dirname(__file__))
setup(
    name="qureed_project_server",
    version="0.0.1",
    author="Simon Sekavčnik",
    author_email="simon.sekavcnik@tum.de",
    description="QuReed Grafical Interface Server",
    license="Apache 2.0",
    packages=find_packages(where="."),
    install_requires=[
        "grpcio",
        "protobuf",
        "virtualenv-api",
        "mpmath"
    ],
    entry_points={
        "console_scripts": [
            "qureed_server=qureed_project_server.server:main",  # Maps the 'qureed_server' command to 'server.py'
        ],
    },
)
