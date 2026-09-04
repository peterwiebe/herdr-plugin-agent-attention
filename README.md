# Agent Attention

A Herdr plugin that cycles through agents that finished or need your input.

## What it does

Press a hotkey to cycle through attention agents:

1. `blocked` — waiting for approval or a response
2. `done` — finished in the background and not yet seen

Within each group, the plugin cycles in view order:

- Agents you have not visited recently come first
- Pressing the hotkey again moves to the next agent in the ring
- `blocked` agents stay ahead of `done` agents

The plugin tracks pane focus history automatically, including when you click an agent in the sidebar, so the cycle reflects what you have actually looked at.

Each jump also shows a short Herdr notification like `Agent Name: finished (2/4)`.

## Requirements

- Herdr 0.7.5+
- Python 3

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
command = '''bash "$HOME/Development/herdr-plugin-agent-attention/bin/goto.sh"'''
description = "cycle attention agents"
```

For a GitHub install, resolve the plugin path with:

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
description = "cycle attention agents"
```

## Actions

| Action | Description |
| --- | --- |
| `agent-attention.goto` | Cycle to the next attention agent |
| `agent-attention.apply-view` | Sort the Agents panel by attention |
| `agent-attention.clear-view` | Reset the Agents panel sort |

Example:

```bash
herdr plugin action invoke agent-attention.goto
```

## Optional: sidebar navigation

You can also bind Herdr's built-in agent navigation keys and apply the attention view once:

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
