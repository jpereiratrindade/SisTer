#!/usr/bin/env python3
import os
import fcntl
import sys


def main():
    if len(sys.argv) < 3:
        raise SystemExit("usage: socket_activation_launcher.py FD[,FD...] EXECUTABLE")
    sources = [int(value) for value in sys.argv[1].split(",") if value]
    duplicates = [fcntl.fcntl(source, fcntl.F_DUPFD, 64) for source in sources]
    try:
        for index, duplicate in enumerate(duplicates):
            os.dup2(duplicate, 3 + index, inheritable=True)
    finally:
        for duplicate in duplicates:
            os.close(duplicate)

    environment = os.environ.copy()
    environment["LISTEN_PID"] = environment.get("TEST_LISTEN_PID", str(os.getpid()))
    environment["LISTEN_FDS"] = environment.get("TEST_LISTEN_FDS", str(len(sources)))
    environment["LISTEN_FDNAMES"] = environment.get(
        "TEST_LISTEN_FDNAMES", ":".join("sisterd-http" for _ in sources)
    )
    os.execve(sys.argv[2], [sys.argv[2]], environment)


if __name__ == "__main__":
    main()
