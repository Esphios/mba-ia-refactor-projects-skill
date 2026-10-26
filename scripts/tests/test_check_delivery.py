import importlib.util
from pathlib import Path
import tempfile
import unittest


MODULE = Path(__file__).parents[1] / "check_delivery.py"
spec = importlib.util.spec_from_file_location("check_delivery", MODULE)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class DeliveryChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.write("README.md", "\n".join("## " + s for s in (
            "Análise Manual", "Construção da Skill", "Resultados", "Como Executar")))
        for number, project in enumerate(checker.PROJECTS, 1):
            prefix = f"{project}/.agents/skills/refactor-arch/"
            self.write(prefix + "SKILL.md", "---\nname: refactor-arch\ndescription: Audit legacy code\n---\n")
            for name in checker.REFERENCES:
                text = "# Reference\nUseful instruction.\n"
                if name == "refactoring-playbook.md":
                    text = "\n".join(
                        f"## AP-{i:02d}\nBefore:\n```python\nx = 1\n```\nAfter:\n```python\nx = 2\n```"
                        for i in range(1, 9))
                self.write(prefix + "references/" + name, text)
            self.write(f"reports/audit-project-{number}.md", "# Audit\nMeasured findings.\n")
            self.write(f"reports/validation-project-{number}.md",
                       f"# Validation\n[log](evidence/project-{number}.log)\n")
            self.write(f"reports/evidence/project-{number}.log", "PASS\n")

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def test_complete_fixture(self):
        self.assertEqual(checker.validate(self.root), [])

    def test_audit_is_required_for_each_project(self):
        (self.root / "reports/audit-project-2.md").unlink()
        self.assertTrue(any("audit-project-2" in e for e in checker.validate(self.root)))

    def test_skill_copies_must_match(self):
        self.write(f"{checker.PROJECTS[1]}/.agents/skills/refactor-arch/SKILL.md", "Different skill")
        self.assertTrue(any("differ" in e for e in checker.validate(self.root)))

    def test_reference_cannot_be_missing(self):
        (self.root / checker.PROJECTS[0] / ".agents/skills/refactor-arch/references/delivery.md").unlink()
        self.assertTrue(any("delivery.md" in e for e in checker.validate(self.root)))

    def test_documented_evidence_must_exist(self):
        (self.root / "reports/evidence/project-3.log").unlink()
        self.assertTrue(any("project-3.log" in e for e in checker.validate(self.root)))

    def test_comments_do_not_count_as_transformations(self):
        for project in checker.PROJECTS:
            self.write(f"{project}/.agents/skills/refactor-arch/references/refactoring-playbook.md",
                       "## AP-01\nBefore:\n```python\n# before\n```\nAfter:\n```python\n# after\n```\n")
        self.assertTrue(any("examples" in e for e in checker.validate(self.root)))

    def test_readme_sections_are_required(self):
        self.write("README.md", "# Missing required delivery sections")
        self.assertTrue(any("Resultados" in e for e in checker.validate(self.root)))


if __name__ == "__main__":
    unittest.main()
