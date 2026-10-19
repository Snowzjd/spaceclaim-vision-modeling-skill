from __future__ import annotations

import ast
import hashlib
import importlib.util
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HARNESS = (
    ROOT
    / "spaceclaim-vision-modeling"
    / "assets"
    / "evaluations"
    / "p3-actions"
    / "import-test.py"
)
SCRIPTS = ROOT / "spaceclaim-vision-modeling" / "scripts"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PACKAGER = _load_module("atomic_import_packager", SCRIPTS / "package_scscript.py")
AUDITOR = _load_module("atomic_import_auditor", SCRIPTS / "audit_scscript.py")
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
BUILDER = _load_module("atomic_import_builder", SCRIPTS / "build_atomic_suite.py")


class AtomicImportHostPrepTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = HARNESS.read_text(encoding="utf-8")

    def test_harness_is_ast_parseable_and_uses_host_injected_fixture_data(self) -> None:
        ast.parse(self.source, filename=str(HARNESS))
        for marker in (
            "ACTION_DIR",
            "REPORT",
            "IMPORT_SOURCE",
            "IMPORT_SHA256",
            "IMPORT_EXPECTED_BODY_SIGNATURES",
            "MA-35",
            "Component",
            "GetRootPart",
            "hashlib.sha256",
        ):
            self.assertIn(marker, self.source)
        self.assertNotIn("source.scdoc", self.source)
        self.assertNotIn("e779ad946f30b2f2e6d2d20b8b45b622af64de3fdac39289768bef520cd61e7c", self.source)
        self.assertNotIn("Document.Open", self.source)
        self.assertNotIn("DocumentSave.Execute", self.source)
        self.assertNotRegex(self.source, r"(?i)[A-Za-z]:[/\\]")

    def test_host_injected_build_packages_and_passes_static_audit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture = root / "caller-fixture.scdoc"
            fixture.write_bytes(b"caller-supplied native fixture")
            digest = hashlib.sha256(fixture.read_bytes()).hexdigest()
            prefix = (
                "# Python Script, API Version = V21\n"
                "ACTION_DIR = r'C:/run-owned/actions'\n"
                "REPORT = r'C:/run-owned/import-report.json'\n"
                "IMPORT_SOURCE = %r\n"
                "IMPORT_SHA256 = %r\n"
                "IMPORT_EXPECTED_BODY_SIGNATURES = %r\n"
                "IMPORT_BBOX_TOLERANCE_MM = 0.001\n"
                "IMPORT_VOLUME_TOLERANCE_MM3 = 0.001\n"
            ) % (
                str(fixture),
                digest,
                [{"bbox_mm": [346.0, -4.0, 0.0, 354.0, 4.0, 12.0], "volume_mm3": 448.0}],
            )
            assembled = prefix + self.source
            assembled_path = root / "import-test.py"
            archive_path = root / "import-test.scscript"
            assembled_path.write_text(assembled, encoding="utf-8", newline="\n")
            ast.parse(assembled, filename=str(assembled_path))
            PACKAGER.package_scscript(assembled_path, archive_path, api_version="21")
            result = AUDITOR.audit_archive(
                archive_path,
                require_api="21",
                forbid_numbered_aliases=True,
                forbidden_operations=("Document.Open", "DocumentSave.Execute"),
            )
            self.assertEqual("passed", result["status"], result["issues"])
            self.assertEqual([], result["numbered_aliases"])
            with zipfile.ZipFile(archive_path) as archive:
                self.assertEqual(assembled.encode("utf-8"), archive.read("_script"))
                self.assertEqual(b"21", archive.read("_apiVersion"))

    def test_builder_import_mode_injects_config_and_packages_v21_archive(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture = root / "caller-fixture.scdoc"
            fixture.write_bytes(b"caller-supplied native fixture")
            digest = hashlib.sha256(fixture.read_bytes()).hexdigest()
            config = {
                "source": fixture,
                "sha256": digest.upper(),
                "expected_body_signatures": [
                    {
                        "bbox_mm": [346, -4, 0, 354, 4, 12],
                        "volume_mm3": 448,
                    }
                ],
                "bbox_tolerance_mm": 0.001,
                "volume_tolerance_mm3": 0.001,
            }
            output = root / "suite-import"
            archive_path = BUILDER.build(output, suite="import", import_config=config)
            generated = (output / "forward.py").read_text(encoding="utf-8")
            self.assertIn("IMPORT_SOURCE = %r" % str(fixture.resolve()), generated)
            self.assertIn("IMPORT_SHA256 = %r" % digest, generated)
            self.assertIn(
                "IMPORT_EXPECTED_BODY_SIGNATURES = %r"
                % [{"bbox_mm": [346.0, -4.0, 0.0, 354.0, 4.0, 12.0], "volume_mm3": 448.0}],
                generated,
            )
            self.assertEqual((output / "forward.scscript").resolve(), archive_path)
            result = AUDITOR.audit_archive(
                archive_path,
                require_api="21",
                forbid_numbered_aliases=True,
                forbidden_operations=("Document.Open", "DocumentSave.Execute"),
            )
            self.assertEqual("passed", result["status"], result["issues"])
            self.assertEqual([], result["numbered_aliases"])
            with zipfile.ZipFile(archive_path) as archive:
                self.assertEqual(generated.encode("utf-8"), archive.read("_script"))
                self.assertEqual(b"21", archive.read("_apiVersion"))
            self.assertTrue((output / "actions" / "ma-35.scscript").is_file())

    def test_import_builder_preserves_existing_output_refusal_and_legacy_api(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture = root / "caller-fixture.scdoc"
            fixture.write_bytes(b"caller-supplied native fixture")
            config = {
                "source": fixture,
                "sha256": hashlib.sha256(fixture.read_bytes()).hexdigest(),
                "expected_body_signatures": [
                    {"bbox_mm": [0, 0, 0, 1, 1, 1], "volume_mm3": 1}
                ],
            }
            output = root / "suite-import"
            BUILDER.build(output, "import", config)
            with self.assertRaises(FileExistsError):
                BUILDER.build(output, "import", config)

            # The pre-existing two-argument call remains valid for non-import
            # suites and still emits the historical forward artifact names.
            legacy = root / "suite-forward"
            legacy_archive = BUILDER.build(legacy, "forward")
            self.assertEqual((legacy / "forward.scscript").resolve(), legacy_archive)
            self.assertTrue((legacy / "forward.py").is_file())


if __name__ == "__main__":
    unittest.main()
