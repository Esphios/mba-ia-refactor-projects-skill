"""Check repository delivery artifacts; this is not a substitute for runtime tests."""

import argparse
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit


PROJECTS = ("code-smells-project", "ecommerce-api-legacy", "task-manager-api")
REFERENCES = tuple(name + ".md" for name in (
    "project-analysis", "anti-patterns", "audit-report-template", "mvc-guidelines",
    "refactoring-playbook", "validation", "delivery", "regression-checks"))
SECTIONS = ("Análise Manual", "Construção da Skill", "Resultados", "Como Executar")
FENCES = re.compile(r"^```[^\n]*\n(.*?)^```\s*$", re.MULTILINE | re.DOTALL)


def example_count(text):
    count = 0
    for section in re.split(r"^## AP-\d+[^\n]*$", text, flags=re.MULTILINE)[1:]:
        parts = re.split(r"\bAfter\b", section, maxsplit=1)
        if len(parts) != 2 or "Before" not in parts[0]:
            continue
        sides = [FENCES.findall(part) for part in parts]
        if all(any(any(line.strip() and not line.lstrip().startswith(("#", "//", "/*"))
                       for line in block.splitlines()) for block in side) for side in sides):
            count += 1
    return count


def validate(root):
    root = Path(root).resolve()
    errors, documents, packages = [], [], []

    def read(path):
        if not path.is_file():
            errors.append(f"Missing file: {path.relative_to(root)}")
            return ""
        try:
            text = path.read_text(encoding="utf-8-sig")
        except (UnicodeError, OSError) as error:
            errors.append(f"Cannot read {path.relative_to(root)}: {error}")
            return ""
        if not text.strip():
            errors.append(f"Empty file: {path.relative_to(root)}")
        documents.append((path, text))
        return text

    readme = read(root / "README.md")
    headings = re.findall(r"^#{1,6}\s+(.+?)\s*$", FENCES.sub("", readme), re.MULTILINE)
    for section in SECTIONS:
        if section not in headings:
            errors.append(f"README missing section: {section}")

    for number, project in enumerate(PROJECTS, 1):
        package = root / project / ".agents/skills/refactor-arch"
        entry = read(package / "SKILL.md")
        if not re.search(r"^name:\s*refactor-arch\s*$", entry, re.MULTILINE):
            errors.append(f"Invalid skill name: {project}")
        for reference in REFERENCES:
            text = read(package / "references" / reference)
            if reference == "refactoring-playbook.md" and example_count(text) < 8:
                errors.append(f"Fewer than eight concrete before/after examples: {project}")
        packages.append({file.relative_to(package).as_posix(): file.read_bytes()
                         for file in package.rglob("*") if file.is_file()})
        read(root / "reports" / f"audit-project-{number}.md")
        read(root / "reports" / f"validation-project-{number}.md")

    if any(package != packages[0] for package in packages[1:]):
        errors.append("Skill packages differ between projects")

    for path, text in documents:
        prose = FENCES.sub("", text)
        prose = re.sub(r"`[^`\n]*`", "", prose)
        for destination in re.findall(r"\]\(([^)\s]+)\)", prose):
            parsed = urlsplit(destination.strip("<>"))
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            target = (path.parent / unquote(parsed.path)).resolve()
            if not target.is_relative_to(root):
                errors.append(f"Nonportable local link in {path.relative_to(root)}: {destination}")
            elif not target.is_file() or target.stat().st_size == 0:
                errors.append(f"Missing or empty linked file in {path.relative_to(root)}: {destination}")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    errors = validate(args.root)
    if errors:
        for error in errors:
            print("FAIL:", error)
        return 1
    print("PASS: delivery artifacts, local links, skill copies and transformation examples.")
    print("Actual boot, HTTP contracts, finding quality and approval evidence require separate review.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
