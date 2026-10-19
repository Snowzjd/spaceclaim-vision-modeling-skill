from __future__ import annotations

import hashlib
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "spaceclaim-vision-modeling" / "scripts" / "execution_host_actions.py"
SPEC = importlib.util.spec_from_file_location("execution_host_actions", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ExecutionHostActionTests(unittest.TestCase):
    def test_dispatch_accepts_catalog_id_and_operation_name(self) -> None:
        result = MODULE.dispatch(
            "confirm_control_authorization",
            authorization={"authorized": True, "scope": "run"},
            task_scope="run",
        )
        self.assertEqual("EX-01", result["action_id"])
        self.assertTrue(result["authorization_structure_valid"])
        self.assertFalse(result["self_authorization"])
        with self.assertRaises(MODULE.HostActionError):
            MODULE.dispatch("EX-99", {})

    def test_ex05_copies_new_path_and_preserves_hash_verified_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            baseline = root / "baseline.scdoc"
            copy = root / "run" / "baseline-copy.scdoc"
            copy.parent.mkdir()
            payload = b"baseline payload\x00"
            baseline.write_bytes(payload)
            digest = hashlib.sha256(payload).hexdigest()

            result = MODULE.copy_baseline_model(
                baseline,
                copy,
                expected_sha256=digest.upper(),
                run_ref="run-05",
            )

            self.assertEqual("EX-05", result["action_id"])
            self.assertEqual(digest, result["baseline_sha256"])
            self.assertEqual(digest, result["copy_sha256"])
            self.assertTrue(result["source_preserved"])
            self.assertEqual(payload, baseline.read_bytes())
            self.assertEqual(payload, copy.read_bytes())

    def test_ex05_rejects_hash_mismatch_and_existing_destination(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            baseline = root / "baseline.scdoc"
            baseline.write_bytes(b"unchanged")
            expected = hashlib.sha256(baseline.read_bytes()).hexdigest()
            existing = root / "existing.scdoc"
            existing.write_bytes(b"do not replace")
            with self.assertRaisesRegex(MODULE.HostActionError, "hash"):
                MODULE.copy_baseline_model(baseline, root / "bad.scdoc", "0" * 64)
            self.assertFalse((root / "bad.scdoc").exists())
            with self.assertRaisesRegex(MODULE.HostActionError, "run_ref"):
                MODULE.copy_baseline_model(baseline, root / "missing-ref.scdoc", expected, run_ref="")
            self.assertFalse((root / "missing-ref.scdoc").exists())
            with self.assertRaisesRegex(MODULE.HostActionError, "new path"):
                MODULE.copy_baseline_model(baseline, existing, expected)
            self.assertEqual(b"do not replace", existing.read_bytes())

    def test_ex07_accepts_distinct_run_owned_outputs_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "run"
            root.mkdir()
            outputs = {
                "model": root / "model.scdoc",
                "report": root / "report.json",
            }
            result = MODULE.verify_run_output_path(outputs, root, run_ref="run-07")
            self.assertEqual("EX-07", result["action_id"])
            self.assertEqual({"model", "report"}, {item["role"] for item in result["outputs"]})
            self.assertFalse((root / "model.scdoc").exists())

    def test_ex07_rejects_role_path_reserved_and_outside_collisions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "run"
            root.mkdir()
            baseline = root / "baseline.scdoc"
            evidence = root / "evidence.json"
            baseline.write_bytes(b"baseline")
            evidence.write_bytes(b"evidence")

            with self.assertRaisesRegex(MODULE.HostActionError, "role collision"):
                MODULE.verify_run_output_path(
                    [{"role": "same", "path": root / "a"}, {"role": "same", "path": root / "b"}],
                    root,
                )
            with self.assertRaisesRegex(MODULE.HostActionError, "baseline/evidence"):
                MODULE.verify_run_output_path({"model": baseline}, root, baseline_path=baseline)
            with self.assertRaisesRegex(MODULE.HostActionError, "baseline/evidence"):
                MODULE.verify_run_output_path({"report": evidence}, root, evidence_paths=[evidence])
            with self.assertRaisesRegex(MODULE.HostActionError, "inside run root"):
                MODULE.verify_run_output_path({"model": Path(directory) / "outside.scdoc"}, root)

            existing = root / "existing.json"
            existing.write_bytes(b"old")
            with self.assertRaises(MODULE.HostActionError):
                MODULE.verify_run_output_path({"report": existing}, root)
            allowed = MODULE.verify_run_output_path(
                [{"role": "report", "path": existing, "overwrite": True}],
                root,
                overwrite_policy="run_owned",
                owned_paths=[existing],
            )
            self.assertTrue(allowed["outputs"][0]["exists"])

    def test_ex07_rejects_symlink_path_when_platform_allows_symlink_creation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "run"
            root.mkdir()
            target = root / "target.json"
            link = root / "link.json"
            try:
                link.symlink_to(target)
            except (OSError, NotImplementedError) as exc:
                self.skipTest("symlink creation unavailable: %s" % exc)
            with self.assertRaisesRegex(MODULE.HostActionError, "symlink"):
                MODULE.verify_run_output_path({"report": link}, root)

    def _write_scscript(self, path: Path, api: bytes = b"21") -> str:
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("_script", b"# script")
            archive.writestr("_apiVersion", api)
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def test_ex11_records_exact_identity_without_claiming_execution_observation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            artifact = Path(directory) / "forward.scscript"
            digest = self._write_scscript(artifact)
            result = MODULE.record_executed_artifact_identity(
                artifact,
                digest.upper(),
                21,
                "run-11",
            )
            self.assertEqual("EX-11", result["action_id"])
            self.assertEqual(digest, result["artifact_sha256"])
            self.assertEqual("21", result["api_version"])
            self.assertTrue(result["identity_match"])
            self.assertFalse(result["execution_observed"])
            self.assertEqual("not_tested", result["runtime_observation"])

    def test_ex11_rejects_hash_api_extension_and_malformed_archive(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifact = root / "forward.scscript"
            digest = self._write_scscript(artifact)
            with self.assertRaisesRegex(MODULE.HostActionError, "hash"):
                MODULE.record_executed_artifact_identity(artifact, "0" * 64, 21, "run")
            with self.assertRaisesRegex(MODULE.HostActionError, "API"):
                MODULE.record_executed_artifact_identity(artifact, digest, 22, "run")
            bad_api = root / "bad-api.scscript"
            bad_digest = self._write_scscript(bad_api, b"V21")
            with self.assertRaises(MODULE.HostActionError):
                MODULE.record_executed_artifact_identity(bad_api, bad_digest, 21, "run")
            not_archive = root / "not-script.scscript"
            not_archive.write_bytes(b"not zip")
            with self.assertRaises(MODULE.HostActionError):
                MODULE.record_executed_artifact_identity(
                    not_archive,
                    hashlib.sha256(not_archive.read_bytes()).hexdigest(),
                    21,
                    "run",
                )

    def test_ex12_selects_earliest_ordered_failure_without_root_cause_substitution(self) -> None:
        events = [
            {"sequence": 3, "status": "failed", "id": "later", "root_cause": "later note"},
            {"sequence": 1, "status": "passed", "id": "setup"},
            {"sequence": 2, "status": "failed", "id": "first"},
        ]
        result = MODULE.capture_earliest_failure_state(events, run_ref="run-12")
        self.assertEqual("first", result["failure_event"]["id"])
        self.assertEqual("sequence", result["ordering_basis"])
        self.assertFalse(result["root_cause_inferred"])
        self.assertEqual("first", result["event"]["id"])

        timestamp_events = [
            {"timestamp": "2026-09-08T12:00:02Z", "status": "failed", "id": "second"},
            {"timestamp": "2026-09-08T12:00:01Z", "status": "failed", "id": "first"},
        ]
        timestamp_result = MODULE.capture_earliest_failure_state(timestamp_events)
        self.assertEqual("first", timestamp_result["failure_event"]["id"])
        self.assertEqual("timestamp", timestamp_result["ordering_basis"])

    def test_ex12_requires_a_failure_event(self) -> None:
        with self.assertRaisesRegex(MODULE.HostActionError, "no failed event"):
            MODULE.capture_earliest_failure_state([{"status": "passed"}])
        with self.assertRaisesRegex(MODULE.HostActionError, "complete comparable order"):
            MODULE.capture_earliest_failure_state(
                [{"status": "failed", "id": "a"}, {"status": "failed", "id": "b"}]
            )
        with self.assertRaisesRegex(MODULE.HostActionError, "run_ref"):
            MODULE.capture_earliest_failure_state(
                [
                    {"sequence": 1, "status": "failed", "run_ref": "run-a"},
                    {"sequence": 2, "status": "failed", "run_ref": "run-b"},
                ],
                run_ref="run-a",
            )

    def test_ex13_blocks_critical_save_callback_and_allows_noncritical_save(self) -> None:
        calls = []
        blocked = MODULE.block_save_after_critical_failure(
            {"status": "failed", "critical": True},
            lambda: calls.append("saved"),
        )
        self.assertEqual("blocked", blocked["status"])
        self.assertFalse(blocked["save_allowed"])
        self.assertFalse(blocked["save_called"])
        self.assertEqual([], calls)

        passed = MODULE.block_save_after_critical_failure(
            {"status": "failed", "critical": False},
            lambda: calls.append("saved"),
        )
        self.assertEqual("eligible", passed["status"])
        self.assertFalse(passed["save_called"])
        self.assertTrue(passed["save_callback_ignored"])
        self.assertEqual([], calls)
        with self.assertRaisesRegex(MODULE.HostActionError, "failure event"):
            MODULE.block_save_after_critical_failure(None, lambda: calls.append("saved"))

    def test_er11_quarantines_one_owned_failed_file_and_preserves_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "run"
            root.mkdir()
            baseline = Path(directory) / "baseline.scdoc"
            baseline.write_bytes(b"baseline")
            failed = root / "failed.scdoc"
            failed.write_bytes(b"failed artifact")
            digest = hashlib.sha256(failed.read_bytes()).hexdigest()
            result = MODULE.remove_run_owned_failed_artifact(
                failed,
                root,
                run_ref="run-11",
                ownership={"run_ref": "run-11"},
                failure_record={"status": "failed", "artifact_path": str(failed)},
                expected_sha256=digest,
                baseline_path=baseline,
            )
            quarantine = Path(result["quarantine_path"])
            self.assertEqual("quarantined", result["status"])
            self.assertFalse(failed.exists())
            self.assertTrue(quarantine.is_file())
            self.assertEqual(digest, hashlib.sha256(quarantine.read_bytes()).hexdigest())
            self.assertEqual(b"baseline", baseline.read_bytes())
            self.assertTrue(result["recoverable"])
            self.assertFalse(result["recursive"])

    def test_er11_requires_ownership_hash_and_nonreserved_regular_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "run"
            root.mkdir()
            failed = root / "failed.scdoc"
            failed.write_bytes(b"failed")
            digest = hashlib.sha256(failed.read_bytes()).hexdigest()
            base_kwargs = {
                "run_ref": "run-11",
                "ownership": {"run_ref": "run-11"},
                "failure_record": {"status": "failed", "artifact_path": str(failed)},
                "expected_sha256": digest,
            }
            with self.assertRaises(MODULE.HostActionError):
                MODULE.remove_run_owned_failed_artifact(failed, root, **dict(base_kwargs, ownership={"run_ref": "other"}))
            with self.assertRaises(MODULE.HostActionError):
                MODULE.remove_run_owned_failed_artifact(failed, root, **dict(base_kwargs, expected_sha256="0" * 64))

            evidence = root / "evidence.json"
            evidence.write_bytes(b"evidence")
            with self.assertRaisesRegex(MODULE.HostActionError, "baseline/evidence"):
                MODULE.remove_run_owned_failed_artifact(
                    evidence,
                    root,
                    **dict(base_kwargs, failure_record={"status": "failed", "artifact_path": str(evidence)}, evidence_paths=[evidence]),
                )
            self.assertTrue(evidence.exists())

            outside = Path(directory) / "outside.scdoc"
            outside.write_bytes(b"outside")
            outside_kwargs = dict(base_kwargs, failure_record={"status": "failed", "artifact_path": str(outside)})
            with self.assertRaises(MODULE.HostActionError):
                MODULE.remove_run_owned_failed_artifact(outside, root, **outside_kwargs)

            child = root / "child"
            child.mkdir()
            child_kwargs = dict(base_kwargs, failure_record={"status": "failed", "artifact_path": str(child)})
            with self.assertRaises(MODULE.HostActionError):
                MODULE.remove_run_owned_failed_artifact(child, root, **child_kwargs)

    def test_er11_delete_mode_removes_only_one_file_without_recursive_delete(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "run"
            root.mkdir()
            failed = root / "failed.scdoc"
            sibling = root / "keep.txt"
            failed.write_bytes(b"failed")
            sibling.write_bytes(b"keep")
            digest = hashlib.sha256(failed.read_bytes()).hexdigest()
            result = MODULE.remove_run_owned_failed_artifact(
                failed,
                root,
                run_ref="run",
                ownership="run",
                failure_record={"status": "failed", "artifact_path": str(failed)},
                expected_sha256=digest,
                mode="delete",
            )
            self.assertEqual("deleted", result["status"])
            self.assertFalse(failed.exists())
            self.assertEqual(b"keep", sibling.read_bytes())


if __name__ == "__main__":
    unittest.main()
