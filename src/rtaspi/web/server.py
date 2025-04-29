"""
Web server implementation.

This module provides the main web server class that handles HTTPS, certificates,
and server configuration.
"""

import os
import ssl
import logging
import asyncio
import datetime
from typing import Optional, Dict, Any
from pathlib import Path
from aiohttp import web
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from rtaspi.api import ServerAPI
from .api import APIServer
from .interface import WebInterface
from .acme import ACMEClient, challenge_handler


class WebServer:
    """Main web server class."""

    def __init__(self):
        """Initialize the web server."""
        self.logger = logging.getLogger(__name__)
        self.server_api = ServerAPI()
        self.app = web.Application()
        self.runner = None
        self.site = None

        # Initialize components
        self.api_server = APIServer(self.app)
        self.web_interface = WebInterface(self.app)

        # Configure routes
        self._setup_routes()

    def _setup_routes(self) -> None:
        """Set up web server routes."""
        # Static files
        self.app.router.add_static(
            "/static", Path(__file__).parent / "static", name="static"
        )

        # Main routes
        self.app.router.add_get("/", self.web_interface.index_handler)
        self.app.router.add_get("/matrix", self.web_interface.matrix_handler)
        self.app.router.add_get("/config", self.web_interface.config_handler)

        # API documentation
        self.app.router.add_get("/docs", self.api_server.docs_handler)
        self.app.router.add_get("/openapi.json", self.api_server.openapi_handler)

    async def start(
        self,
        host: str = "127.0.0.1",
        port: int = 8080,
        ssl: bool = False,
        cert_file: Optional[str] = None,
        key_file: Optional[str] = None,
        domain: Optional[str] = None,
        email: Optional[str] = None,
        staging: bool = True,
        workers: int = 1,
        debug: bool = False,
    ) -> None:
        """Start the web server.

        Args:
            host: Host to bind to
            port: Port to listen on
            ssl: Whether to enable HTTPS
            cert_file: Path to SSL certificate file
            key_file: Path to SSL private key file
            domain: Domain name for automatic certificate
            email: Email for Let's Encrypt notifications
            staging: Whether to use Let's Encrypt staging
            workers: Number of worker processes
            debug: Whether to enable debug mode
        """
        # Configure SSL context if enabled
        ssl_context = None
        if ssl:
            if domain and email:
                # Check if certificate needs renewal
                acme_client = ACMEClient(domain, email, staging)
                await acme_client.initialize()
                needs_renewal = await acme_client.check_certificate()

                if needs_renewal:
                    # Generate new certificate using Let's Encrypt
                    cert_info = await self._generate_certificate(
                        domain=domain, email=email, staging=staging
                    )
                    cert_file = cert_info["cert_file"]
                    key_file = cert_info["key_file"]
                else:
                    # Use existing certificate
                    cert_file = str(Path("certs") / "server.crt")
                    key_file = str(Path("certs") / "server.key")
            elif not (cert_file and key_file):
                # Generate self-signed certificate
                cert_info = self._generate_self_signed_certificate()
                cert_file = cert_info["cert_file"]
                key_file = cert_info["key_file"]

            # Create SSL context
            ssl_context = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
            ssl_context.load_cert_chain(cert_file, key_file)

        # Configure application
        self.app["config"] = {
            "host": host,
            "port": port,
            "ssl": ssl,
            "cert_file": cert_file,
            "key_file": key_file,
            "domain": domain,
            "workers": workers,
            "debug": debug,
        }

        # Start server
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()

        self.site = web.TCPSite(
            self.runner, host=host, port=port, ssl_context=ssl_context
        )
        await self.site.start()

        self.logger.info(
            f"Started web server on " f"{'https' if ssl else 'http'}://{host}:{port}"
        )

    async def stop(self) -> None:
        """Stop the web server."""
        if self.site:
            await self.site.stop()
            self.site = None

        if self.runner:
            await self.runner.cleanup()
            self.runner = None

        self.logger.info("Stopped web server")

    async def _generate_certificate(
        self, domain: str, email: str, staging: bool = True
    ) -> Dict[str, str]:
        """Generate SSL certificate using Let's Encrypt.

        Args:
            domain: Domain name for the certificate
            email: Email address for Let's Encrypt notifications
            staging: Whether to use Let's Encrypt staging environment

        Returns:
            Dictionary containing paths to generated files
        """
        # Initialize ACME client
        acme_client = ACMEClient(domain, email, staging)
        await acme_client.initialize()

        # Add challenge handler route
        self.app["acme_client"] = acme_client
        self.app.router.add_get(
            "/.well-known/acme-challenge/{token}", challenge_handler
        )

        try:
            # Obtain certificate
            cert_info = await acme_client.obtain_certificate()
            self.logger.info(f"Generated Let's Encrypt certificate for {domain}")
            return cert_info
        except Exception as e:
            self.logger.error(f"Failed to obtain Let's Encrypt certificate: {e}")
            self.logger.info("Falling back to self-signed certificate")
            return self._generate_self_signed_certificate(domain)
        finally:
            # Cleanup
            self.app["acme_client"] = None

    def _generate_self_signed_certificate(
        self, domain: Optional[str] = None
    ) -> Dict[str, str]:
        """Generate self-signed SSL certificate.

        Args:
            domain: Optional domain name for the certificate

        Returns:
            Dictionary containing paths to generated files
        """
        # Create output directory
        certs_dir = Path("certs")
        certs_dir.mkdir(parents=True, exist_ok=True)

        # Generate key
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

        # Create certificate
        subject = issuer = x509.Name(
            [x509.NameAttribute(NameOID.COMMON_NAME, domain or "localhost")]
        )

        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(private_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.datetime.utcnow())
            .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365))
            .add_extension(
                x509.SubjectAlternativeName([x509.DNSName(domain or "localhost")]),
                critical=False,
            )
            .sign(private_key, hashes.SHA256())
        )

        # Save certificate and key
        cert_file = certs_dir / "server.crt"
        key_file = certs_dir / "server.key"

        with open(cert_file, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))

        with open(key_file, "wb") as f:
            f.write(
                private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption(),
                )
            )

        self.logger.info(
            f"Generated self-signed certificate for " f"{domain or 'localhost'}"
        )

        return {
            "cert_file": str(cert_file),
            "key_file": str(key_file),
        }
