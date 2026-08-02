#!/usr/bin/env python3
import argparse
import json
import os
from pathlib import Path
import stat
import signal
import sys
import tempfile
import time


SCHEMA = "sister.process-identity/1.0.0"


def positive_pid(raw: str) -> int:
    value = int(raw)
    if value <= 0:
        raise ValueError("PID must be positive")
    return value


def process_start_ticks(pid: int) -> int:
    raw = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8")
    closing = raw.rfind(")")
    if closing < 0:
        raise ValueError("invalid process stat record")
    fields = raw[closing + 2 :].split()
    if len(fields) <= 19:
        raise ValueError("invalid process stat record")
    return int(fields[19])


def process_environment(pid: int) -> dict[str, str]:
    values = {}
    for entry in Path(f"/proc/{pid}/environ").read_bytes().split(b"\0"):
        if not entry or b"=" not in entry:
            continue
        name, value = entry.split(b"=", 1)
        values[name.decode("utf-8", errors="strict")] = value.decode(
            "utf-8", errors="strict"
        )
    return values


def process_command(pid: int) -> Path:
    command = Path(f"/proc/{pid}/cmdline").read_bytes().split(b"\0", 1)[0]
    if not command:
        raise ValueError("process command line is empty")
    decoded = Path(command.decode("utf-8", errors="strict"))
    if decoded.is_absolute():
        return decoded.resolve()
    working_directory = Path(os.readlink(f"/proc/{pid}/cwd"))
    return (working_directory / decoded).resolve()


def observe(pid: int, expected_executable: Path, environment: str) -> dict:
    process = Path(f"/proc/{pid}")
    process_stat = process.stat()
    if process_stat.st_uid != os.geteuid():
        raise ValueError("process belongs to a different user")
    actual_executable = Path(os.readlink(process / "exe")).resolve()
    if actual_executable != expected_executable:
        raise ValueError("process executable does not match sisterd")
    if process_command(pid) != expected_executable:
        raise ValueError("process command line does not match sisterd")
    if process_environment(pid).get("SISTER_ENV") != environment:
        raise ValueError("process environment does not match the PID file")
    return {
        "schema": SCHEMA,
        "pid": pid,
        "uid": os.geteuid(),
        "environment": environment,
        "executable": str(expected_executable),
        "start_ticks": process_start_ticks(pid),
    }


def write_private_atomic(path: Path, payload: dict) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, ensure_ascii=True, separators=(",", ":"))
            stream.write("\n")
        os.replace(temporary, path)
        os.chmod(path, 0o600)
    finally:
        temporary.unlink(missing_ok=True)


def read_record(path: Path, expected_executable: Path, environment: str) -> dict:
    metadata = path.lstat()
    if not stat.S_ISREG(metadata.st_mode) or path.is_symlink():
        raise ValueError("PID file must be a regular non-symlink file")
    if metadata.st_uid != os.geteuid() or stat.S_IMODE(metadata.st_mode) & 0o077:
        raise ValueError("PID file ownership or permissions are unsafe")
    record = json.loads(path.read_text(encoding="utf-8"))
    required = {"schema", "pid", "uid", "environment", "executable", "start_ticks"}
    if not isinstance(record, dict) or set(record) != required:
        raise ValueError("PID file structure is invalid")
    if record["schema"] != SCHEMA or record["uid"] != os.geteuid():
        raise ValueError("PID file identity is invalid")
    if record["environment"] != environment or record["executable"] != str(expected_executable):
        raise ValueError("PID file does not belong to this environment or worktree")
    if type(record["pid"]) is not int or record["pid"] <= 0:
        raise ValueError("PID file contains an invalid PID")
    if type(record["start_ticks"]) is not int or record["start_ticks"] <= 0:
        raise ValueError("PID file contains an invalid start time")
    return record


def record_process(args: argparse.Namespace) -> int:
    pid = positive_pid(args.pid)
    expected = args.executable.resolve(strict=True)
    deadline = time.monotonic() + args.wait_seconds
    last_error = None
    while time.monotonic() < deadline:
        try:
            payload = observe(pid, expected, args.environment)
            write_private_atomic(args.pid_file, payload)
            return 0
        except (FileNotFoundError, ProcessLookupError, ValueError, OSError) as error:
            last_error = error
            time.sleep(0.02)
    raise ValueError(f"could not record started sisterd identity: {last_error}")


def validate_process(args: argparse.Namespace) -> int:
    expected = args.executable.resolve(strict=True)
    record = read_record(args.pid_file, expected, args.environment)
    pid = record["pid"]
    if not Path(f"/proc/{pid}").exists():
        return 4
    observed = observe(pid, expected, args.environment)
    if observed != record:
        raise ValueError("PID was reused or process identity changed")
    print(pid)
    return 0


def terminate_process(args: argparse.Namespace) -> int:
    expected = args.executable.resolve(strict=True)
    record = read_record(args.pid_file, expected, args.environment)
    pid = record["pid"]
    try:
        pidfd = os.pidfd_open(pid)
    except ProcessLookupError:
        return 4
    try:
        observed = observe(pid, expected, args.environment)
        if observed != record:
            raise ValueError("PID was reused or process identity changed")
        signal.pidfd_send_signal(pidfd, signal.SIGTERM)
    finally:
        os.close(pidfd)
    print(pid)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("record", "validate", "terminate"):
        child = subparsers.add_parser(command)
        child.add_argument("--pid-file", type=Path, required=True)
        child.add_argument("--environment", required=True)
        child.add_argument("--executable", type=Path, required=True)
        if command == "record":
            child.add_argument("--pid", required=True)
            child.add_argument("--wait-seconds", type=float, default=2.0)
    args = parser.parse_args()
    if args.command == "record":
        return record_process(args)
    if args.command == "terminate":
        return terminate_process(args)
    return validate_process(args)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (json.JSONDecodeError, OSError, ValueError) as error:
        print(f"process identity error: {error}", file=sys.stderr)
        sys.exit(3)
