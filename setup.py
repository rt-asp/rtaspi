#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Installation of the rtaspi package.
"""

import os
from setuptools import setup, find_packages

# Long description from README.md
try:
    with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), "README.md"), encoding="utf-8") as f:
        LONG_DESCRIPTION = '\n' + f.read()
except FileNotFoundError:
    LONG_DESCRIPTION = ''

# Get version from _version.py
version = {}
with open("src/rtaspi/_version.py") as f:
    exec(f.read(), version)

# Configuration setup
setup(
    name="rtaspi",
    version=version["__version__"],
    description="Real-Time Annotation and Stream Processing Interface",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    author="Tom Sapletta",
    author_email="info@softreck.dev",
    maintainer="rtaspi developers",
    maintainer_email="info@softreck.dev",
    python_requires=">=3.11",
    url="https://rtaspi.rtasp.com",
    install_requires=[
        # Core dependencies
        "pyyaml>=6.0.1",
        "psutil>=5.9.0",
        "requests>=2.31.0",
        "urllib3>=1.26.9",
        
        # Streaming dependencies
        "websockets>=10.3",
        "aiohttp>=3.8.0",
        "fastapi>=0.110.0",
        "uvicorn>=0.27.0",
        
        # HTTPS/Certificate management
        "python-acme>=2.7.0",
        "cryptography>=42.0.0",
        "certbot>=2.7.0",
        "dnspython>=2.4.0",
        
        # Device discovery
        "upnpclient>=1.0.3",
        "zeroconf>=0.38.1",
        "wsdiscovery>=2.0.0",
        "onvif-zeep>=0.2.12",
        
        # Media processing
        "opencv-python>=4.6.0",
        "numpy>=1.22.3",
        "Pillow>=9.1.0",
        "pyaudio>=0.2.13",
        
        # Protocol support
        "grpcio>=1.62.0",
        "grpcio-tools>=1.62.0",
        "paho-mqtt>=1.6.0",
        "redis>=4.0.0",
    ],
    extras_require={
        "dev": [
            # Testing
            "pytest>=7.1.2",
            "pytest-cov>=2.12.1",
            "pytest-asyncio>=0.21.0",
            
            # Code quality
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            
            # Type checking
            "types-requests>=2.31.0",
            "types-PyYAML>=6.0.1",
            "types-psutil>=5.9.0",
        ],
    },
    project_urls={
        "Repository": "https://github.com/rt-asp/python",
        "Changelog": "https://github.com/rt-asp/python/releases",
        "Wiki": "https://github.com/rt-asp/python/wiki",
        "Issue Tracker": "https://github.com/rt-asp/python/issues/new",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    entry_points={
        'console_scripts': [
            'rtaspi=rtaspi.main:main',
        ],
    },
    license="Apache-2.0",
    license_files=("LICENSE",),
    keywords=["python", "rtaspi", "streaming", "real-time", "annotation", "processing"],
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Topic :: Multimedia :: Video',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
