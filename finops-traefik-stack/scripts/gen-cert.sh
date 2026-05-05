#!/usr/bin/env bash
set -euo pipefail

CERT_DIR="traefik/dynamic/certs"
mkdir -p "${CERT_DIR}"

# Para domínios .dev, o navegador exige certificado confiável (HSTS).
# Se mkcert estiver disponível, gera certificado assinado por CA local.
if command -v mkcert >/dev/null 2>&1; then
  mkcert -cert-file "${CERT_DIR}/local.crt" -key-file "${CERT_DIR}/local.key" \
    localhost 127.0.0.1 ::1 \
    finops.local-dev traefik.local-dev pgadmin.local-dev portainer.local-dev \
    finops.local traefik.local pgadmin.local portainer.local
else
  SAN_LIST="DNS:localhost,DNS:*.localhost,DNS:finops.local-dev,DNS:traefik.local-dev,DNS:pgadmin.local-dev,DNS:portainer.local-dev,DNS:finops.local,DNS:traefik.local,DNS:pgadmin.local,DNS:portainer.local"
  openssl req -x509 -newkey rsa:2048 -sha256 -days 3650 -nodes \
    -keyout "${CERT_DIR}/local.key" \
    -out "${CERT_DIR}/local.crt" \
    -subj "/CN=localhost" \
    -addext "subjectAltName=${SAN_LIST}"
fi

# Traefik roda como usuario nao-root na imagem oficial, portanto precisa ler os arquivos.
chmod 644 "${CERT_DIR}/local.crt" "${CERT_DIR}/local.key"

echo "✅ Certificado gerado em ${CERT_DIR}/local.crt e ${CERT_DIR}/local.key"
echo "⚠️  Seu navegador pode alertar por ser self-signed."
