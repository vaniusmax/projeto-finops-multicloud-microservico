#!/usr/bin/env bash
set -euo pipefail

ARCH="$(uname -m)"
case "${ARCH}" in
  x86_64|amd64)
    AWS_ARCH="x86_64"
    ;;
  aarch64|arm64)
    AWS_ARCH="aarch64"
    ;;
  *)
    echo "Arquitetura nao suportada para instalacao automatica do AWS CLI: ${ARCH}" >&2
    exit 1
    ;;
esac

echo "[1/4] Instalando dependencias base..."
sudo apt-get update
sudo apt-get install -y \
  ca-certificates \
  curl \
  gnupg \
  groff \
  less \
  lsb-release \
  python3 \
  python3-venv \
  unzip

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TMP_DIR}"' EXIT

echo "[2/4] Instalando AWS CLI v2 (latest)..."
curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-${AWS_ARCH}.zip" -o "${TMP_DIR}/awscliv2.zip"
unzip -q "${TMP_DIR}/awscliv2.zip" -d "${TMP_DIR}"
sudo "${TMP_DIR}/aws/install" --update

echo "[3/4] Instalando Azure CLI (latest)..."
curl -fsSL https://aka.ms/InstallAzureCLIDeb | sudo bash

echo "[4/4] Instalando OCI CLI (latest)..."
bash -c "$(curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)" -- \
  --accept-all-defaults \
  --exec-dir "${HOME}/bin" \
  --install-dir "${HOME}/lib/oracle-cli"

if ! grep -q 'export PATH="$HOME/bin:$PATH"' "${HOME}/.profile" 2>/dev/null; then
  echo 'export PATH="$HOME/bin:$PATH"' >> "${HOME}/.profile"
fi
export PATH="${HOME}/bin:${PATH}"

echo
echo "Versoes instaladas:"
aws --version
az version --query '"azure-cli"' -o tsv
oci --version

echo
echo "Instalacao concluida."
