# vclip - Command Snippet Manager

A Python CLI tool that parses markdown files containing command snippets, provides a rofi-based fuzzy search interface, and copies selected commands to clipboard.

By default, `vclip` copies commands exactly as written. Variable substitution is optional and can be toggled from inside the rofi menu.

## Features

- 📝 **Markdown Parser**: Extract code blocks from markdown files
- 🔍 **Rofi Integration**: Launch rofi with parsed commands for fuzzy search
- 📋 **Clipboard Integration**: Copy selected commands using xclip/xsel/wl-copy
- 🚀 **Caching System**: Parse files once, cache results for fast subsequent loads
- ⚙️ **Configuration**: YAML config for paths, settings, and customization
- 🔧 **Multiple Commands**: Support for multiple code blocks under one heading

## Installation

### System Dependencies

```bash
# Install system dependencies (Ubuntu/Debian)
sudo apt install rofi xclip

# For Wayland users
sudo apt install wl-clipboard
```

### Install vclip

**Option 1: pipx (Recommended)**
```bash
# Install pipx if you don't have it
sudo apt update
sudo apt install pipx
pipx ensurepath

# Install vclip in isolated environment
pipx install .
```

**Option 2: Development Installation**
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install in development mode
pip install -e .
```

### Uninstall

```bash
# If installed with pipx
pipx uninstall vclip

# If installed with pip
pip uninstall vclip
```

## Quick Start

1. **Create configuration**:
   ```bash
   vclip --create-config
   ```

2. **Add your command files** to one of these locations:
   - `~/Documents/commands/`
   - `~/.local/share/vclip/`

3. **Run vclip**:
   ```bash
   vclip
   ```

## Markdown Format

Commands should be written in this format:

```markdown
# Category Name

## Command Description
```bash
command goes here
```

## Another Command
```
command without language specified (defaults to bash)
```
```

### Example

```markdown
# System Administration

## Check disk usage
```bash
df -h
```

## View large files
```bash
find /home -type f -size +100M -exec ls -lh {} \; | awk '{ print $9 ": " $5 }'
```

# Docker Commands

## View container logs
```bash
docker logs -f container_name
```
```

### Multiple Commands Per Heading

You can have multiple code blocks under one heading. They will be distinguished by their language label:

```markdown
## Enumerate SMB shares
```bash
netexec smb $IP --shares
```

```python
# Python alternative
from impacket import smbclient
```
```

In rofi, these appear as:
- `Enumerate SMB shares [bash]`
- `Enumerate SMB shares [python]`

If no language is specified, numbered labels are used:
- `Command Name [1]`
- `Command Name [2]`

## Configuration

Configuration file is located at `~/.config/vclip/config.yaml`:

```yaml
# Source configuration
sources:
  files: []
  directories:
    - "~/Documents/commands"
    - "~/.local/share/vclip"
  recursive: true
  file_patterns:
    - "*.md"
    - "*.markdown"

# Rofi interface configuration
rofi:
  args: []
  use_markup: true
  max_lines: 15
  prompt: "Commands"

# Cache configuration
cache:
  enabled: true
  directory: null  # Uses ~/.cache/vclip
  auto_cleanup: true

# Copy commands exactly as written by default
substitute_variables: false

# Optional variables for substitution when the mode is enabled
variables:
  # HOST: "10.10.10.10"
```

## Usage

```bash
# Show command selector
vclip

# Show help
vclip --help

# List all commands
vclip --list-commands

# List source files
vclip --list-files

# Clear cache
vclip --clear-cache

# Show config path
vclip --config-path
```

After selecting a command, it will be copied to your clipboard. Use `Ctrl+Shift+V` (or `Ctrl+V`) to paste it into your terminal.

The rofi list includes a `[Settings] Variable substitution: OFF/ON` entry. Select it to toggle substitution mode and persist that choice in your config.

## Testing

Run the verification script to check your installation:

```bash
python3 verify_installation.py
```

Run the test suite:

```bash
python3 -m pytest tests/
```

## Project Structure

```
vclip/
├── cmd_manager/          # Main package
│   ├── parser.py        # Markdown parsing logic
│   ├── rofi.py         # Rofi interface
│   ├── clipboard.py    # Clipboard operations
│   ├── cache.py        # Cache management
│   └── config.py       # Configuration handling
├── config/
│   └── config.yaml     # Default configuration
├── test_data/
│   └── sample.md       # Test markdown file
├── tests/              # Test files
├── vclip               # Main executable script
├── requirements.txt
└── setup.py
```

## License

MIT License
