# softwareobservatory

CLI and MCP server for querying the [Software
Observatory](https://softwareobservatory.com) catalog: 56 "epistemic sensors"
for software correctness, organized into 11 families. The full catalog ships
inside the package, so every command works offline.

Built to be driven by agents as well as humans: stdout is JSON whenever it is
piped (or `--json` is passed), and `softwareobservatory mcp` speaks the Model
Context Protocol over stdio.

## Usage

```console
$ npx softwareobservatory list --family structural
$ npx softwareobservatory get SO-003
$ npx softwareobservatory search mutation
$ npx softwareobservatory suggest "our tests pass but bugs still ship"
$ npx softwareobservatory gaps "how do I know my ai-generated code is safe"
$ npx softwareobservatory stack linter,SO-003,canary-analysis
$ npx softwareobservatory values oracle
```

## Commands

| Command | Description |
|---------|-------------|
| `list [--family <slug>]` | List sensors, optionally within one family. |
| `families` | List the 11 sensor families with counts. |
| `get <id\|slug\|title>` | One sensor in full: frontmatter, entry text, related entries. |
| `search <term...>` | Substring search over titles and entry text, ranked. |
| `values <field>` | Distinct values of a frontmatter field (`oracle`, `latency`, `type`, `stack_level`, ...). |
| `suggest <question...>` | Ranked sensors relevant to a plain-language concern. |
| `gaps <question...>` | Like `suggest`, but only the first result from each newly covered family. |
| `stack <id,slug,...>` | Family/stack coverage report for a sensor set, with recommendations. |
| `mcp` | Run an MCP (stdio JSON-RPC) server. |
| `version` | CLI and dataset versions. |

## Flags

- `--json`: machine-readable output. This is the default when stdout is not a
  TTY, so piping into `jq` or an agent harness just works.
- `--plain`: force human-readable output.

## MCP server

```console
$ npx softwareobservatory mcp
```

Tools exposed: `list_families`, `list_sensors`, `get_sensor`,
`suggest_sensors`, `stack_coverage`. Every sensor is also available as an MCP
resource at `softwareobservatory://sensor/<slug>`, and the family list at
`softwareobservatory://families`.

Example MCP client config (Claude Code, Crush, etc.):

```json
{
  "mcpServers": {
    "softwareobservatory": {
      "command": "npx",
      "args": ["-y", "softwareobservatory", "mcp"]
    }
  }
}
```

## Data

`data/sensors.json` is generated from the site's markdown sources by
`scripts/export_cli_data.py` (which `scripts/build.py` runs on every build) and
committed so the package can be published straight from the repo. Dataset
schema is versioned (`version` field); the CLI prints it via `version`.
