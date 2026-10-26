"""Run owned commands and terminate their process tree on timeout/interruption."""

import os
import signal
import subprocess


def run_owned(command, *, cwd, env, stream, timeout):
    options = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {
        "start_new_session": True}
    process = subprocess.Popen(command, cwd=cwd, env=env, stdout=stream,
                               stderr=subprocess.STDOUT, **options)
    stream.write(f"Owned process PID: {process.pid}\n")
    stream.flush()

    def terminate_tree():
        if os.name == "nt":
            # The launcher is still alive: target only this known, owned PID.
            terminated = subprocess.run(
                [os.path.join(os.environ.get("SystemRoot", r"C:\Windows"),
                              "System32", "taskkill.exe"),
                 "/PID", str(process.pid), "/T", "/F"],
                stdout=stream, stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW, timeout=30, check=False)
            if terminated.returncode and process.poll() is None:
                raise RuntimeError(f"Cannot terminate owned process tree {process.pid}")
        else:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        process.wait(timeout=30)

    try:
        return process.wait(timeout=timeout)
    except (subprocess.TimeoutExpired, KeyboardInterrupt):
        terminate_tree()
        raise
