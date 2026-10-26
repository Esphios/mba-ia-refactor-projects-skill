import ctypes
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest


MODULE = Path(__file__).parents[1] / "processes.py"
spec = importlib.util.spec_from_file_location("delivery_processes", MODULE)
processes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(processes)


def alive(pid):
    if os.name == "nt":
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.restype = ctypes.c_void_p
        handle = kernel.OpenProcess(0x1000, False, pid)
        if not handle:
            return False
        try:
            code = ctypes.c_ulong()
            kernel.GetExitCodeProcess.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong)]
            if not kernel.GetExitCodeProcess(handle, ctypes.byref(code)):
                raise ctypes.WinError(ctypes.get_last_error())
            return code.value == 259
        finally:
            kernel.CloseHandle.argtypes = [ctypes.c_void_p]
            kernel.CloseHandle(handle)
    try:
        os.kill(pid, 0)
        status = Path(f"/proc/{pid}/status")
        return not (status.is_file() and "State:\tZ" in status.read_text())
    except ProcessLookupError:
        return False


class ProcessCleanup(unittest.TestCase):
    def test_timeout_stops_owned_launcher_and_child(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        with self.subTest("owned process cleanup"):
            path = Path(temporary.name)
            worker = path / "worker.py"
            worker.write_text(
                "import os, pathlib, subprocess, sys, time\n"
                "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(120)'])\n"
                "pathlib.Path('pids.txt').write_text(str(os.getpid())+' '+str(child.pid))\n"
                "time.sleep(120)\n", encoding="utf-8")
            with (path / "output.log").open("w", encoding="utf-8") as stream:
                with self.assertRaises(subprocess.TimeoutExpired):
                    processes.run_owned([sys.executable, str(worker)], cwd=path,
                                        env=os.environ.copy(), stream=stream, timeout=2)
            pids = [int(pid) for pid in (path / "pids.txt").read_text().split()]
            def cleanup():
                for pid in pids:
                    if alive(pid):
                        if os.name == "nt":
                            subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"],
                                           capture_output=True, timeout=15, check=False)
                        else:
                            os.kill(pid, 9)
            self.addCleanup(cleanup)
            deadline = time.monotonic() + 5
            while any(alive(pid) for pid in pids) and time.monotonic() < deadline:
                time.sleep(0.05)
            self.assertFalse(any(alive(pid) for pid in pids), f"Owned processes survived: {pids}")


if __name__ == "__main__":
    unittest.main()
