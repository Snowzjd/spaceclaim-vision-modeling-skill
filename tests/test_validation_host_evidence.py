"""Focused reproducibility checks for public P5 host-helper evidence."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "spaceclaim-vision-modeling"
PUBLIC = PACKAGE / "assets" / "evaluations" / "p5-actions"
PUBLIC_P4 = PACKAGE / "assets" / "evaluations" / "p4-actions"
HOST_ACTIONS_PATH = PACKAGE / "scripts" / "validation_host_actions.py"
SAVE_REPORT_PATH = PUBLIC_P4 / "save-report.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_host_actions():
    spec = importlib.util.spec_from_file_location("validation_host_actions", HOST_ACTIONS_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def public_path(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def collect_strings(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield from collect_strings(key)
            yield from collect_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from collect_strings(item)
    elif isinstance(value, str):
        yield value


class ValidationHostEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.host_actions = load_host_actions()
        cls.host_checks = load_json(PUBLIC / "host-checks.json")
        cls.observation_document = load_json(PUBLIC / "reopen-observation.json")
        cls.cases = {case["catalog_id"]: case for case in cls.host_checks["cases"]}

    def test_public_native_reproduces_va19_and_va20_flat_results(self) -> None:
        native_candidates = sorted(PUBLIC_P4.rglob("*.scdoc"))
        self.assertEqual(1, len(native_candidates))
        native = native_candidates[0]
        native_hash = sha256(native)
        va19 = self.cases["VA-19"]
        va20 = self.cases["VA-20"]

        self.assertEqual(native_hash, self.host_checks["provenance"]["native_source"]["sha256"])
        self.assertEqual(native_hash, self.host_checks["provenance"]["public_native"]["sha256"])
        self.assertEqual(public_path(native), va19["result"]["path"])
        self.assertEqual(public_path(native), va20["result"]["path"])

        actual_va19 = self.host_actions.check_output_file_identity(str(native.resolve()), native_hash)
        actual_va19["path"] = public_path(native)
        self.assertEqual(actual_va19, va19["result"])

        run_ref = va20["inputs"]["run_ref"]
        save_record = va20["inputs"]["save_record"]
        actual_va20 = self.host_actions.check_native_save_result(
            str(native.resolve()),
            native_hash,
            save_record,
            run_ref,
        )
        actual_va20["path"] = public_path(native)
        self.assertEqual(actual_va20, va20["result"])

        save_report = load_json(SAVE_REPORT_PATH)
        save_report_hash = sha256(SAVE_REPORT_PATH)
        self.assertEqual(save_report_hash, self.host_checks["provenance"]["save_report"]["sha256"])
        self.assertTrue(run_ref.startswith("runs/p4-live/save-01|report_sha256:"))
        self.assertIn(save_report_hash, run_ref)
        self.assertNotIn("run_ref", save_report)
        self.assertFalse(va20["result"]["native_save_observed"])
        self.assertEqual("not_tested", va20["result"]["native_reopen"])

    def test_public_reopen_observation_reproduces_va23(self) -> None:
        native_candidates = sorted(PUBLIC_P4.rglob("*.scdoc"))
        self.assertEqual(1, len(native_candidates))
        native_hash = sha256(native_candidates[0])
        va23 = self.cases["VA-23"]
        observation_source = self.observation_document["source_report"]
        observation = self.observation_document["observation"]

        self.assertEqual("runs/p5-live/reopen-01/report.json", observation_source["path"])
        self.assertRegex(observation_source["sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(
            observation_source["sha256"],
            self.host_checks["provenance"]["reopen_report"]["sha256"],
        )
        self.assertEqual(
            sha256(PUBLIC / "reopen-observation.json"),
            self.host_checks["provenance"]["reopen_observation"]["sha256"],
        )
        self.assertEqual(native_hash, observation["artifact_sha256"])
        self.assertEqual("native_reopen", observation["source_kind"])
        self.assertEqual("measured", observation["status"])
        self.assertEqual(
            {
                "count",
                "bbox_mm",
                "volume_mm3",
                "status",
                "source_kind",
                "artifact_sha256",
            },
            set(self.observation_document["report_fields"]),
        )
        self.assertEqual(1, self.observation_document["report_fields"]["count"])
        self.assertEqual(native_hash, self.observation_document["report_fields"]["artifact_sha256"])
        self.assertEqual("native_reopen", self.observation_document["report_fields"]["source_kind"])
        self.assertEqual("passed", self.observation_document["report_fields"]["status"])
        self.assertEqual(
            "observation_plus_selected_report_fields",
            observation_source["extraction"]["mode"],
        )
        self.assertIn("not a full report copy", observation_source["extraction"]["note"])
        self.assertNotIn("active_path", self.observation_document)
        self.assertIn("active_path", {item["field"] for item in observation_source["redactions"]})

        inputs = va23["inputs"]
        actual = self.host_actions.check_observed_property(
            observation,
            inputs["expected_value"],
            inputs["expected_artifact_sha256"],
            absolute_tolerance=inputs["absolute_tolerance"],
            action_id=inputs["action_id"],
        )
        self.assertEqual(actual, va23["result"])
        self.assertEqual("passed", actual["status"])
        self.assertFalse(actual["runtime_observed"])

    def test_va25_has_no_fabricated_reimport_result(self) -> None:
        va25 = self.cases["VA-25"]
        self.assertEqual("not_tested", va25["status"])
        self.assertIsNone(va25["result"])
        self.assertNotIn("inputs", va25)
        self.assertTrue(va25["reason"])

    def test_public_host_evidence_uses_relative_paths_only(self) -> None:
        for path in (PUBLIC / "host-checks.json", PUBLIC / "reopen-observation.json"):
            with self.subTest(path=path.name):
                for value in collect_strings(load_json(path)):
                    self.assertIsNone(re.match(r"^[A-Za-z]:[\\/]", value))
                    self.assertFalse(value.startswith("\\\\"))


if __name__ == "__main__":
    unittest.main()
