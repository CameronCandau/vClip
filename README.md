# vclip - Command Snippet Manager

A Python CLI tool that parses markdown files containing command snippets, provides a rofi-based fuzzy search interface, and copies selected commands to clipboard with variable substitution support.

## Features

- 📝 **Markdown Parser**: Extract code blocks from markdown files with metadata support
- 🔍 **Rofi Integration**: Launch rofi with parsed commands for fuzzy search
- 📋 **Clipboard Integration**: Copy selected commands using xclip/xsel/wl-copy
- 🚀 **Caching System**: Parse files once, cache results for fast subsequent loads
- ⚙️ **Configuration**: YAML config for paths, settings, and customization
- 🔧 **Variable Substitution**: Support for variables like `$TARGET`, `$URL` in commands

## Installation

### System Dependencies

```bash
# Install system dependencies (Ubuntu/Debian)
sudo apt install rofi xclip

# For Wayland users
sudo apt install wl-clipboard

# For auto-paste functionality (optional)
sudo apt install xdotool  # X11 auto-paste
# OR for Wayland
sudo apt install wtype    # Wayland auto-paste
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
<!-- tags: tag1, tag2, tag3 -->
```bash
command goes here
```

### Example

```markdown
# System Administration

## Check disk usage
<!-- tags: system, disk, monitoring -->
```bash
df -h
```

## View large files
<!-- tags: system, files, cleanup -->
```bash
find /home -type f -size +100M -exec ls -lh {} \; | awk '{ print $9 ": " $5 }'
```

# Docker Commands

## View container logs
<!-- tags: docker, logs, debugging -->
```bash
docker logs -f $CONTAINER_NAME
```
```

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


# Variable definitions
variables:
  TARGET: "192.168.1.1"
  USERNAME: "admin"
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

# Run without prompting for missing variables (ideal for keyboard shortcuts)
vclip --no-prompt

# Auto-paste commands directly to active window
vclip --auto-paste

# Combine for perfect keyboard shortcut (recommended)
vclip --auto-paste --no-prompt
```

After selecting a command, it will be copied to your clipboard. Use `Ctrl+Shift+V` (or `Ctrl+V`) to paste it into your terminal.

## Variable Substitution

Commands can contain variables in the format `$VARIABLE_NAME`. When you select a command with variables:

1. vclip first checks for predefined variables in your config
2. Prompts you for any missing variables
3. Substitutes all variables before copying to clipboard

Example:
```bash
# Command in markdown
ssh $USER@$HOST -p $PORT

# After substitution
ssh admin@192.168.1.1 -p 2222
```

### Non-interactive Mode

Use `--no-prompt` when running from keyboard shortcuts or scripts. This mode:
- Only substitutes variables defined in your config file
- Leaves undefined variables as-is (e.g., `$UNDEFINED_VAR` remains unchanged)
- Never prompts for input, making it perfect for keyboard shortcuts

## Keyboard Shortcuts & Auto-Paste

### Manual Paste (Copy to Clipboard Only)
```bash
# Just copy to clipboard
vclip --no-prompt
```

### Auto-Paste (Recommended)
```bash
# Copy and automatically paste to active window
vclip --auto-paste --no-prompt
```

### Setting Up Keyboard Shortcuts

**i3 Window Manager:**
```
# Add to ~/.config/i3/config
bindsym $mod+space exec vclip --auto-paste --no-prompt
```

**GNOME/Ubuntu:**
- Settings → Keyboard → Custom Shortcuts
- Command: `vclip --auto-paste --no-prompt`

**KDE:**
- System Settings → Shortcuts → Custom Shortcuts
- Command: `vclip --auto-paste --no-prompt`

### Platform Support
- **Linux X11**: xdotool, fallback to basic Ctrl+V
- **Linux Wayland**: wtype
- **macOS**: AppleScript (Cmd+V)
- **Windows**: PowerShell SendKeys (Ctrl+V)

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