"""qureed installation configuration"""

import os

from setuptools import find_packages, setup

current_dir = os.path.abspath(os.path.dirname(__file__))
setup(
    name="qureed_project_server",
    version="0.0.1",
    author="Simon Sekavčnik",
    author_email="simon.sekavcnik@tum.de",
    description="QuReed Grafical Interface",
    license="Apache 2.0",
    packages=find_packages(where="."),
    install_requires=[
        "grpcio",
        "protobuf"
    ],
    entry_points={
    },
)
