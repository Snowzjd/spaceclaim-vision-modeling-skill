from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_PATH = ROOT / "spaceclaim-vision-modeling" / "SKILL.md"
WORKFLOW_PATH = (
    ROOT / "spaceclaim-vision-modeling" / "references" / "execution-workflow.md"
)


class ExecutionWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skill = SKILL_PATH.read_text(encoding="utf-8")
        cls.workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    def test_skill_routes_authorized_runs_to_fast_workflow(self) -> None:
        self.assertIn("references/execution-workflow.md", self.skill)
        self.assertIn("Do not insert manual geometry reviews", self.skill)

    def test_fast_workflow_has_only_meaningful_gates(self) -> None:
        for gate in ("Entry state", "Run result", "Persistence", "Final review"):
            self.assertIn(gate, self.workflow)
        self.assertIn("Do not perform a separate repository audit", self.workflow)
        self.assertIn("Never press Run again", self.workflow)

    def test_starting_document_rules_are_explicit(self) -> None:
        self.assertIn("No baseline model", self.workflow)
        self.assertIn("Baseline model supplied", self.workflow)
        self.assertIn("new unsaved design", self.workflow)
        self.assertIn("Do not create or save an extra blank working model", self.workflow)
        self.assertIn("baseline-copy mode", self.workflow)
        self.assertIn("no-baseline script", self.workflow)
        self.assertIn("Never modify the baseline", self.workflow)

    def test_visual_control_preserves_a_large_workspace(self) -> None:
        self.assertIn("maximized or full-screen workspace", self.workflow)
        self.assertIn("visual-interaction.md", self.workflow)
        self.assertIn("multi-view visual agreement", self.workflow)


if __name__ == "__main__":
    unittest.main()
