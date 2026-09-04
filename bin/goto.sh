#!/usr/bin/env bash
set -euo pipefail

herdr_bin="${HERDR_BIN_PATH:-herdr}"

if ! command -v jq >/dev/null 2>&1; then
  echo "jq is required for agent-attention" >&2
  exit 1
fi

selection="$(
  "$herdr_bin" agent list | jq -r '
    .result.agents
    | map(select(.agent_status == "blocked" or .agent_status == "done"))
    | sort_by(
        if .agent_status == "blocked" then 0 else 1 end,
        -.state_change_seq
      )
    | if length > 0 then .[0] else empty end
    | if . == null or . == "" then empty else
        [
          .pane_id,
          .agent_status,
          (.terminal_title_stripped // .terminal_title // .pane_id)
        ] | @tsv
      end
  '
)"

if [[ -z "${selection:-}" ]]; then
  "$herdr_bin" notification show "Agent Attention" \
    --body "No agents need attention right now." \
    --sound none >/dev/null 2>&1 || true
  exit 0
fi

IFS=$'\t' read -r target status title <<<"$selection"

"$herdr_bin" agent focus "$target" >/dev/null

case "$status" in
  blocked)
    label="needs your response"
    sound="request"
    ;;
  done)
    label="finished"
    sound="done"
    ;;
  *)
    label="$status"
    sound="none"
    ;;
esac

"$herdr_bin" notification show "Agent Attention" \
  --body "${title}: ${label}" \
  --sound "$sound" >/dev/null 2>&1 || true
