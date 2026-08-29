from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
import warnings
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "spaceclaim-vision-modeling" / "scripts" / "audit_scscript.py"
SPEC = importlib.util.spec_from_file_location("audit_scscript", MODULE_PATH)
assert SPEC and SPEC.loader
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


def write_archive(
    path: Path,
    script: str,
    user_objects: bytes = b"",
    *,
    script_encoding: str = "utf-8",
    omit_members: tuple[str, ...] = (),
) -> None:
    members = {
        "_script": script.encode(script_encoding),
        "_apiVersion": b"21",
        "_smartVariableVersion": b"1",
        "_userScriptObjects": user_objects,
    }
    with zipfile.ZipFile(path, "w") as archive:
        for name, data in members.items():
            if name not in omit_members:
                archive.writestr(name, data)


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

    def test_comments_and_strings_do_not_satisfy_operation_gate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "comments.scscript"
            write_archive(
                archive,
                '# Combine.Merge(selection)\nmessage = "Combine.Merge Face12"\n',
            )
            report = AUDIT.audit_archive(
                archive,
                required_operations=("Combine.Merge",),
            )
            self.assertEqual("failed", report["status"])
            self.assertEqual([], report["numbered_aliases"])
            self.assertEqual({}, report["operation_counts"])

    def test_similar_operation_name_is_not_an_exact_match(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "similar.scscript"
            write_archive(archive, "result = Combine.MergeExtra(selection)\n")
            report = AUDIT.audit_archive(
                archive,
                required_operations=("Combine.Merge",),
            )
            self.assertEqual("failed", report["status"])
            self.assertEqual(1, report["operation_counts"]["Combine.MergeExtra"])

    def test_forbidden_operation_ignores_similar_name(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "similar-allowed.scscript"
            write_archive(archive, "result = Combine.MergeExtra(selection)\n")
            report = AUDIT.audit_archive(
                archive,
                forbidden_operations=("Combine.Merge",),
            )
            self.assertEqual("passed", report["status"])

    def test_missing_core_member_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "missing-member.scscript"
            write_archive(archive, "pass\n", omit_members=("_apiVersion",))
            report = AUDIT.audit_archive(archive)
            self.assertEqual("failed", report["status"])
            self.assertIn("missing_member", [issue["code"] for issue in report["issues"]])

    def test_duplicate_member_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "duplicate.scscript"
            write_archive(archive, "pass\n")
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                with zipfile.ZipFile(archive, "a") as package:
                    package.writestr("_apiVersion", b"21")
            report = AUDIT.audit_archive(archive)
            self.assertEqual("failed", report["status"])
            self.assertIn("duplicate_members", [issue["code"] for issue in report["issues"]])

    def test_utf16_script_is_decoded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "utf16.scscript"
            write_archive(
                archive,
                "result = Combine.Merge(selection)\n",
                script_encoding="utf-16",
            )
            report = AUDIT.audit_archive(
                archive,
                required_operations=("Combine.Merge",),
            )
            self.assertEqual("passed", report["status"])
            self.assertEqual(1, report["operation_counts"]["Combine.Merge"])

    def test_bomless_utf16le_script_is_decoded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "utf16le.scscript"
            write_archive(
                archive,
                "result = Combine.Merge(selection)\n",
                script_encoding="utf-16-le",
            )
            report = AUDIT.audit_archive(
                archive,
                required_operations=("Combine.Merge",),
            )
            self.assertEqual("passed", report["status"])

    def test_windows_backslash_path_warns_without_failing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "path.scscript"
            write_archive(archive, 'output = "C:\\work\\model.scdoc"\n')
            report = AUDIT.audit_archive(archive)
            self.assertEqual("passed", report["status"])
            self.assertIn("backslash_path_literals", [issue["code"] for issue in report["issues"]])

    def test_cli_writes_json_report_and_returns_status_code(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "cli.scscript"
            report_path = Path(directory) / "reports" / "audit.json"
            write_archive(archive, "result = Combine.Merge(selection)\n")
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = AUDIT.main(
                    [
                        str(archive),
                        "--require-api",
                        "21",
                        "--require-operation",
                        "Combine.Merge",
                        "--report",
                        str(report_path),
                    ]
                )
            self.assertEqual(0, exit_code)
            self.assertEqual("passed", json.loads(stdout.getvalue())["status"])
            self.assertEqual("passed", json.loads(report_path.read_text(encoding="utf-8"))["status"])

    def test_invalid_archive_fails_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "invalid.scscript"
            archive.write_text("not a zip", encoding="utf-8")
            report = AUDIT.audit_archive(archive)
            self.assertEqual("failed", report["status"])
            self.assertEqual("invalid_archive", report["issues"][0]["code"])


if __name__ == "__main__":
    unittest.main()
