# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
A Python CLI tool called "vclip" that parses markdown methodology files containing command snippets, provides a rofi-based fuzzy search interface, and copies selected commands to clipboard.

## Commands for Development

### Project Setup
```bash
# Install dependencies (create requirements.txt first)
pip install -r requirements.txt

# Install in development mode (after creating setup.py)
pip install -e .

# Run the tool
./vclip

# Or after installation
vclip
```

### Testing
```bash
# Run tests (create test files first)
python -m pytest tests/

# Run specific test
python -m pytest tests/test_parser.py

# Test with sample data
python -m cmd_manager.parser test_data/sample.md
```

## Architecture Overview

### Core Components
1. **parser.py**: Markdown parsing engine that extracts code blocks with metadata (tags, categories)
2. **rofi.py**: Interface layer for rofi integration and command selection
3. **clipboard.py**: Clipboard operations using xclip
4. **cache.py**: JSON-based caching system for parsed commands
5. **config.py**: YAML configuration management

### Expected Project Structure
```
vclip/
├── cmd_manager/           # Main package
│   ├── __init__.py
│   ├── parser.py         # Markdown parsing logic
│   ├── cache.py          # Cache management
│   ├── rofi.py          # Rofi interface
│   ├── clipboard.py     # Clipboard operations
│   └── config.py        # Configuration handling
├── config/
│   └── config.yaml      # Default configuration
├── test_data/
│   └── sample.md        # Test markdown file
├── tests/               # Test files
├── vclip                # Main executable script
├── requirements.txt
└── setup.py
```

### Data Flow
1. Parser extracts commands from markdown files with metadata
2. Cache stores parsed results as JSON for fast startup
3. Rofi displays commands in "description (tags)" format
4. Selected command is copied to clipboard via xclip
5. Support for variable substitution ($TARGET, $URL, etc.)

### Markdown Format
Expected input format for command files:
```markdown
# Category Name

## Command Description
<!-- tags: tag1, tag2, tag3 -->
```bash
command goes here
```

### Command Data Structure
Each parsed command should include:
- content: The actual command text
- description: Human-readable description
- tags: List of tags for filtering
- category: Section header from markdown
- source_file: Origin file path

## Implementation Priority
1. Start with parser.py and Command dataclass
2. Create basic CLI that parses test file
3. Add rofi integration
4. Add clipboard functionality
5. Implement caching system
6. Add configuration support