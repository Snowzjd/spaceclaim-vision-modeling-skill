from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = (
    ROOT / "spaceclaim-vision-modeling" / "references" / "controller-compatibility.md"
)
SKILL_PATH = ROOT / "spaceclaim-vision-modeling" / "SKILL.md"
README_PATH = ROOT / "README.md"

OPERATIONS = (
    "list_windows",
    "capture_window",
    "focus_window",
    "click",
    "type_text",
    "key",
    "stop",
    "health",
)
STATES = ("implemented", "tested", "unsupported", "not_tested")


class HostCapabilityContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = CONTRACT_PATH.read_text(encoding="utf-8")
        cls.skill = SKILL_PATH.read_text(encoding="utf-8")
        cls.readme = README_PATH.read_text(encoding="utf-8")

    def test_contract_declares_the_minimum_operation_set(self) -> None:
        self.assertIn("## Host capability contract", self.contract)
        for operation in OPERATIONS:
            self.assertIn("`%s`" % operation, self.contract, operation)

    def test_contract_keeps_the_four_capability_states(self) -> None:
        for state in STATES:
            self.assertIn("`%s`" % state, self.contract, state)
        self.assertIn("implemented` at most", self.contract)

    def test_contract_records_per_action_identity_and_metadata(self) -> None:
        for field in ("run id", "window handle and process id", "timestamp", "DPI"):
            self.assertIn(field, self.contract, field)
        self.assertIn("before and after each action", self.contract)
        self.assertIn("one backend and one input queue per run", self.contract)

    def test_stop_is_bounded_and_not_retried_on_another_backend(self) -> None:
        self.assertIn("two seconds from request to empty queue", self.contract)
        self.assertIn("not retried on another backend", self.contract)

    def test_skill_routes_to_the_contract_before_desktop_control(self) -> None:
        self.assertIn("references/controller-compatibility.md", self.skill)
        self.assertIn("host capability contract", self.skill)

    def test_readme_points_to_the_contract_without_adding_a_capability_claim(self) -> None:
        self.assertIn("host capability contract", self.readme)
        self.assertIn("declared is still not tested", self.readme)


if __name__ == "__main__":
    unittest.main()
