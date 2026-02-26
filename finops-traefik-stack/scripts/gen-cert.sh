#!/usr/bin/env bash
set -euo pipefail

CERT_DIR="traefik/dynamic/certs"
mkdir -p "${CERT_DIR}"

openssl req -x509 -newkey rsa:2048 -sha256 -days 3650 -nodes   -keyout "${CERT_DIR}/local.key"   -out "${CERT_DIR}/local.crt"   -subj "/CN=localhost"   -addext "subjectAltName=DNS:localhost,DNS:*.localhost"

echo "✅ Certificado gerado em ${CERT_DIR}/local.crt e ${CERT_DIR}/local.key"
echo "⚠️  Seu navegador pode alertar por ser self-signed."
