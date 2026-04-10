"""Go CLI binary downloader — mirrors cli/npm/install.js logic.

Downloads from S3, verifies SHA256, caches at ~/.runagents/bin/.
Stdlib only: urllib.request, tarfile, hashlib, platform.
"""

import hashlib
import os
import platform
import shutil
import stat
import sys
import tarfile
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

CLI_VERSION = "1.3.1"
S3_BASE = "https://runagents-releases.s3.amazonaws.com/cli"

PLATFORM_MAP = {"Darwin": "darwin", "Linux": "linux", "Windows": "windows"}
ARCH_MAP = {"x86_64": "amd64", "AMD64": "amd64", "arm64": "arm64", "aarch64": "arm64"}

_BIN_DIR = Path.home() / ".runagents" / "bin"


def ensure_binary(version: str = CLI_VERSION) -> Path | None:
    """Return path to Go binary, downloading if needed. Returns None on failure."""
    # 1. Check cached binary
    cached = _BIN_DIR / f"runagents-{version}"
    if cached.exists() and os.access(cached, os.X_OK):
        return cached

    # 2. Check PATH
    on_path = shutil.which("runagents")
    if on_path:
        return Path(on_path)

    # 3. Download
    try:
        return _download(version)
    except Exception as e:
        print(f"Warning: could not download CLI binary: {e}", file=sys.stderr)
        return None


def _download(version: str) -> Path:
    plat = PLATFORM_MAP.get(platform.system())
    arch = ARCH_MAP.get(platform.machine())
    if not plat or not arch:
        raise RuntimeError(f"Unsupported platform: {platform.system()}/{platform.machine()}")

    ext = ".zip" if plat == "windows" else ".tar.gz"
    asset = f"runagents_{plat}_{arch}{ext}"
    url = f"{S3_BASE}/v{version}/{asset}"
    checksums_url = f"{S3_BASE}/v{version}/checksums.txt"

    _BIN_DIR.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        archive_path = Path(tmpdir) / asset

        # Download archive
        print(f"Downloading runagents v{version} for {plat}/{arch}...")
        urllib.request.urlretrieve(url, archive_path)

        # Verify checksum
        try:
            with urllib.request.urlopen(checksums_url, timeout=10) as resp:
                checksums_text = resp.read().decode()
            expected_hash = _find_hash(checksums_text, asset)
            if expected_hash:
                actual_hash = _sha256(archive_path)
                if actual_hash != expected_hash:
                    raise RuntimeError(
                        f"SHA256 mismatch for {asset}: expected {expected_hash}, got {actual_hash}"
                    )
        except urllib.error.URLError:
            pass  # Skip verification if checksums unavailable

        # Extract
        bin_name = "runagents.exe" if plat == "windows" else "runagents"
        if ext == ".tar.gz":
            with tarfile.open(archive_path, "r:gz") as tar:
                # Find the binary in the archive
                for member in tar.getmembers():
                    if member.name.endswith(bin_name):
                        member.name = bin_name
                        tar.extract(member, tmpdir)
                        break
        else:
            import zipfile
            with zipfile.ZipFile(archive_path) as zf:
                for name in zf.namelist():
                    if name.endswith(bin_name):
                        zf.extract(name, tmpdir)
                        break

        src = Path(tmpdir) / bin_name
        dst = _BIN_DIR / f"runagents-{version}"
        shutil.move(str(src), str(dst))
        dst.chmod(dst.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        print(f"Installed runagents v{version} to {dst}")
        return dst


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _find_hash(checksums_text: str, asset_name: str) -> str | None:
    for line in checksums_text.strip().splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1] == asset_name:
            return parts[0]
    return None
