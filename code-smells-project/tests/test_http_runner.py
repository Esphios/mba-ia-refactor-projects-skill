"""The real-runner result includes successful process AND file cleanup."""
import json
import subprocess
import sys
from pathlib import Path


def test_http_runner_owns_process_and_releases_database_before_cleanup():
    script=Path(__file__).with_name('run_http_matrix.py')
    result=subprocess.run([sys.executable,str(script)],capture_output=True,text=True,
        encoding='utf-8',timeout=60)
    assert result.returncode == 0, result.stderr
    report=json.loads(result.stdout)
    assert report['result']=='PASS' and report['contracts']==19
    assert all(process['stopped'] for process in report['processes'])
    assert report['cleanup']=='processes stopped and disposable directory removed'
