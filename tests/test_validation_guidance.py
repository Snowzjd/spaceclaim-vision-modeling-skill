"""Focused integrity checks for the frozen P5 guidance evaluation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "spaceclaim-vision-modeling"
PUBLIC = PACKAGE / "assets" / "evaluations" / "p5-actions"
GUIDES = PUBLIC / "initial-guides"
MANIFEST = PUBLIC / "snapshot-manifest.json"
IDS = [f"VA-{number:02d}" for number in range(4, 26)] + [
    f"VI-{number:02d}" for number in range(1, 23)
]
INPUT_STATES = {"normal", "ambiguous", "missing", "contradictory"}
CASE_KEYS = {
    "catalog_id",
    "guidance_file",
    "guidance_sha256",
    "input_state",
    "disposition",
    "single_action_plan",
    "bounded_output_fields",
    "refusal_reason",
    "resolution_request",
    "uncertainty",
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ValidationGuidanceTests(unittest.TestCase):
    def test_public_snapshots_match_original_sha256_manifest(self) -> None:
        manifest = load_json(MANIFEST)
        self.assertEqual("p5-independent-public-snapshot-manifest", manifest["format"])
        for name, record in manifest["files"].items():
            with self.subTest(name=name):
                published = PUBLIC / name
                self.assertEqual(record["sha256"], sha256(published))
                self.assertEqual(record["size_bytes"], published.stat().st_size)

    def test_all_44_ids_are_unique_and_cover_input_states(self) -> None:
        raw = load_json(PUBLIC / "raw-inputs.json")
        results = load_json(PUBLIC / "results.json")
        raw_cases = raw["cases"]
        result_cases = results["cases"]
        raw_ids = [case["catalog_id"] for case in raw_cases]
        result_ids = [case["catalog_id"] for case in result_cases]

        self.assertEqual(44, len(raw_cases))
        self.assertEqual(44, len(result_cases))
        self.assertEqual(IDS, raw_ids)
        self.assertEqual(IDS, result_ids)
        self.assertEqual(44, len(set(raw_ids)))
        self.assertEqual(44, len(set(result_ids)))
        self.assertEqual(INPUT_STATES, {case["input_state"] for case in result_cases})
        self.assertEqual(
            {state: 11 for state in INPUT_STATES},
            {
                state: sum(case["input_state"] == state for case in result_cases)
                for state in INPUT_STATES
            },
        )
        self.assertEqual(
            {state: 11 for state in INPUT_STATES},
            {
                state: sum(case["provenance"]["state_class"] == state for case in raw_cases)
                for state in INPUT_STATES
            },
        )

        self.assertEqual("synthetic-only", raw["fixture_mode"])
        self.assertEqual("not_performed", raw["host_or_gui_execution"])
        for case in raw_cases:
            with self.subTest(action=case["catalog_id"]):
                self.assertEqual("synthetic-hand-authored", case["provenance"]["source"])
                self.assertEqual("input-only", case["provenance"]["observation_boundary"])
                self.assertEqual(
                    case["provenance"]["state_class"],
                    next(item["input_state"] for item in result_cases if item["catalog_id"] == case["catalog_id"]),
                )

    def test_each_case_guidance_hash_matches_its_initial_snapshot(self) -> None:
        results = load_json(PUBLIC / "results.json")
        snapshot_names = {path.stem.upper() for path in GUIDES.glob("*.json")}
        self.assertEqual(set(IDS), snapshot_names)

        for case in results["cases"]:
            action_id = case["catalog_id"]
            expected_relative = (
                f"spaceclaim-vision-modeling/references/atomic-guidance/"
                f"{action_id.lower()}.json"
            )
            snapshot = GUIDES / f"{action_id.lower()}.json"
            with self.subTest(action=action_id):
                self.assertEqual(expected_relative, case["guidance_file"])
                self.assertTrue(snapshot.is_file())
                self.assertEqual(case["guidance_sha256"], sha256(snapshot))
                self.assertEqual(action_id, load_json(snapshot)["catalog_id"])

    def test_frozen_decisions_have_no_runtime_result_fields(self) -> None:
        results = load_json(PUBLIC / "results.json")
        self.assertEqual("p5-independent-results", results["format"])
        self.assertEqual(44, len(results["cases"]))
        for case in results["cases"]:
            with self.subTest(action=case["catalog_id"]):
                self.assertLessEqual(set(case), CASE_KEYS)
                self.assertIn(case["disposition"], {"plan_only", "refuse"})
                self.assertIsInstance(case["bounded_output_fields"], list)
                self.assertTrue(case["uncertainty"])

    def test_refusal_fields_and_bounded_plan_fields_are_structurally_exclusive(self) -> None:
        results = load_json(PUBLIC / "results.json")
        dispositions = {case["disposition"] for case in results["cases"]}
        self.assertEqual({"plan_only", "refuse"}, dispositions)
        for case in results["cases"]:
            with self.subTest(action=case["catalog_id"]):
                if case["disposition"] == "refuse":
                    self.assertNotIn("single_action_plan", case)
                    self.assertEqual([], case["bounded_output_fields"])
                    self.assertIsInstance(case.get("refusal_reason"), str)
                    self.assertTrue(case["refusal_reason"].strip())
                    self.assertIsInstance(case.get("resolution_request"), str)
                    self.assertTrue(case["resolution_request"].strip())
                else:
                    self.assertNotIn("refusal_reason", case)
                    self.assertNotIn("resolution_request", case)
                    self.assertIsInstance(case.get("single_action_plan"), str)
                    self.assertTrue(case["single_action_plan"].strip())
                    self.assertGreater(len(case["bounded_output_fields"]), 0)


if __name__ == "__main__":
    unittest.main()
