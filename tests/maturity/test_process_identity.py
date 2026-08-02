import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
IDENTITY = ROOT / "scripts" / "app" / "process_identity.py"
STOP = ROOT / "scripts" / "app" / "stop.sh"


class ProcessIdentityTests(unittest.TestCase):
    def setUp(self) -> None:
        environment = os.environ.copy()
        environment["SISTER_ENV"] = "ownership-test"
        self.process = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(30)"],
            cwd=ROOT,
            env=environment,
        )
        self.temporary = tempfile.TemporaryDirectory()
        self.pid_file = Path(self.temporary.name) / "process.pid"
        self.record(self.pid_file)

    def tearDown(self) -> None:
        if self.process.poll() is None:
            self.process.terminate()
            self.process.wait(timeout=5)
        self.temporary.cleanup()

    def command(self, action: str, pid_file: Path):
        return [
            sys.executable,
            str(IDENTITY),
            action,
            "--pid-file",
            str(pid_file),
            "--environment",
            "ownership-test",
            "--executable",
            sys.executable,
        ]

    def record(self, pid_file: Path) -> None:
        subprocess.run(
            self.command("record", pid_file) + ["--pid", str(self.process.pid)],
            cwd=ROOT,
            check=True,
        )

    def test_validates_pid_uid_executable_environment_and_start_time(self) -> None:
        completed = subprocess.run(
            self.command("validate", self.pid_file),
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertEqual(str(self.process.pid), completed.stdout.strip())
        self.assertEqual(0o600, self.pid_file.stat().st_mode & 0o777)

    def test_rejects_reused_or_tampered_identity(self) -> None:
        record = json.loads(self.pid_file.read_text())
        record["start_ticks"] += 1
        self.pid_file.write_text(json.dumps(record) + "\n", encoding="utf-8")
        os.chmod(self.pid_file, 0o600)
        completed = subprocess.run(
            self.command("validate", self.pid_file),
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(3, completed.returncode)
        self.assertIsNone(self.process.poll())

    def test_rejects_permissive_pid_file(self) -> None:
        os.chmod(self.pid_file, 0o644)
        completed = subprocess.run(
            self.command("validate", self.pid_file),
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(3, completed.returncode)
        self.assertIsNone(self.process.poll())

    def test_reports_stale_record_without_signaling_another_process(self) -> None:
        self.process.terminate()
        self.process.wait(timeout=5)
        completed = subprocess.run(
            self.command("validate", self.pid_file),
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(4, completed.returncode)

    def test_terminates_the_validated_process_through_pidfd(self) -> None:
        completed = subprocess.run(
            self.command("terminate", self.pid_file),
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertEqual(str(self.process.pid), completed.stdout.strip())
        self.process.wait(timeout=5)
        self.assertEqual(-signal.SIGTERM, self.process.returncode)

    def test_stop_refuses_pid_file_for_a_different_executable(self) -> None:
        governed_pid_file = ROOT / ".run" / "sisterd-ownership-test.pid"
        governed_pid_file.unlink(missing_ok=True)
        self.record(governed_pid_file)
        try:
            completed = subprocess.run(
                [str(STOP), "ownership-test"],
                cwd=ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(3, completed.returncode)
            self.assertIsNone(self.process.poll())
        finally:
            governed_pid_file.unlink(missing_ok=True)

    def test_stop_refuses_legacy_numeric_pid_file(self) -> None:
        governed_pid_file = ROOT / ".run" / "sisterd-ownership-test.pid"
        governed_pid_file.write_text(f"{self.process.pid}\n", encoding="utf-8")
        os.chmod(governed_pid_file, 0o600)
        try:
            completed = subprocess.run(
                [str(STOP), "ownership-test"],
                cwd=ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(3, completed.returncode)
            self.assertIsNone(self.process.poll())
        finally:
            governed_pid_file.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
