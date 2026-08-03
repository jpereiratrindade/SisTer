#!/usr/bin/env python3
"""Create one governed lab Unix listener and exec sisterd with it activated."""

import os
import fcntl
from pathlib import Path
import socket
import sys


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: socket_activation_lab.py SOCKET_PATH EXECUTABLE")
    socket_path = Path(sys.argv[1])
    executable = Path(sys.argv[2])
    if not socket_path.is_absolute() or not executable.is_absolute():
        raise SystemExit("socket path and executable must be absolute")
    socket_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    if socket_path.exists():
        if not socket_path.is_socket():
            raise SystemExit(f"refusing to replace non-socket path: {socket_path}")
        socket_path.unlink()

    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(str(socket_path))
    os.chmod(socket_path, 0o660)
    listener.listen(256)
    duplicate = fcntl.fcntl(listener.fileno(), fcntl.F_DUPFD, 64)
    listener.close()
    os.dup2(duplicate, 3, inheritable=True)
    os.close(duplicate)

    environment = os.environ.copy()
    environment["LISTEN_PID"] = str(os.getpid())
    environment["LISTEN_FDS"] = "1"
    environment["LISTEN_FDNAMES"] = "sisterd-http"
    os.execve(str(executable), [str(executable)], environment)


if __name__ == "__main__":
    main()
