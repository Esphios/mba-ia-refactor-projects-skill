#!/usr/bin/env python3
"""Check delivery files and evidence references using only the standard library.

This is a structural gate, not proof of genuine execution, sound findings, MVC
semantics, endpoint coverage, authorship, Git tracking or a public remote.
"""
import argparse
import os
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit


PROJECTS = ("code-smells-project", "ecommerce-api-legacy", "task-manager-api")
REFERENCES = ("project-analysis", "anti-patterns", "audit-report-template",
              "mvc-guidelines", "refactoring-playbook", "validation")
PACKAGE_FILES = ("SKILL.md",) + tuple(f"references/{name}.md" for name in REFERENCES)
EXCLUDED = {"node_modules", ".git", ".venv", "venv", "env", "__pycache__",
            ".pytest_cache", ".mypy_cache", ".ruff_cache", ".tox", ".nox",
            "dist", "build", "coverage", "htmlcov", "site-packages", "bin", "obj"}
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})[^\n]*\n(.*?)^ {0,3}\1[ \t]*$",
                   re.MULTILINE | re.DOTALL)


def files_under(directory):
    """Prune dependencies before descending; never follow directory symlinks."""
    for current, directories, files in os.walk(directory, followlinks=False):
        directories[:] = sorted(name for name in directories
                                if name.casefold() not in EXCLUDED
                                and not (Path(current) / name).is_symlink())
        for name in sorted(files):
            yield Path(current) / name


def markdown_links(text):
    """Local destinations in inline links/images and reference definitions.

    Fenced examples and inline code are deliberately excluded. This handles the
    ordinary Markdown used by this repository, not the entire CommonMark grammar.
    """
    prose = FENCE.sub("", text)
    prose = re.sub(r"`+[^`\n]*`+", "", prose)
    destination = r'(<[^>\n]+>|[^\s<>]+?)(?:\s+["\'][^\n]*["\'])?'
    inline = re.finditer(r"!?\[[^\]\n]*\]\(" + destination + r"\)", prose)
    definitions = re.finditer(r"^ {0,3}\[[^\]\n]+\]:\s*" + destination + r"\s*$",
                              prose, re.MULTILINE)
    return [match.group(1).strip("<>") for match in (*inline, *definitions)]


def has_code(block):
    block = re.sub(r"/\*.*?\*/", "", block, flags=re.DOTALL)
    return any(line.strip() and not line.lstrip().startswith(("#", "//", "<!--"))
               for line in block.splitlines())


def concrete_examples(text):
    result = set()
    sections = re.split(r"^##\s+(AP-\d{2})\b[^\n]*$", text, flags=re.MULTILINE)
    for identifier, section in zip(sections[1::2], sections[2::2]):
        before = re.search(r"\b(?:Before|Antes)\b", section, re.IGNORECASE)
        after = re.search(r"\b(?:After|Depois)\b", section, re.IGNORECASE)
        if before and after and before.start() < after.start():
            old = FENCE.findall(section[before.end():after.start()])
            new = FENCE.findall(section[after.end():])
            if any(has_code(code) for _, code in old) and any(has_code(code) for _, code in new):
                result.add(identifier)
    return result


def validate(root):
    errors = []

    def display(path):
        return path.relative_to(root).as_posix() if path.is_relative_to(root) else str(path)

    def require(path):
        if not path.is_file():
            errors.append(f"missing file: {display(path)}")
            return ""
        try:
            content = path.read_text(encoding="utf-8-sig")
        except (UnicodeError, OSError) as error:
            errors.append(f"cannot read {display(path)}: {error}")
            return ""
        if not content.strip():
            errors.append(f"expected nonempty file: {display(path)}")
        return content

    markdown = set()
    readme = root / "README.md"
    text = require(readme)
    markdown.add(readme)
    headings = set(re.findall(r"^#{1,6}\s+(.+?)\s*#*\s*$", FENCE.sub("", text), re.MULTILINE))
    for heading in ("Análise Manual", "Construção da Skill", "Resultados", "Como Executar"):
        if heading not in headings:
            errors.append(f"README.md missing section: {heading}")

    canonical = {}
    for index, project in enumerate(PROJECTS):
        project_root = root / project
        project_readme = project_root / "README.md"
        require(project_readme)
        markdown.add(project_readme)
        package = project_root / ".agents/skills/refactor-arch"
        actual = {file.relative_to(package).as_posix(): file.read_bytes()
                  for file in files_under(package)}
        if index == 0:
            canonical = actual
        elif actual != canonical:
            errors.append(f"skill package differs from {PROJECTS[0]}: {project}")
        contents = {name: require(package / name) for name in PACKAGE_FILES}
        markdown.update(file for file in files_under(package) if file.suffix.lower() == ".md")
        frontmatter = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)", contents["SKILL.md"], re.DOTALL)
        fields = dict(re.findall(r"^([\w-]+):\s*(.+)$", frontmatter.group(1), re.MULTILINE)) if frontmatter else {}
        if fields.get("name", "").strip("\"'") != "refactor-arch" or not fields.get("description", "").strip("\"' "):
            errors.append(f"invalid name/description frontmatter: {display(package / 'SKILL.md')}")
        catalog = contents["references/anti-patterns.md"]
        for number in range(1, 13):
            identifier = f"AP-{number:02}"
            if not re.search(rf"^\|[^\n]*\b{identifier}\b[^\n]*\|\s*(?:CRITICAL|HIGH|MEDIUM|LOW)\s*\|", catalog, re.MULTILINE):
                errors.append(f"{project} catalog missing {identifier} with severity")
        for severity in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
            if not re.search(rf"\|\s*{severity}\s*\|", catalog):
                errors.append(f"{project} catalog missing severity {severity}")
        expected = {f"AP-{number:02}" for number in range(1, 13)}
        missing = expected - concrete_examples(contents["references/refactoring-playbook.md"])
        if missing:
            errors.append(f"{project} playbook missing concrete before/after examples: {', '.join(sorted(missing))}")
        sources = [file.relative_to(project_root) for file in files_under(project_root)
                   if file.suffix in {".py", ".js", ".cjs", ".mjs"}
                   and not set(file.relative_to(project_root).parts) & {".agents", "tests", "test"}]
        for role, names in (("models", {"models", "model"}),
                            ("controllers", {"controllers", "controller"}),
                            ("routes", {"routes", "views", "blueprints"})):
            if not any(set(file.parts[:-1]) & names and file.name != "__init__.py" for file in sources):
                errors.append(f"{project} missing {role} source module")
        if not any(file.name in {"app.py", "app.js", "server.js", "server.py", "index.js", "wsgi.py", "main.py"} for file in sources):
            errors.append(f"{project} missing application entry source")

    reports = []
    for number in range(1, 4):
        for kind in ("audit", "validation"):
            report = root / f"reports/{kind}-project-{number}.md"
            require(report)
            reports.append(report)
    markdown.update(file for file in files_under(root / "reports") if file.suffix.lower() == ".md")
    markdown.update(reports)
    links = {}
    for document in sorted(markdown):
        if not document.is_file():
            continue
        links[document] = []
        for destination in markdown_links(document.read_text(encoding="utf-8-sig")):
            parsed = urlsplit(destination)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            target = (document.parent / unquote(parsed.path)).resolve()
            links[document].append(target)
            if not target.exists():
                errors.append(f"broken link in {display(document)}: {destination}")
    evidence_root = (root / "reports/evidence").resolve()
    for report in reports:
        logs = [file for file in links.get(report, []) if file.is_relative_to(evidence_root)
                and file.suffix.lower() in {".txt", ".log", ".jsonl", ".json", ".md"}]
        if not logs:
            errors.append(f"{display(report)} must link to an actual log in reports/evidence/")
        for log in logs:
            require(log)
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1],
                        help="delivery repository root (default: script's parent repository)")
    args = parser.parse_args()
    errors = validate(args.root.resolve())
    for error in errors:
        print(f"FAIL: {error}")
    if errors:
        print(f"Delivery structure incomplete: {len(errors)} issue(s).")
        return 1
    print("Delivery structure PASS: packages, links, examples, MVC files and referenced logs exist.")
    print("Review and real application tests remain required; file presence does not prove execution or quality.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
