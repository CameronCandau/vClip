# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**vclip** is a Python CLI tool for penetration testers that parses markdown methodology files containing command snippets, provides a rofi-based fuzzy search interface with live preview, and copies selected commands to clipboard. Built for the OSCP methodology by parsing 27 markdown files into 602 unique, deduplicated commands.

**Current Version**: 0.1.0 (Production-ready for lab work)
**Installation**: pipx (isolated virtual environment)
**Primary Use Case**: Fast command access during penetration testing engagements

---

## Current Status (October 2025)

### ✅ What's Working

**Core Functionality:**
- ✅ Parses 27 markdown files from Veilcat-OSCP-Methodology
- ✅ 602 unique commands (deduplicated from original 647)
- ✅ Smart deduplication: identical content removed, same description disambiguated
- ✅ Two-line rofi display: **Bold description** with command preview below
- ✅ Command previews always visible (even during fuzzy search)
- ✅ Correct command-to-clipboard mapping (fixed index bug)
- ✅ 60% screen width rofi window for better readability
- ✅ JSON caching for fast startup (~instant with cache)
- ✅ Configurable via YAML in config/config.yaml

**Deduplication Logic:**
1. Commands with identical content hash → merged (keep first)
2. Multiple commands with same description in SAME file → numbered (#1, #2, #3)
3. Same description across DIFFERENT files → source file added to description
   - Example: "Crack ASREPRoast hashes (Active Directory Attack Chain)"

**Search Capabilities:**
- Case-insensitive fuzzy matching
- Searches both description AND command content
- Tokenized search (can search "nmap min rate" to find "nmap --min-rate")
- Trade-off: Can't search exact hyphens (e.g., "--min-rate" won't match, but "min rate" will)

### 🐛 Known Issues & Behavior

**Hyphen Search Limitation:**
- Rofi tokenizes on hyphens by default (treats `--min-rate` as separate tokens)
- **Workaround**: Search without hyphens: `min rate` instead of `--min-rate`
- **Reason**: Disabling tokenization breaks fuzzy matching (higher priority feature)

**Variable Substitution Not Implemented:**
- Commands contain `$IP`, `$TARGET`, `$DOMAIN` variables
- Currently copied literally - user must manually replace
- **Status**: Highest priority future feature (see Roadmap below)

### 🔧 Recent Fixes (This Session)

1. **Fixed rofi index mismatch bug** - Commands were showing wrong content
   - Root cause: Two-line format created 1204 rofi lines but code expected 602
   - Solution: Divide rofi line index by 2 → correct command index

2. **Fixed command preview visibility** - Preview disappeared during search
   - Root cause: Newline separator treated each line as separate rofi entry
   - Solution: Use ASCII Unit Separator (\x1f) to keep two lines together

3. **Eliminated empty commands** - 4 commands had no content (only comments)
   - Solution: Filter out code blocks with only whitespace/comments

4. **Eliminated duplicate descriptions** - 25 duplicates reduced to 0
   - Solution: Multi-pass deduplication with intelligent disambiguation

5. **Increased rofi window size** - Text was cut off
   - Solution: 60% width, 2-line element height, scrollbar enabled

---

## Installation & Usage

### Installation (Production)

```bash
# Install via pipx (recommended - isolated environment)
cd /home/exis/code/vclip
pipx install .

# Verify installation
which vclip  # Should show: /home/exis/.local/bin/vclip
vclip --version  # Should show: vclip 0.1.0
```

### Development Workflow

```bash
# After making code changes:
pipx uninstall vclip && pipx install .

# Clear cache to force reparse:
vclip --clear-cache

# Test changes:
vclip
```

### Usage

```bash
# Primary usage - open rofi selector
vclip

# Utility commands
vclip --list-commands      # Show all commands (formatted)
vclip --list-files         # Show source markdown files
vclip --clear-cache        # Force reparse on next run
vclip --config-path        # Show config file location
vclip --create-config      # Create default config file
```

### Configuration

**User Config**: `~/.config/vclip/config.yaml` (auto-created on first run)
**Default Config**: `/home/exis/code/vclip/config/config.yaml` (template)
**Cache**: `~/.cache/vclip/commands_*.json`

**Current Source Directories:**
- `/home/exis/Veilcat-OSCP-Methodology/` (primary)
  - Active Directory/
  - Service Enumeration/
  - Local Privilege Escalation/
  - Additional Notes/

**Key Config Settings:**
```yaml
rofi:
  window_width: 60          # 60% of screen width
  element_height: 2         # 2 lines per entry (description + preview)
  max_lines: 15             # Show up to 15 entries at once

sources:
  recursive: true           # Search subdirectories
  file_patterns: ["*.md", "*.markdown"]

cache:
  enabled: true             # JSON caching for speed
```

---

## Architecture

### Project Structure

```
vclip/
├── cmd_manager/              # Main package (1571 LOC)
│   ├── parser.py            # Markdown parsing + deduplication (252 lines)
│   ├── rofi.py              # Rofi interface with two-line display (231 lines)
│   ├── cache.py             # JSON caching system (291 lines)
│   ├── config.py            # YAML config management (301 lines)
│   ├── clipboard.py         # xclip integration (243 lines)
│   └── cli.py               # Main entry point (246 lines)
├── config/
│   └── config.yaml          # Default configuration template
├── test_data/
│   └── sample.md            # Test markdown file
├── vclip                    # Main executable script
├── setup.py                 # Package metadata
├── requirements.txt         # Dependencies: pyyaml
└── CLAUDE.md               # This file
```

### Data Flow

```
1. User runs `vclip`
   ↓
2. ConfigManager loads config from ~/.config/vclip/config.yaml
   ↓
3. Get source files from configured directories (27 markdown files)
   ↓
4. CachedMarkdownParser checks cache validity
   ├─ Cache hit → Load 602 commands from JSON (~instant)
   └─ Cache miss → Parse all files + deduplicate (~1-2 seconds)
   ↓
5. RofiInterface formats commands with pango markup:
   - Line 1: <b>Description</b> <i>[language]</i>
   - Line 2: <small><span alpha='60%'>command preview</span></small>
   - Separated by ASCII Unit Separator (\x1f)
   ↓
6. User searches/selects command in rofi
   ↓
7. Rofi returns entry index → lookup Command object
   ↓
8. ClipboardManager copies command.content to clipboard via xclip
   ↓
9. User pastes command in terminal
```

### Key Technical Details

**Two-Line Rofi Display:**
- Each command is formatted as 2 lines of pango markup
- Lines separated by `\n` (newline) within each entry
- Entries separated by `\x1f` (ASCII Unit Separator) between commands
- `-sep "\x1f"` flag tells rofi to treat each two-line block as one entry
- `-eh 2` sets element height to 2 lines
- Result: Preview stays visible during fuzzy search

**Deduplication Algorithm** (3-pass):
1. **Content hash deduplication**: Remove exact duplicates by MD5 hash
2. **Same-file numbering**: Multiple commands with same description in one file → "#1", "#2", "#3"
3. **Cross-file disambiguation**: Same description across files → add "(filename)" suffix

**Example:**
- Before: "WMI Enumeration" appears 6 times in 135 WMI,MSRPC.md
- After: "WMI Enumeration #1" through "WMI Enumeration #6"

**Caching Strategy:**
- Cache file named by hash of all source file paths
- Cache invalidates if any source file modified (mtime + content hash)
- Cache stores: commands as JSON + metadata + file hashes
- Auto-cleanup removes stale caches

### Markdown Format

Expected input format (from Veilcat-OSCP-Methodology):

```markdown
# Category Name (Level 1 heading)

## Command Description (Level 2 heading - becomes description)
```bash
command content here
```

## Another Command Description
```bash
another command
```
```

**Parsing Rules:**
- `# Heading` → Category (context only, not displayed in rofi)
- `## Heading` → Description (shown in bold in rofi)
- Code blocks with `bash`, `sh`, `shell`, or no language → parsed as commands
- Comments allowed in commands (e.g., `# hashcat OR john`)
- Empty code blocks (only comments/whitespace) → filtered out
- Multiple code blocks under same `##` heading → numbered automatically

### Command Data Structure

```python
@dataclass
class Command:
    content: str          # Actual command text (with comments)
    description: str      # From ## markdown heading
    category: str         # From # markdown heading
    source_file: str      # Full path to .md file
    language: str         # "bash" or numbering for multi-blocks
    line_number: int      # Line in source file
```

---

## Commands for Development

### Testing & Debugging

```bash
# Parse a single file (no cache)
python3 -m cmd_manager.parser test_data/sample.md

# Test rofi interface
python3 -m cmd_manager.rofi test_data/sample.md

# Test cache performance
python3 -m cmd_manager.cache test_data/sample.md parse

# Show cache info
python3 -m cmd_manager.cache test_data/sample.md info

# Test config loading
python3 -m cmd_manager.config show
```

### Common Development Tasks

```bash
# After editing parser/rofi/config code:
pipx uninstall vclip && pipx install . && vclip --clear-cache

# Check what vclip binary is being used:
which vclip
cat $(which vclip) | head -5  # Should point to pipx venv

# Debug command parsing:
vclip --list-commands | grep -A 3 "search term"

# Count commands:
vclip --list-commands | grep -c "^\s*-"

# Check source files:
vclip --list-files
```

---

## Future Improvements (Roadmap)

### 🔥 High Priority (Game Changers)

**1. Variable Substitution** ⭐ #1 Priority
- **Problem**: Commands contain `$IP`, `$TARGET`, `$DOMAIN` etc. - copied literally
- **Impact**: Manual editing every time = slow, error-prone in live engagements
- **Proposed Solution** (Interactive prompts):
  ```
  Selected: nmap -p- $IP

  Variables detected:
    IP: [10.10.11.___ ]  ← Pre-filled from last session

  [Enter] to copy | [Esc] to cancel | [Tab] to edit
  ```
- **Implementation Ideas**:
  - Option A: Pre-prompt at startup: `vclip` → "IP: " → saves for session
  - Option B: Prompt on selection (only if command has variables) ← **Recommended**
  - Option C: Config-based (`variables:` section in config.yaml)
  - Store last-used values in `~/.local/share/vclip/session.json`
- **Files to modify**: `clipboard.py` (add variable replacement), `cli.py` (prompt logic)

**2. Command History / Recently Used**
- **Problem**: Use 20% of commands 80% of the time, but always search from scratch
- **Solution**:
  - Track usage in `~/.local/share/vclip/history.json`
  - Show last 10-20 commands at top of rofi list
  - Different color/marker for recent commands
- **Value**: Muscle memory, faster workflow after initial learning
- **Implementation**: Add to `cache.py`, integrate in `rofi.py` display

**3. Tag-Based Filtering**
- **Problem**: 602 commands is overwhelming when focused on one service
- **Current**: Must search by keyword
- **Improvement**:
  - Add tag metadata to markdown: `<!-- tags: smb, enumeration, recon -->`
  - CLI filter: `vclip -t smb` or `vclip --tag recon,kerberos`
  - Category filter: `vclip -c "Service Enumeration"`
- **Files to modify**: `parser.py` (parse tags), `cli.py` (add filter args)

### 🟡 Medium Priority (Quality of Life)

**4. Multi-Command Sequences / Related Commands**
- Suggest "next steps" after selecting a command
- Example: After "Enumerate SMB shares" → suggest "Mount SMB share", "smbclient connect"
- Could use category proximity or manual tagging

**5. Command Favorites / Pinning**
- Star/pin frequently-used commands
- Dedicated keybind: `Super+Shift+V` → only show favorites

**6. Multi-Target Context**
- Reality: Multiple targets in parallel during pentest
- Solution: `vclip --target dc01` vs `vclip --target web01`
- Per-target variable substitution + command history

**7. Note-Taking Integration**
- Quick note when copying command: "Trying this because nmap showed port 445 open"
- Append to `~/.local/share/vclip/engagement_log.md` with timestamp

**8. Syntax Highlighting in Preview**
- Color-code command components (IPs, flags, file paths)
- Use ANSI colors in preview line

### 🟢 Low Priority (Nice to Have)

**9. Command Validation**
- Check if required tool is installed (e.g., `which netexec`)
- Warn if command might be slow/noisy
- Suggest alternatives if tool missing

**10. Output Templates**
- Standardize output formats: `-oA scan_results` for nmap
- Consistent directory structure: `nmap/`, `loot/`, `creds/`

**11. Clipboard History**
- Keep last 10 copied commands
- Keybind to re-copy previous command

**12. Integration with tmux/terminal multiplexer**
- Auto-paste into pane (not just clipboard)
- Send command + Enter key

---

## Troubleshooting

### Common Issues

**"Error: Error running rofi: embedded null byte"**
- Cause: Trying to use `\0` (null byte) as separator in text mode
- Fixed in current version (uses `\x1f` ASCII Unit Separator instead)
- If you see this: Make sure you've reinstalled after latest changes

**Commands show wrong content when selected**
- Cause: Rofi index mismatch (two-line format vs command count)
- Fixed: Rofi now returns entry index directly (not line index)
- Solution: `vclip --clear-cache` and restart

**Command preview disappears when searching**
- Cause: Using newline as rofi separator (each line = separate entry)
- Fixed: Using `\x1f` separator keeps both lines together
- Solution: Reinstall latest version

**Can't search for exact flags like `--min-rate`**
- Not a bug: Rofi tokenizes on hyphens by default
- Workaround: Search without hyphens: `min rate 4500`
- Why not fixed: Disabling tokenization breaks fuzzy matching (higher priority)

**Cache not invalidating after markdown changes**
- Run: `vclip --clear-cache`
- Cache uses file mtime + content hash - should auto-detect changes
- If persistent: Check file timestamps with `ls -l`

**Commands not showing from new markdown files**
- Check if directory is in config: `vclip --list-files`
- Config location: `~/.config/vclip/config.yaml`
- Add to `sources.directories` list
- Clear cache: `vclip --clear-cache`

### Development Issues

**Changes not applying after editing code**
- Must reinstall: `pipx uninstall vclip && pipx install .`
- pipx uses isolated venv at `/home/exis/.local/pipx/venvs/vclip/`
- Running `./vclip` from source != installed `vclip` command

**Import errors after changes**
- Check if you're in the right directory: `/home/exis/code/vclip`
- Verify pipx installation: `which vclip`
- Should show: `/home/exis/.local/bin/vclip`
- Not: `/home/exis/code/vclip/vclip`

---

## Performance Notes

**With Cache:**
- Startup: ~50-100ms
- Load 602 commands from JSON
- Near-instant rofi display

**Without Cache (first run or after clear):**
- Parse 27 markdown files: ~1-2 seconds
- Deduplication: ~50-100ms
- Cache write: ~10-20ms
- Total: ~2 seconds

**Memory Usage:**
- Python process: ~30-40 MB
- Rofi process: ~10-15 MB
- Cache file: ~150-200 KB

---

## Red Team Operations - Usage Tips

### Workflow Recommendations

**Starting an Engagement:**
1. Set up environment variables (future: will be prompted)
   - Current workaround: Keep target IP in clipboard manager
2. Open vclip with keybind (configure in your WM/DE)
3. Start with reconnaissance commands: search "nmap", "enum", "discover"

**During Enumeration:**
- Search by service: "smb", "ldap", "kerberos", "http"
- Search by action: "enumerate", "scan", "check", "test"
- Search by tool: "nmap", "netexec", "impacket", "kerbrute"

**After Finding Credentials:**
- Search "password spray", "auth", "login", "creds"
- Remember to update `$USERNAME` and `$PASSWORD` placeholders manually

**Post-Exploitation:**
- Search "bloodhound", "secretsdump", "mimikatz", "dump"
- Privilege escalation: search "linpeas", "winpeas", "sudo", "suid"

### Known Gaps (Be Aware)

1. **No automatic variable substitution** - Always edit commands after pasting
2. **No command output tracking** - Use tmux logging or script command
3. **No credential store** - Use separate password manager
4. **No engagement context** - Commands copied without logging why/when
5. **Static command set** - Manual markdown edits needed for new techniques

### Comparison to Alternatives

**vs. Terminal History (Ctrl+R):**
- ✅ Better: Organized by purpose, searchable by description
- ✅ Better: Works across terminal sessions
- ❌ Worse: One extra keystroke (open rofi vs Ctrl+R)

**vs. Obsidian/Notion with code blocks:**
- ✅ Better: Faster access (no context switch to browser)
- ✅ Better: Keyboard-driven, no mouse needed
- ❌ Worse: Less flexible (can't add notes/screenshots inline)

**vs. CherryTree/Cherrytree:**
- ✅ Better: Fuzzy search vs tree navigation
- ✅ Better: Command preview before copy
- ✅ Better: Auto-parses from markdown (no manual entry)

**vs. Custom bash aliases:**
- ✅ Better: Searchable, discoverable
- ✅ Better: Can see command before running
- ❌ Worse: Requires paste step (aliases execute immediately)

---

## Contributing / Future Development

### Before Starting New Features

1. **Read this file completely** - Contains important context and decisions
2. **Check "Future Improvements" section** - See if feature already planned
3. **Test current state**: Run `vclip` to understand UX
4. **Review recent fixes** - Understand what problems were solved and how

### Code Style

- Type hints on all functions
- Docstrings for public methods
- Comments for non-obvious logic (especially index calculations!)
- Keep functions under 50 lines when possible
- Use dataclasses for structured data

### Testing Changes

```bash
# Always test with real data
vclip --list-commands | head -20

# Verify command count hasn't changed unexpectedly
vclip --list-commands | grep -c "^\s*-"  # Should be ~602

# Test rofi display and selection
vclip

# Check cache behavior
vclip --clear-cache
vclip  # Should take ~2 seconds (parsing)
vclip  # Should be instant (cached)
```

### Git Workflow

```bash
# Current branch
git branch  # Should show: main

# Recent commits show stable state
git log --oneline -5

# Before committing new features:
# 1. Test thoroughly with vclip
# 2. Clear cache and verify
# 3. Check for regressions in command count/display
```

---

## Questions for Future Claude

When resuming work on this project, consider:

1. **Variable substitution**: Should we prompt interactively, use config file, or both?
2. **Command history**: Store globally or per-engagement?
3. **Tag system**: Parse from comments or add new metadata section?
4. **Multi-target**: Separate config files or in-memory context switching?
5. **Credential storage**: Integrate with pass/KeePassXC or built-in encrypted store?

---

## Summary - Project Health

**Status**: ✅ **Production-ready for lab work and engagements**

**Strengths:**
- Fast, keyboard-driven workflow
- Reliable command selection and clipboard copy
- Smart deduplication prevents confusion
- Visual preview reduces errors
- Cached parsing makes it very responsive

**Known Limitations:**
- Manual variable substitution required
- No engagement logging/context
- Hyphen search limitation (tokenization trade-off)
- Static command set (manual markdown updates)

**Next Steps (Priority Order):**
1. Implement variable substitution with interactive prompts
2. Add command usage tracking and "recently used" section
3. Implement tag-based filtering
4. Add favorites/pinning system
5. Multi-target context management

**Last Updated**: October 18, 2025 (Session with fixes for index bug, preview visibility, deduplication)
