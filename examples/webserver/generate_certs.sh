#!/bin/bash

# Create certs directory if it doesn't exist
mkdir -p certs

# Generate private key and self-signed certificate
openssl req -x509 -newkey rsa:4096 -keyout certs/server.key -out certs/server.crt -days 365 -nodes -subj "/CN=localhost"

# Set appropriate permissions
chmod 600 certs/server.key
chmod 644 certs/server.crt

echo "SSL certificates generated successfully in certs/ directory"
echo "Note: These are self-signed certificates for development purposes only"
