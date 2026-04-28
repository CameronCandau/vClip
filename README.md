# OpIndex

`OpIndex` is a Linux-first command memory tool for markdown notes. It parses reusable command blocks from your notes, lets you search them from a launcher, and copies the selected command to the clipboard.

The current UI is optimized for `rofi` on X11, but the note format and CLI are useful independently of the launcher.

## What it does

- searches reusable commands from markdown files
- organizes sources into named workspaces
- supports quick workspace switching from a launcher
- shows source-document context while browsing
- lints notes against the OpIndex authoring standard
- copies selected commands to the clipboard

## Platform

`OpIndex` currently targets Linux. It expects one of:

- `rofi` for the interactive launcher flow
- `xclip`, `xsel`, or `wl-copy` for clipboard access

## Installation

### System dependencies

Debian or Ubuntu:

```bash
sudo apt install rofi xclip
```

Wayland clipboard support:

```bash
sudo apt install wl-clipboard
```

### Python package

The intended PyPI distribution name is `opindex`.

```bash
pipx install opindex
```

This installs the `opindex` command.

For local development:

```bash
pipx install .
```

## Quick start

Create a config:

```bash
opindex --create-config
```

Run the selector in the default workspace:

```bash
opindex
```

Open the workspace picker first:

```bash
opindex --workspace-menu
```

Search a specific workspace:

```bash
opindex --workspace oscp
```

Search all workspaces:

```bash
opindex --all
```

Browse by workspace, then document:

```bash
opindex --browse
```

## Configuration

The config file lives at:

```text
~/.config/opindex/config.yaml
```

Example:

```yaml
default_workspace: oscp

workspaces:
  oscp:
    directories:
      - "~/notes/OSCP-Methodology"
    files: []
    recursive: true
    file_patterns:
      - "*.md"
      - "*.markdown"

  cheatsheets:
    directories:
      - "~/notes/cheatsheets"
    files: []
    recursive: true
    file_patterns:
      - "*.md"
      - "*.markdown"

rofi:
  args: []
  use_markup: true
  max_lines: 15
  prompt: "Commands"
  window_width: 60
  element_height: 2

cache:
  enabled: true
  directory: null
  auto_cleanup: true

substitute_variables: false
variables: {}
```

## Markdown format

Minimal parseable format:

````markdown
# Azure CLI

## Login with device code
```bash
az login --use-device-code
```
````

`OpIndex` parses:

- `#` as the category
- `##` as the searchable task heading
- fenced code blocks as command content

Supported command block languages:

- empty language
- `bash`
- `sh`
- `shell`
- `powershell`
- `ps1`
- `cmd`
- `bat`
- `batch`

For the stricter durable-note format, see:

- [docs/opindex-note-standard.md](docs/opindex-note-standard.md)
- [docs/opindex-agent-skill-spec.md](docs/opindex-agent-skill-spec.md)

## Linting

Lint a specific note:

```bash
opindex --lint-files path/to/file.md
```

Lint the selected workspace sources:

```bash
opindex --lint-files
```

## CLI

Common commands:

```bash
opindex --help
opindex --list-workspaces
opindex --list-files
opindex --list-commands
opindex --clear-cache
opindex --config-path
```

## Development

Run tests:

```bash
python3 -m pytest tests/
```

Run the parser against a file:

```bash
python3 -m cmd_manager.parser test_data/sample.md
```

Lint a note during development:

```bash
python3 opindex --lint-files test_data/sample.md
```

## Publishing

The package is prepared for Trusted Publishing from GitHub Actions. See:

- [PUBLISHING.md](PUBLISHING.md)

Releases publish to PyPI from pushed tags in the form `v<semver>`.

## License

MIT
