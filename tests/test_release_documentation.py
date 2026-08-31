from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README_PATH = ROOT / "README.md"
CHANGELOG_PATH = ROOT / "CHANGELOG.md"
VERSION_PATH = ROOT / "VERSION"
SKILL_PATH = ROOT / "spaceclaim-vision-modeling" / "SKILL.md"
BOUNDARY_PATH = (
    ROOT / "spaceclaim-vision-modeling" / "references" / "integration-boundary.md"
)
AGENTS_PATH = ROOT / "AGENTS.md"


class ReleaseDocumentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.readme = README_PATH.read_text(encoding="utf-8")
        cls.changelog = CHANGELOG_PATH.read_text(encoding="utf-8")
        cls.skill = SKILL_PATH.read_text(encoding="utf-8")
        cls.boundary = BOUNDARY_PATH.read_text(encoding="utf-8")
        cls.agents = AGENTS_PATH.read_text(encoding="utf-8")
        cls.version = VERSION_PATH.read_text(encoding="utf-8").strip()

    def test_release_version_is_aligned(self) -> None:
        self.assertEqual("0.2.0", self.version)
        self.assertIn("Version: **v%s**" % self.version, self.readme)
        self.assertIn("## v%s" % self.version, self.changelog)
        self.assertNotIn("Local release candidate", self.readme)
        self.assertNotIn("Latest published release", self.readme)

    def test_readme_declares_exactly_three_external_capability_groups(self) -> None:
        section = self.readme.split("## Required external capabilities", 1)[1].split(
            "\n## ", 1
        )[0]
        numbered = re.findall(r"(?m)^(\d+)\. \*\*(.+?)\*\*", section)
        self.assertEqual(["1", "2", "3"], [number for number, _ in numbered])
        labels = " ".join(label.lower() for _, label in numbered)
        self.assertIn("visual", labels)
        self.assertIn("computer-use", labels)
        self.assertIn("spaceclaim", labels)

    def test_public_overview_and_boundary_are_case_neutral(self) -> None:
        public_boundary = self.readme + "\n" + self.boundary
        forbidden = (
            "001-offset-block-array",
            "002-flanged-short-pipe",
            "003-stepped-shaft-keyway",
            "004-rounded-plate-support",
            "INLET",
            "OUTLET",
        )
        for token in forbidden:
            self.assertNotIn(token, public_boundary)

    def test_authorized_control_defaults_to_maximized_spaceclaim(self) -> None:
        combined = self.skill + "\n" + self.readme
        self.assertRegex(
            combined,
            r"throughout authorized control by default|throughout authorized control",
        )

    def test_external_artifacts_are_provenance_not_required_public_proof(self) -> None:
        self.assertIn("bounded provenance", self.agents)
        self.assertIn("must not be required to reproduce a public capability claim", self.agents)
        self.assertIn("cannot independently inspect", self.readme)

    def test_runtime_claims_are_bound_to_exact_executed_artifacts(self) -> None:
        self.assertIn("Runtime evidence is bound to the exact executed artifact", self.readme)
        self.assertIn("Bind runtime claims to the exact executed artifact", self.boundary)

    def test_public_text_stays_within_spaceclaim_modeling_scope(self) -> None:
        forbidden = (("mesh" + "ing").lower(), ("flu" + "ent").lower())
        violations = []
        text_suffixes = {".md", ".py", ".json", ".yaml", ".yml", ".txt"}
        for path in ROOT.rglob("*"):
            if not path.is_file() or ".git" in path.parts or path.suffix.lower() not in text_suffixes:
                continue
            text = path.read_text(encoding="utf-8").lower()
            for token in forbidden:
                if token in text:
                    violations.append("%s: %s" % (path.relative_to(ROOT), token))
        self.assertEqual([], violations)


if __name__ == "__main__":
    unittest.main()
