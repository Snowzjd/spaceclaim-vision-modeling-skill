from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "spaceclaim-vision-modeling"
SKILL_PATH = PACKAGE / "SKILL.md"
VISUAL_PATH = PACKAGE / "references" / "visual-interaction.md"
WORKFLOW_PATH = PACKAGE / "references" / "execution-workflow.md"
REVIEWER_PATH = PACKAGE / "prompts" / "validation_reviewer.md"
CASE_VISUAL_RECORDS = {
    "001": (
        PACKAGE / "assets" / "cases" / "001-offset-block-array" / "validation-checklist.md",
        PACKAGE / "assets" / "cases" / "001-offset-block-array" / "runtime-evidence.md",
    ),
    "002": (
        PACKAGE / "assets" / "cases" / "002-flanged-short-pipe" / "validation" / "checklist.md",
        PACKAGE / "assets" / "cases" / "002-flanged-short-pipe" / "validation" / "runtime-evidence.md",
    ),
    "003": (
        PACKAGE / "assets" / "cases" / "003-stepped-shaft-keyway" / "validation" / "checklist.md",
        PACKAGE / "assets" / "cases" / "003-stepped-shaft-keyway" / "validation" / "runtime-evidence.md",
    ),
    "004": (
        PACKAGE / "assets" / "cases" / "004-rounded-plate-support" / "validation" / "checklist.md",
        PACKAGE / "assets" / "cases" / "004-rounded-plate-support" / "validation" / "runtime-evidence.md",
    ),
}


class VisualInteractionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skill = SKILL_PATH.read_text(encoding="utf-8")
        cls.visual = VISUAL_PATH.read_text(encoding="utf-8")
        cls.workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
        cls.reviewer = REVIEWER_PATH.read_text(encoding="utf-8")
        cls.case_visual_records = {
            case_id: (
                checklist.read_text(encoding="utf-8"),
                evidence.read_text(encoding="utf-8"),
            )
            for case_id, (checklist, evidence) in CASE_VISUAL_RECORDS.items()
        }

    def test_skill_routes_viewport_work_to_visual_reference(self) -> None:
        self.assertIn("references/visual-interaction.md", self.skill)
        self.assertIn("maximized or full-screen", self.skill)
        self.assertIn("navigation themes can remap", self.skill)

    def test_default_mouse_and_keyboard_operations_are_covered(self) -> None:
        required = (
            "Left click",
            "Ctrl",
            "Double left click",
            "Triple left click",
            "Right click",
            "middle mouse button",
            "Shift",
            "Wheel zoom",
            "Alt+Z",
            "Home view",
            "Plan view",
        )
        for operation in required:
            with self.subTest(operation=operation):
                self.assertIn(operation, self.visual)

    def test_selection_and_viewpoint_rules_are_explicit(self) -> None:
        for rule in (
            "left-to-right",
            "right-to-left",
            "selection filter",
            "standard views",
            "front and back",
            "left and right",
            "top and bottom",
            "Plan or Snap view",
        ):
            with self.subTest(rule=rule):
                self.assertIn(rule, self.visual)

    def test_navigation_theme_requires_calibration(self) -> None:
        self.assertIn("navigation themes and custom options can remap", self.visual)
        self.assertIn("one small reversible navigation motion", self.visual)
        self.assertIn("not as proof of the current machine configuration", self.visual)

    def test_controller_capability_gate_prevents_false_input_claims(self) -> None:
        self.assertIn("confirm that the active desktop controller can express it", self.visual)
        self.assertIn("modifier held during a mouse action", self.visual)
        self.assertIn("Spin, Pan, or Zoom control", self.visual)
        self.assertIn("Do not claim direct automation", self.visual)

    def test_visual_acceptance_has_separate_evidence_contract(self) -> None:
        for field in (
            "view name or orientation:",
            "selection state:",
            "expected visible features:",
            "observed agreement or discrepancy:",
            "occluded or unresolved features:",
            "capture path and hash, when archived:",
        ):
            with self.subTest(field=field):
                self.assertIn(field, self.visual)
        self.assertIn("does not replace dimensional", self.visual)
        self.assertIn("Mark visual agreement `not_tested`", self.visual)

    def test_fast_workflow_preserves_full_viewport_and_visual_gates(self) -> None:
        self.assertIn("maximized or full-screen workspace", self.workflow)
        self.assertIn("visual-interaction.md", self.workflow)
        self.assertIn("multi-view visual agreement", self.workflow)
        self.assertIn("Do not turn every routine click", self.workflow)

    def test_validation_reviewer_requires_multiview_review(self) -> None:
        self.assertIn("multi-view visual agreement", self.reviewer)
        self.assertIn("maximized unobstructed viewport", self.reviewer)
        self.assertIn("recorded unresolved occlusion", self.reviewer)

    def test_cases_001_to_004_record_completed_visual_reviews(self) -> None:
        for case_id, (checklist, evidence) in self.case_visual_records.items():
            with self.subTest(case_id=case_id):
                self.assertIn("- [x]", checklist)
                self.assertIn("visual review", (checklist + evidence).lower())
                self.assertIn("Review date: 2026-08-31", evidence)
                self.assertIn("maximized SpaceClaim 2022 R1 window", evidence)
                self.assertIn("visual-home.png", evidence)
                self.assertIn("SHA-256", evidence)

    def test_zoom_extents_has_visible_control_fallback(self) -> None:
        self.assertIn("GPU overlay", self.visual)
        self.assertIn("choose Zoom Extents", self.visual)
        self.assertIn("Do not repeatedly retry", self.visual)

    def test_official_help_sources_are_linked_without_bundling_vendor_docs(self) -> None:
        for page in (
            "SpaceClaim_shortcuts.htm",
            "Selecting.htm",
            "Orienting_Spinning_your_design.htm",
            "Orienting_Panning_your_design.htm",
            "Navigation_options.htm",
        ):
            with self.subTest(page=page):
                self.assertIn(page, self.visual)


if __name__ == "__main__":
    unittest.main()
