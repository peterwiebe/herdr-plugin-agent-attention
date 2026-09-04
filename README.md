# Agent Attention

A Herdr plugin that jumps to the agent that most recently finished or needs your input.

## What it does

Press a hotkey and Herdr focuses the highest-priority attention agent:

1. `blocked` — waiting for approval or a response
2. `done` — finished in the background and not yet seen

Agents are ranked by status first, then by most recent state change.

The action also shows a short Herdr notification so you get feedback even when you were already on the target pane.

## Requirements

- Herdr 0.7.5+
- `jq` on your `PATH`

## Install

```bash
herdr plugin install peterwiebe/herdr-plugin-agent-attention
```

## Keybinding

Add a binding to `~/.config/herdr/config.toml`:

```toml
[[keys.command]]
key = "ctrl+alt+a"
type = "shell"
command = '''bash "$HOME/.herdr/plugins/data/agent-attention/bin/goto.sh"'''
description = "go to agent needing attention"
```

After a GitHub install, Herdr stores the plugin under its managed plugin data directory. To use a stable path in your config, run:

```bash
herdr plugin config-dir agent-attention
```

Then point the binding at `bin/goto.sh` inside that directory.

Reload config:

```bash
herdr server reload-config
```

Prefix bindings also work:

```toml
[[keys.command]]
key = "prefix+shift+a"
type = "shell"
command = '''bash "<config-dir>/bin/goto.sh"'''
description = "go to agent needing attention"
```

## Actions

| Action | Description |
| --- | --- |
| `agent-attention.goto` | Focus the top attention agent |
| `agent-attention.apply-view` | Sort the Agents panel by attention |
| `agent-attention.clear-view` | Reset the Agents panel sort |

Example:

```bash
herdr plugin action invoke agent-attention.goto
```

## Optional: cycle attention agents

Bind Herdr's built-in agent navigation keys and apply the attention view once:

```toml
next_agent = "ctrl+alt+]"
previous_agent = "ctrl+alt+["
```

```bash
herdr plugin action invoke agent-attention.apply-view
```

## Development

```bash
herdr plugin link /path/to/herdr-plugin-agent-attention
herdr plugin action invoke agent-attention.goto
```

## License

MIT
