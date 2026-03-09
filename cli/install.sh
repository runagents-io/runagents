#!/usr/bin/env sh
# RunAgents CLI install script
# Usage: curl -fsSL https://raw.githubusercontent.com/stylesync01/runagents/main/cli/install.sh | sh

set -eu

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
VERSION=$(curl -fsSL "$S3_BASE/latest/checksums.txt" | head -1 | grep -o 'v[0-9][0-9.]*' | head -1 || true)
if [ -z "$VERSION" ]; then
  echo "Failed to resolve latest RunAgents version from $S3_BASE/latest/checksums.txt"
  exit 1
fi

echo "Installing runagents ${VERSION} for ${OS}/${ARCH}..."

ASSET="runagents_${OS}_${ARCH}.tar.gz"
URL="${S3_BASE}/${VERSION}/${ASSET}"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT INT TERM

calc_sha256() {
  file="$1"
  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$file" | awk '{print $1}'
    return 0
  fi
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$file" | awk '{print $1}'
    return 0
  fi
  echo "Missing checksum utility: install shasum or sha256sum"
  return 1
}

curl -fsSL "$URL" -o "$TMP/$ASSET"
curl -fsSL "${S3_BASE}/${VERSION}/checksums.txt" -o "$TMP/checksums.txt"

EXPECTED_CHECKSUM=$(awk -v asset="$ASSET" '$2 == asset || $2 == "*" asset || $2 == "./" asset { print $1; exit }' "$TMP/checksums.txt")
if [ -z "$EXPECTED_CHECKSUM" ]; then
  echo "Failed to find checksum for $ASSET in checksums.txt"
  exit 1
fi
ACTUAL_CHECKSUM=$(calc_sha256 "$TMP/$ASSET")
if [ "$EXPECTED_CHECKSUM" != "$ACTUAL_CHECKSUM" ]; then
  echo "Checksum verification failed for $ASSET"
  echo "Expected: $EXPECTED_CHECKSUM"
  echo "Actual:   $ACTUAL_CHECKSUM"
  exit 1
fi

tar -xzf "$TMP/$ASSET" -C "$TMP" runagents
rm "$TMP/$ASSET"

if [ -w "$INSTALL_DIR" ]; then
  mv "$TMP/runagents" "$INSTALL_DIR/runagents"
  chmod +x "$INSTALL_DIR/runagents"
else
  sudo mv "$TMP/runagents" "$INSTALL_DIR/runagents"
  sudo chmod +x "$INSTALL_DIR/runagents"
fi

echo "runagents ${VERSION} installed to $INSTALL_DIR/runagents"
$INSTALL_DIR/runagents version
