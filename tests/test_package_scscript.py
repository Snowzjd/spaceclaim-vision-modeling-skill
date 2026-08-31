from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "spaceclaim-vision-modeling" / "scripts" / "package_scscript.py"
SPEC = importlib.util.spec_from_file_location("package_scscript", MODULE_PATH)
assert SPEC and SPEC.loader
PACKAGER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PACKAGER)


SOURCE = "# Python Script, API Version = V21\nresult = 1\n"


class PackageScscriptTests(unittest.TestCase):
    def write_source(self, directory: str, name: str = "source.py") -> Path:
        path = Path(directory) / name
        path.write_text(SOURCE, encoding="utf-8", newline="")
        return path

    def test_minimal_members_content_and_fixed_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = self.write_source(directory)
            output = Path(directory) / "case.scscript"
            returned = PACKAGER.package_scscript(source, output)
            self.assertEqual(output, returned)
            with zipfile.ZipFile(output) as archive:
                self.assertEqual(list(archive.namelist()), list(PACKAGER.MEMBER_ORDER))
                self.assertEqual(archive.read("_script"), SOURCE.encode("utf-8"))
                self.assertEqual(archive.read("_apiVersion"), b"21")
                self.assertEqual(archive.read("_smartVariableVersion"), b"2")
                self.assertEqual(archive.read("[Content_Types].xml"), PACKAGER.CONTENT_TYPES_XML)
                for info in archive.infolist():
                    self.assertEqual(info.date_time, PACKAGER.DETERMINISTIC_TIMESTAMP)
                    self.assertEqual(info.create_system, 0)
                    self.assertEqual(info.create_version, 45)
                    self.assertEqual(info.external_attr, 0)
                self.assertEqual(archive.getinfo("_script").compress_type, zipfile.ZIP_DEFLATED)
                self.assertEqual(archive.getinfo("_apiVersion").compress_type, zipfile.ZIP_DEFLATED)
                self.assertEqual(archive.getinfo("_smartVariableVersion").compress_type, zipfile.ZIP_STORED)
                self.assertEqual(archive.getinfo("[Content_Types].xml").compress_type, zipfile.ZIP_STORED)

    def test_identical_inputs_have_identical_archive_hash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = self.write_source(directory)
            first = Path(directory) / "first.scscript"
            second = Path(directory) / "second.scscript"
            PACKAGER.package_scscript(source, first)
            PACKAGER.package_scscript(source, second)
            self.assertEqual(
                hashlib.sha256(first.read_bytes()).hexdigest(),
                hashlib.sha256(second.read_bytes()).hexdigest(),
            )

    def test_existing_output_requires_force(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = self.write_source(directory)
            output = Path(directory) / "case.scscript"
            PACKAGER.package_scscript(source, output)
            original = output.read_bytes()
            with self.assertRaises(FileExistsError):
                PACKAGER.package_scscript(source, output)
            PACKAGER.package_scscript(source, output, force=True)
            self.assertEqual(original, output.read_bytes())

    def test_empty_or_whitespace_source_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "empty.py"
            output = Path(directory) / "case.scscript"
            source.write_text(" \n\t", encoding="utf-8")
            with self.assertRaises(ValueError):
                PACKAGER.package_scscript(source, output)
            self.assertFalse(output.exists())

    def test_non_digit_api_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = self.write_source(directory)
            output = Path(directory) / "case.scscript"
            with self.assertRaises(ValueError):
                PACKAGER.package_scscript(source, output, api_version="V21")
            self.assertFalse(output.exists())

    def test_same_source_and_output_path_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = self.write_source(directory, "same.scscript")
            with self.assertRaises(ValueError):
                PACKAGER.package_scscript(source, source, force=True)

    def test_cli_success_and_force_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = self.write_source(directory)
            output = Path(directory) / "cli.scscript"
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                self.assertEqual(0, PACKAGER.main([str(source), str(output)]))
            self.assertEqual(str(output), stdout.getvalue().strip())
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                self.assertEqual(2, PACKAGER.main([str(source), str(output)]))
            self.assertIn("refusing to overwrite", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
