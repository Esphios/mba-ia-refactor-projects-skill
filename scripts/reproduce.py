"""Install and validate this delivery, including actual isolated HTTP processes.

Run in a clean checkout for acceptance. Logs contain command output, never an
environment dump. Project HTTP runners own their disposable data and children.
"""

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from processes import run_owned


PYTHON_PROJECTS = ("code-smells-project", "task-manager-api")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, required=True,
                        help="New directory for raw local command logs and summary.json; review before sharing")
    parser.add_argument("--skip-install", action="store_true",
                        help="Reuse .venv-delivery and node_modules; not a clean reproduction")
    args = parser.parse_args()
    root, output = args.root.resolve(), args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    results = []
    environment = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")

    def run(name, command, cwd=root, timeout=600):
        log = output / f"{name}.log"
        print(f"Running {name}...", flush=True)
        started = time.monotonic()
        with log.open("w", encoding="utf-8") as stream:
            stream.write(f"Command: {json.dumps([str(item) for item in command])}\n")
            stream.flush()
            try:
                code = run_owned([str(item) for item in command], cwd=cwd,
                                 env=environment, stream=stream, timeout=timeout)
            except (OSError, subprocess.TimeoutExpired) as error:
                stream.write(f"\nRunner error: {error}\n")
                code = 124 if isinstance(error, subprocess.TimeoutExpired) else 127
        results.append({"step": name, "exit_code": code,
                        "seconds": round(time.monotonic() - started, 2), "log": log.name})
        (output / "summary.json").write_text(
            json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if code:
            raise RuntimeError(f"{name} failed ({code}); see {log}")

    try:
        run("integration-tests", [sys.executable, "-m", "unittest", "discover",
                                  "-s", "scripts/tests", "-v"])
        run("delivery-artifacts", [sys.executable, "scripts/check_delivery.py"])
        for project in PYTHON_PROJECTS:
            directory = root / project
            venv = directory / ".venv-delivery"
            executable = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
            if not args.skip_install:
                if venv.exists():
                    raise RuntimeError(f"Use a clean checkout: {venv} already exists")
                run(f"{project}-venv", [sys.executable, "-m", "venv", venv])
                run(f"{project}-install", [executable, "-m", "pip", "install", "-r",
                                          "requirements-dev.txt"], cwd=directory)
            run(f"{project}-python-version", [executable, "--version"], cwd=directory)
            run(f"{project}-versions", [executable, "-m", "pip", "freeze"], cwd=directory)
            run(f"{project}-tests", [executable, "-m", "pytest", "-q"], cwd=directory)
            run(f"{project}-http", [executable, "tests/run_http_matrix.py"], cwd=directory)

        node = shutil.which("node")
        npm = shutil.which("npm.cmd" if os.name == "nt" else "npm")
        if not node or not npm:
            raise RuntimeError("Node and npm must be installed")
        cli = Path(node).parent / "node_modules/npm/bin/npm-cli.js"
        npm_command = [node, cli] if cli.is_file() else [npm]
        directory = root / "ecommerce-api-legacy"
        run("node-version", [node, "--version"])
        run("npm-version", [*npm_command, "--version"])
        if not args.skip_install:
            run("ecommerce-api-legacy-install", [*npm_command, "ci"], cwd=directory)
        run("ecommerce-api-legacy-tests", [*npm_command, "test"], cwd=directory)
        run("ecommerce-api-legacy-http", [*npm_command, "run", "test:http"], cwd=directory)
    except RuntimeError as error:
        print(error, file=sys.stderr)
        return 1
    print(f"PASS: all steps completed. Evidence: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
