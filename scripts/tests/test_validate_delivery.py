"""Disposable delivery fixtures; no dependency on the current delivery state."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "validate-delivery.py"
PROJECTS = ("code-smells-project", "ecommerce-api-legacy", "task-manager-api")
REFERENCES = ("project-analysis", "anti-patterns", "audit-report-template",
              "mvc-guidelines", "refactoring-playbook", "validation")


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.write("README.md", "\n".join("## " + section for section in
                   ("Análise Manual", "Construção da Skill", "Resultados", "Como Executar")))
        for number, project in enumerate(PROJECTS, 1):
            self.write(f"{project}/README.md", "[delivery](../README.md)")
            self.write(f"{project}/app.py", "app = object()")
            for role in ("models", "controllers", "routes"):
                self.write(f"{project}/{role}/item.py", "item = object()")
            prefix = f"{project}/.agents/skills/refactor-arch"
            self.write(f"{prefix}/SKILL.md", "---\nname: refactor-arch\ndescription: Audit legacy projects.\n---\n" +
                       "\n".join(f"[{name}](references/{name}.md)" for name in REFERENCES))
            for name in REFERENCES:
                self.write(f"{prefix}/references/{name}.md", "# Reference\n")
            self.write(f"{prefix}/references/anti-patterns.md", "\n".join(
                f"| AP-{i:02} | {severity} | evidence |" for i, severity in enumerate(
                    ["CRITICAL"] * 3 + ["HIGH"] * 4 + ["MEDIUM"] * 3 + ["LOW"] * 2, 1)))
            self.write(f"{prefix}/references/refactoring-playbook.md", self.examples(12))
            self.write(f"reports/audit-project-{number}.md", f"# Audit\n[log](evidence/audit-{number}.txt)")
            self.write(f"reports/validation-project-{number}.md", f"# Validation\n[log](evidence/run-{number}.jsonl)")
            self.write(f"reports/evidence/audit-{number}.txt", "Observed audit output\n")
            self.write(f"reports/evidence/run-{number}.jsonl", '{"event": "boot", "result": "pass"}\n')

    def write(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    @staticmethod
    def examples(count, body="return connection.execute(sql)"):
        return "\n".join(f"## AP-{i:02} — Example\n\nBefore:\n\n```python\n{body}\n```\n\nAfter:\n\n```python\nreturn connection.execute(sql, values)\n```\n" for i in range(1, count + 1))

    def run_validator(self):
        return subprocess.run([sys.executable, "-X", "utf8", str(SCRIPT), "--root", str(self.root)],
                              capture_output=True, text=True, encoding="utf-8")

    def assert_invalid(self, expected):
        result = self.run_validator()
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn(expected, result.stdout + result.stderr)

    def test_complete_alternative_root_passes(self):
        result = self.run_validator()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_missing_audit(self):
        (self.root / "reports/audit-project-2.md").unlink()
        self.assert_invalid("audit-project-2.md")

    def test_missing_reference(self):
        (self.root / PROJECTS[0] / ".agents/skills/refactor-arch/references/validation.md").unlink()
        self.assert_invalid("validation.md")

    def test_reduced_playbook(self):
        for project in PROJECTS:
            self.write(f"{project}/.agents/skills/refactor-arch/references/refactoring-playbook.md", self.examples(2))
        self.assert_invalid("concrete before/after")

    def test_unequal_packages(self):
        self.write(f"{PROJECTS[1]}/.agents/skills/refactor-arch/references/validation.md", "changed")
        self.assert_invalid("differs")

    def test_absent_log(self):
        (self.root / "reports/evidence/run-3.jsonl").unlink()
        self.assert_invalid("run-3.jsonl")

    def test_empty_logs_are_not_evidence(self):
        self.write("reports/evidence/run-3.jsonl", "\n")
        self.assert_invalid("nonempty")

    def test_comments_only_are_not_examples(self):
        for project in PROJECTS:
            self.write(f"{project}/.agents/skills/refactor-arch/references/refactoring-playbook.md", self.examples(12, "# fix this later"))
        self.assert_invalid("concrete before/after")

    def test_readme_links_are_checked(self):
        self.write(f"{PROJECTS[2]}/README.md", "[missing](missing.md)")
        self.assert_invalid("missing.md")

    def test_reference_style_links_are_checked(self):
        self.write("README.md", (self.root / "README.md").read_text(encoding="utf-8") +
                   "\n[missing][evidence]\n\n[evidence]: reports/missing.txt\n")
        self.assert_invalid("missing.txt")

    def test_generated_sources_do_not_satisfy_mvc(self):
        shutil.rmtree(self.root / PROJECTS[0] / "controllers")
        self.write(f"{PROJECTS[0]}/node_modules/example/controllers/fake.py", "fake = True")
        self.assert_invalid("controllers")

    def test_generated_markdown_is_excluded(self):
        self.write("reports/node_modules/library/README.md", "[bad](missing.md)")
        self.write(f"{PROJECTS[0]}/.venv/README.md", "[bad](missing.md)")
        result = self.run_validator()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_missing_frontmatter_description(self):
        path = self.root / PROJECTS[0] / ".agents/skills/refactor-arch/SKILL.md"
        path.write_text(path.read_text(encoding="utf-8").replace(
            "description: Audit legacy projects.\n", ""), encoding="utf-8")
        self.assert_invalid("frontmatter")

    def test_missing_catalog_family(self):
        for project in PROJECTS:
            path = self.root / project / ".agents/skills/refactor-arch/references/anti-patterns.md"
            path.write_text(path.read_text(encoding="utf-8").replace("AP-12", "AP-13"), encoding="utf-8")
        self.assert_invalid("catalog missing AP-12")

    def test_missing_required_readme_section(self):
        self.write("README.md", "## Análise Manual\n")
        self.assert_invalid("Resultados")

    def test_missing_entry(self):
        (self.root / PROJECTS[1] / "app.py").unlink()
        self.assert_invalid("application entry")

    def test_example_links_do_not_require_fictional_files(self):
        path = self.root / "README.md"
        path.write_text(path.read_text(encoding="utf-8") +
                        "\n```markdown\n[example](fictional.md)\n```\n", encoding="utf-8")
        result = self.run_validator()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
