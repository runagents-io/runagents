#!/usr/bin/env sh
# RunAgents CLI install script
# Usage: curl -fsSL https://raw.githubusercontent.com/runagents-io/runagents/main/cli/install.sh | sh

set -e

S3_BASE="https://runagents-releases.s3.amazonaws.com/cli"
INSTALL_DIR="${INSTALL_DIR:-/usr/local/bin}"

OS=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)
case "$ARCH" in
  x86_64)        ARCH="amd64" ;;
  aarch64|arm64) ARCH="arm64" ;;
  *) echo "Unsupported architecture: $ARCH" && exit 1 ;;
esac
case "$OS" in
  darwin|linux) ;;
  *) echo "Unsupported OS: $OS" && exit 1 ;;
esac

# Get latest version from S3 manifest
VERSION=$(curl -fsSL "$S3_BASE/latest/checksums.txt" | head -1 | grep -o 'v[0-9][0-9.]*' | head -1)
if [ -z "$VERSION" ]; then
  # Fallback: hardcoded latest
  VERSION="v1.0.0"
fi

echo "Installing runagents ${VERSION} for ${OS}/${ARCH}..."

ASSET="runagents_${OS}_${ARCH}.tar.gz"
URL="${S3_BASE}/${VERSION}/${ASSET}"
TMP=$(mktemp -d)

curl -fsSL "$URL" -o "$TMP/$ASSET"
tar -xzf "$TMP/$ASSET" -C "$TMP" runagents
rm "$TMP/$ASSET"

if [ -w "$INSTALL_DIR" ]; then
  mv "$TMP/runagents" "$INSTALL_DIR/runagents"
  chmod +x "$INSTALL_DIR/runagents"
else
  sudo mv "$TMP/runagents" "$INSTALL_DIR/runagents"
  sudo chmod +x "$INSTALL_DIR/runagents"
fi

rm -rf "$TMP"
echo "runagents ${VERSION} installed to $INSTALL_DIR/runagents"
runagents --version
