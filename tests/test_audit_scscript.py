from __future__ import annotations

import importlib.util
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "spaceclaim-vision-modeling" / "scripts" / "audit_scscript.py"
SPEC = importlib.util.spec_from_file_location("audit_scscript", MODULE_PATH)
assert SPEC and SPEC.loader
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


def write_archive(path: Path, script: str, user_objects: bytes = b"") -> None:
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("_script", script.encode("utf-8"))
        archive.writestr("_apiVersion", b"21")
        archive.writestr("_smartVariableVersion", b"1")
        archive.writestr("_userScriptObjects", user_objects)


class AuditScscriptTests(unittest.TestCase):
    def test_semantic_script_passes_required_operation_gate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "good.scscript"
            write_archive(archive, "result = Combine.Merge(selection)\n")
            report = AUDIT.audit_archive(
                archive,
                require_api="21",
                required_operations=("Combine.Merge",),
            )
            self.assertEqual("passed", report["status"])
            self.assertEqual([], report["numbered_aliases"])

    def test_alias_closure_is_checked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "missing-object.scscript"
            write_archive(archive, "selection = Face12\n")
            report = AUDIT.audit_archive(archive)
            self.assertEqual("failed", report["status"])
            self.assertIn(
                "smart_variable_closure_missing",
                [issue["code"] for issue in report["issues"]],
            )

    def test_numbered_aliases_can_be_forbidden(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "alias.scscript"
            write_archive(archive, "selection = Body7\n", b"Body7")
            report = AUDIT.audit_archive(archive, forbid_numbered_aliases=True)
            self.assertEqual("failed", report["status"])
            self.assertIn("topology_sensitive_aliases", [i["code"] for i in report["issues"]])

    def test_forbidden_operation_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "forbidden.scscript"
            write_archive(archive, "VolumeExtract.Create(primary, secondary, seed)\n")
            report = AUDIT.audit_archive(
                archive, forbidden_operations=("VolumeExtract.Create",)
            )
            self.assertEqual("failed", report["status"])

    def test_invalid_archive_fails_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "invalid.scscript"
            archive.write_text("not a zip", encoding="utf-8")
            report = AUDIT.audit_archive(archive)
            self.assertEqual("failed", report["status"])
            self.assertEqual("invalid_archive", report["issues"][0]["code"])


if __name__ == "__main__":
    unittest.main()
