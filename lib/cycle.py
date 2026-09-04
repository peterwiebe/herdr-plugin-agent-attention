#!/usr/bin/env python3
"""Cycle through blocked and finished-unseen agents by view history."""

import json
import os
import subprocess
import sys
import time

ATTENTION_STATUSES = {"blocked", "done"}
STATE_FILENAME = "view-history.json"


def herdr_bin():
    return os.environ.get("HERDR_BIN_PATH", "herdr")


def state_path():
    state_dir = os.environ.get("HERDR_PLUGIN_STATE_DIR")
    if not state_dir:
        return None
    return os.path.join(state_dir, STATE_FILENAME)


def load_state():
    path = state_path()
    if not path or not os.path.exists(path):
        return {"viewed_at": {}}
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        return {"viewed_at": {}}
    if not isinstance(data.get("viewed_at"), dict):
        data["viewed_at"] = {}
    return data


def save_state(state):
    path = state_path()
    if not path:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2, sort_keys=True)


def herdr_json(args):
    result = subprocess.run(
        [herdr_bin(), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "herdr command failed"
        raise RuntimeError(message)
    return json.loads(result.stdout)


def attention_agents():
    payload = herdr_json(["agent", "list"])
    agents = payload.get("result", {}).get("agents", [])
    return [agent for agent in agents if agent.get("agent_status") in ATTENTION_STATUSES]


def current_pane_id():
    payload = herdr_json(["pane", "current"])
    pane = payload.get("result", {}).get("pane") or {}
    return pane.get("pane_id")


def status_rank(status):
    return 0 if status == "blocked" else 1


def sort_key(agent, viewed_at):
    pane_id = agent.get("pane_id", "")
    viewed = viewed_at.get(pane_id, 0)
    return (
        status_rank(agent.get("agent_status")),
        viewed,
        -int(agent.get("state_change_seq") or 0),
    )


def prune_history(state, agents):
    live_ids = {agent.get("pane_id") for agent in agents if agent.get("pane_id")}
    state["viewed_at"] = {
        pane_id: timestamp
        for pane_id, timestamp in state.get("viewed_at", {}).items()
        if pane_id in live_ids
    }


def record_view(state, pane_id, timestamp=None):
    if not pane_id:
        return
    state.setdefault("viewed_at", {})[pane_id] = int(timestamp or time.time() * 1000)


def pick_next(agents, viewed_at, current_pane):
    ordered = sorted(agents, key=lambda agent: sort_key(agent, viewed_at))
    pane_ids = [agent.get("pane_id") for agent in ordered]
    if current_pane in pane_ids:
        index = pane_ids.index(current_pane)
        return ordered[(index + 1) % len(ordered)]
    return ordered[0]


def agent_title(agent):
    return (
        agent.get("terminal_title_stripped")
        or agent.get("terminal_title")
        or agent.get("pane_id")
        or "agent"
    )


def notify(title, body, sound):
    subprocess.run(
        [herdr_bin(), "notification", "show", title, "--body", body, "--sound", sound],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def goto():
    agents = attention_agents()
    if not agents:
        notify("Agent Attention", "No agents need attention right now.", "none")
        return 0

    state = load_state()
    prune_history(state, agents)
    viewed_at = state.get("viewed_at", {})
    current_pane = current_pane_id()
    target = pick_next(agents, viewed_at, current_pane)

    pane_id = target.get("pane_id")
    if not pane_id:
        notify("Agent Attention", "No agent pane could be resolved.", "none")
        return 1

    herdr_json(["agent", "focus", pane_id])
    record_view(state, pane_id)
    save_state(state)

    status = target.get("agent_status", "idle")
    if status == "blocked":
        label = "needs your response"
        sound = "request"
    elif status == "done":
        label = "finished"
        sound = "done"
    else:
        label = status
        sound = "none"

    ordered = sorted(agents, key=lambda agent: sort_key(agent, viewed_at))
    position = next(
        (index + 1 for index, agent in enumerate(ordered) if agent.get("pane_id") == pane_id),
        1,
    )
    count = len(ordered)
    notify(
        "Agent Attention",
        f"{agent_title(target)}: {label} ({position}/{count})",
        sound,
    )
    return 0


def record_focus():
    pane_id = pane_id_from_event() or current_pane_id()
    if not pane_id:
        return 0

    state = load_state()
    record_view(state, pane_id)
    prune_history(state, attention_agents())
    save_state(state)
    return 0


def pane_id_from_event():
    raw = os.environ.get("HERDR_PLUGIN_EVENT_JSON")
    if not raw:
        return None
    try:
        event = json.loads(raw)
    except ValueError:
        return None

    data = event.get("data") if isinstance(event.get("data"), dict) else event
    pane = data.get("pane") if isinstance(data.get("pane"), dict) else {}
    return data.get("pane_id") or data.get("focused_pane_id") or pane.get("pane_id")


def main():
    command = sys.argv[1] if len(sys.argv) > 1 else "goto"
    if command == "goto":
        try:
            return goto()
        except RuntimeError as error:
            print(str(error), file=sys.stderr)
            return 1
    if command == "record-focus":
        try:
            return record_focus()
        except RuntimeError:
            return 0
    print(f"usage: {sys.argv[0]} {{goto|record-focus}}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
