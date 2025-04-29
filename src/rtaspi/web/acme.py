"""ACME client for Let's Encrypt certificate management."""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta

from acme import client, messages
from acme.client import ClientV2
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from josepy import JWKRSA
from aiohttp import web


class ACMEClient:
    """ACME client for Let's Encrypt certificate management."""

    LETS_ENCRYPT_DIRECTORY_URL = {
        True: "https://acme-staging-v02.api.letsencrypt.org/directory",
        False: "https://acme-v02.api.letsencrypt.org/directory",
    }

    def __init__(
        self,
        domain: str,
        email: str,
        staging: bool = True,
        storage_dir: Optional[str] = None,
    ):
        """Initialize ACME client.

        Args:
            domain: Domain name for the certificate
            email: Contact email for Let's Encrypt
            staging: Whether to use staging environment
            storage_dir: Directory to store certificates and account info
        """
        self.logger = logging.getLogger(__name__)
        self.domain = domain
        self.email = email
        self.staging = staging
        self.storage_dir = Path(storage_dir or "certs")
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.account_key: Optional[JWKRSA] = None
        self.client: Optional[ClientV2] = None
        self.http_challenge = None
        self._http_challenge_resource = None

    async def initialize(self) -> None:
        """Initialize ACME client and account."""
        # Load or create account key
        account_key_path = self.storage_dir / "account.key"
        if account_key_path.exists():
            with open(account_key_path, "rb") as f:
                key_data = f.read()
            private_key = serialization.load_pem_private_key(key_data, password=None)
        else:
            private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            with open(account_key_path, "wb") as f:
                f.write(
                    private_key.private_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PrivateFormat.PKCS8,
                        encryption_algorithm=serialization.NoEncryption(),
                    )
                )

        # Create ACME client
        self.account_key = JWKRSA(key=private_key)
        net = client.ClientNetwork(self.account_key)
        directory = messages.Directory.from_url(
            self.LETS_ENCRYPT_DIRECTORY_URL[self.staging]
        )
        self.client = ClientV2(directory, net=net)

        # Register account if needed
        await self._register_account()

    async def _register_account(self) -> None:
        """Register ACME account if not already registered."""
        account_path = self.storage_dir / "account.json"
        if account_path.exists():
            return

        registration = await self.client.new_account(
            messages.NewRegistration.from_data(
                email=self.email, terms_of_service_agreed=True
            )
        )

        with open(account_path, "w") as f:
            json.dump({"uri": registration.uri, "email": self.email}, f)

    async def obtain_certificate(self) -> Dict[str, str]:
        """Obtain new certificate using HTTP challenge.

        Returns:
            Dictionary containing paths to certificate files
        """
        # Create domain private key
        domain_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

        # Create certificate signing request
        csr = (
            x509.CertificateSigningRequestBuilder()
            .subject_name(
                x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, self.domain)])
            )
            .add_extension(
                x509.SubjectAlternativeName([x509.DNSName(self.domain)]),
                critical=False,
            )
            .sign(domain_key, hashes.SHA256())
        )

        # Request certificate issuance
        order = await self.client.new_order(
            csr.public_bytes(serialization.Encoding.DER)
        )

        # Get HTTP challenge
        authorizations = await self.client.poll_authorizations(order)
        challenge = None
        for authz in authorizations:
            for c in authz.body.challenges:
                if isinstance(c.chall, messages.HTTP01):
                    challenge = c
                    break
            if challenge:
                break

        if not challenge:
            raise ValueError("No HTTP challenge found")

        # Get challenge data
        response, validation = challenge.response_and_validation(self.account_key)
        self._http_challenge_resource = validation

        try:
            # Notify Let's Encrypt we're ready
            await self.client.answer_challenge(challenge, response)

            # Wait for certificate issuance
            order = await self.client.poll_and_finalize(order)

            # Save certificate and key
            cert_path = self.storage_dir / "server.crt"
            key_path = self.storage_dir / "server.key"

            with open(cert_path, "wb") as f:
                f.write(order.fullchain_pem.encode())

            with open(key_path, "wb") as f:
                f.write(
                    domain_key.private_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PrivateFormat.PKCS8,
                        encryption_algorithm=serialization.NoEncryption(),
                    )
                )

            return {"cert_file": str(cert_path), "key_file": str(key_path)}

        finally:
            # Clear challenge
            self._http_challenge_resource = None

    def get_challenge_response(self) -> Optional[str]:
        """Get current HTTP challenge response.

        Returns:
            Challenge response text if challenge is active
        """
        return self._http_challenge_resource

    async def check_certificate(self) -> bool:
        """Check if certificate needs renewal.

        Returns:
            True if certificate needs renewal
        """
        cert_path = self.storage_dir / "server.crt"
        if not cert_path.exists():
            return True

        with open(cert_path, "rb") as f:
            cert_data = f.read()

        cert = x509.load_pem_x509_certificate(cert_data)
        expiry = cert.not_valid_after

        # Renew if less than 30 days until expiry
        return datetime.utcnow() + timedelta(days=30) > expiry


async def challenge_handler(request: web.Request) -> web.Response:
    """Handle ACME HTTP challenge requests."""
    app = request.app
    acme_client = app.get("acme_client")
    if not acme_client:
        return web.Response(status=404)

    challenge = acme_client.get_challenge_response()
    if not challenge:
        return web.Response(status=404)

    return web.Response(text=challenge)
