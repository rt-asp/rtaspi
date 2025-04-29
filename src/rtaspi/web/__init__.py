"""
Web server module for rtaspi.

This module provides a web server with:
- HTTPS support with automatic certificates
- REST API with OpenAPI documentation
- Web interface for device management
- Matrix view for cameras/microphones
- Configuration and control interface
"""

__version__ = "1.0.0"
__author__ = "RT-ASP Team"
__all__ = ["WebServer", "APIServer", "WebInterface"]

from .server import WebServer
from .api import APIServer
from .interface import WebInterface

# Version history:
# 1.0.0 - Initial release with web server components
#       - HTTPS support with automatic certificates
#       - REST API with OpenAPI documentation
#       - Web interface with device management
#       - Matrix view for cameras/microphones
#       - Configuration and control interface
