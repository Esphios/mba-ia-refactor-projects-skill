"""Reproduce tests and real HTTP boots in a checkout using disposable data."""

import argparse
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import tempfile
import time
from urllib.request import urlopen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path)
    parser.add_argument("--skip-install", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    output = args.output or root / "reports/evidence/reproduction.log"
    output.parent.mkdir(parents=True, exist_ok=True)
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    with output.open("w", encoding="utf-8") as log:
        def run(command, cwd, env=None):
            log.write(f"\n$ {' '.join(map(str, command))}\n")
            log.flush()
            completed = subprocess.run(list(map(str, command)), cwd=cwd, env=env,
                                       stdout=log, stderr=subprocess.STDOUT,
                                       creationflags=flags, timeout=600)
            log.write(f"exit={completed.returncode}\n")
            log.flush()
            if completed.returncode:
                raise RuntimeError(f"Failed: {command}; see {output}")

        def python_for(project):
            candidates = [project / name for name in (".venv-reproduce", ".venv-refactor", ".venv")]
            suffix = Path("Scripts/python.exe") if os.name == "nt" else Path("bin/python")
            environment = next((candidate for candidate in candidates if (candidate / suffix).exists()), candidates[0])
            if not (environment / suffix).exists():
                run([sys.executable, "-m", "venv", environment], project)
            python = environment / suffix
            if not args.skip_install:
                run([python, "-m", "pip", "install", "-r", "requirements-dev.txt"], project)
            run([python, "--version"], project)
            return python

        first = root / "code-smells-project"
        python = python_for(first)
        run([python, "-m", "pytest", "-q"], first)
        with tempfile.TemporaryDirectory(prefix="delivery-http-") as scratch:
            env = os.environ.copy()
            env.update(SECRET_KEY=secrets.token_urlsafe(36), DATABASE=str(Path(scratch) / "store.db"),
                       DEMO_ADMIN_PASSWORD=secrets.token_urlsafe(18),
                       DEMO_CUSTOMER_PASSWORD=secrets.token_urlsafe(18),
                       DEMO_SECOND_CUSTOMER_PASSWORD=secrets.token_urlsafe(18), HOST="127.0.0.1",
                       LEGACY_PASSWORD_CUTOFF="2099-01-01T00:00:00+00:00")
            with socket.socket() as available:
                available.bind(("127.0.0.1", 0))
                port = available.getsockname()[1]
            env.update(PORT=str(port), BASE_URL=f"http://127.0.0.1:{port}")
            run([python, "-m", "flask", "--app", "app", "init-db"], first, env)
            run([python, "-m", "flask", "--app", "app", "seed-demo"], first, env)
            log.write("\n$ python app.py (disposable database, loopback, debug disabled)\n")
            log.flush()
            process = subprocess.Popen([str(python), "app.py"], cwd=first, env=env,
                                       stdout=log, stderr=subprocess.STDOUT, creationflags=flags)
            try:
                deadline = time.monotonic() + 20
                while time.monotonic() < deadline:
                    if process.poll() is not None:
                        raise RuntimeError("Project 1 exited before readiness")
                    try:
                        with urlopen(env["BASE_URL"] + "/health", timeout=1) as response:
                            if response.status == 200:
                                break
                    except OSError:
                        time.sleep(0.1)
                else:
                    raise RuntimeError("Project 1 readiness timed out")
                run([python, "tests/run_http_matrix.py"], first, env)
            finally:
                if os.name == 'nt' and process.poll() is None:
                    # Windows venv launchers can spawn a real Python child. Stop
                    # only the process tree owned by this runner, before deleting
                    # its temporary database/logs.
                    subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                   creationflags=flags, timeout=15, check=False)
                elif process.poll() is None:
                    process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=10)

        second = root / "ecommerce-api-legacy"
        # npm is a .cmd shim on Windows; resolve its real CLI for shell-free execution.
        import shutil
        node = shutil.which("node")
        npm = shutil.which("npm")
        if not node or not npm:
            raise RuntimeError("Node and npm must be on PATH")
        npm_cli = Path(npm).parent / "node_modules/npm/bin/npm-cli.js"
        npm_command = [node, str(npm_cli)] if npm_cli.exists() else [npm]
        run([node, "--version"], second)
        if not args.skip_install:
            run(npm_command + ["ci"], second)
        run(npm_command + ["test"], second)
        run(npm_command + ["run", "test:http"], second)

        third = root / "task-manager-api"
        python = python_for(third)
        run([python, "-m", "pytest", "-q"], third)
        run([python, "tests/run_http_matrix.py"], third)
        run([sys.executable, "scripts/validate-delivery.py", "--root", root], root)
        log.write("\nPASS: three suites, three real boots and complete HTTP matrices; delivery structure valid.\n")
    print(f"PASS: {output}")


if __name__ == "__main__":
    main()
