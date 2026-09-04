#!/usr/bin/env python3
"""Apply a transient Agents-panel view sorted by attention."""

import json
import os
import socket
import sys

SOURCE = "plugin:agent-attention"

PARAMS = {
    "source": SOURCE,
    "label": "attention",
    "filter": {
        "op": "in",
        "field": "status",
        "values": ["blocked", "done"],
    },
    "sort": [
        {"field": "attention", "order": "desc"},
        {"field": "state_change_seq", "order": "desc"},
    ],
}


def state_file():
    state_dir = os.environ.get("HERDR_PLUGIN_STATE_DIR")
    return os.path.join(state_dir, "view.json") if state_dir else None


def send(method, params):
    path = os.environ.get("HERDR_SOCKET_PATH")
    if not path:
        sys.stderr.write("Could not send to herdr (no socket path)\n")
        return False

    request = json.dumps({"id": "agent-attention", "method": method, "params": params})

    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(2.0)
        sock.connect(path)
        sock.sendall(request.encode("utf-8") + b"\n")

        buffer = b""
        while b"\n" not in buffer:
            chunk = sock.recv(4096)
            if not chunk:
                break
            buffer += chunk
        sock.close()
    except OSError:
        sys.stderr.write("Could not send to herdr\n")
        return False

    line = buffer.split(b"\n", 1)[0]
    try:
        response = json.loads(line.decode("utf-8"))
    except ValueError:
        sys.stderr.write("Could not send to herdr (malformed reply)\n")
        return False

    if isinstance(response, dict) and "error" in response:
        error = response.get("error")
        message = error.get("message") if isinstance(error, dict) else error
        sys.stderr.write(f"herdr rejected the request: {message}\n")
        return False

    return True


def main():
    operation = sys.argv[1] if len(sys.argv) > 1 else ""
    state_path = state_file()

    if operation == "set":
        if not send("agent.view.set", PARAMS):
            return 1
        if state_path:
            with open(state_path, "w", encoding="utf-8") as handle:
                json.dump(PARAMS, handle)
        return 0

    if operation == "clear":
        if not send("agent.view.clear", {"source": SOURCE}):
            return 1
        if state_path and os.path.exists(state_path):
            os.remove(state_path)
        return 0

    if operation == "restore":
        if not state_path or not os.path.exists(state_path):
            return 0
        try:
            with open(state_path, encoding="utf-8") as handle:
                send("agent.view.set", json.load(handle))
        except (OSError, ValueError):
            pass
        return 0

    sys.stderr.write("usage: view.py {set|clear|restore}\n")
    return 1


if __name__ == "__main__":
    sys.exit(main())
