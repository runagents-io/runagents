"""Tests for Python CLI binary resolution."""

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from runagents.cli import binary


class TestEnsureBinary(unittest.TestCase):
    def test_prefers_cached_binary(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            cache_dir.mkdir()
            cached = cache_dir / "runagents-1.4.0"
            cached.write_text("binary")
            cached.chmod(0o755)

            with mock.patch.object(binary, "_BIN_DIR", cache_dir):
                with mock.patch("runagents.cli.binary.shutil.which") as mock_which:
                    result = binary.ensure_binary("1.4.0")

            self.assertEqual(result, cached)
            mock_which.assert_not_called()

    def test_uses_path_binary_when_different_from_wrapper(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            path_binary = Path(tmpdir) / "runagents-real"
            path_binary.write_text("binary")
            path_binary.chmod(0o755)

            with mock.patch.object(binary, "_BIN_DIR", cache_dir):
                with mock.patch("runagents.cli.binary.shutil.which", return_value=str(path_binary)):
                    with mock.patch("runagents.cli.binary.sys.argv", [str(Path(tmpdir) / "runagents")]):
                        result = binary.ensure_binary("1.4.0")

            self.assertEqual(result, path_binary)

    def test_ignores_wrapper_on_path_and_downloads_native_binary(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            wrapper = Path(tmpdir) / "runagents"
            wrapper.write_text("#!/usr/bin/env python3\n")
            wrapper.chmod(0o755)
            downloaded = Path(tmpdir) / "runagents-native"
            downloaded.write_text("binary")
            downloaded.chmod(0o755)

            with mock.patch.object(binary, "_BIN_DIR", cache_dir):
                with mock.patch("runagents.cli.binary.shutil.which", return_value=str(wrapper)):
                    with mock.patch("runagents.cli.binary.sys.argv", [str(wrapper)]):
                        with mock.patch("runagents.cli.binary._download", return_value=downloaded) as mock_download:
                            result = binary.ensure_binary("1.4.0")

            self.assertEqual(result, downloaded)
            mock_download.assert_called_once_with("1.4.0")


if __name__ == "__main__":
    unittest.main()
