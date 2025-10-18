"""
Markdown parser for extracting command snippets with metadata.
"""

import re
import hashlib
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from pathlib import Path


@dataclass
class Command:
    """Represents a command snippet with metadata."""
    content: str
    description: str
    category: str
    source_file: str
    language: str = ""
    line_number: int = 0

    def __post_init__(self):
        """Clean up command content."""
        self.content = self.content.strip()
        self.description = self.description.strip()
        self.category = self.category.strip()
        self.language = self.language.strip()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'content': self.content,
            'description': self.description,
            'category': self.category,
            'source_file': self.source_file,
            'language': self.language,
            'line_number': self.line_number
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Command':
        """Create Command from dictionary."""
        return cls(
            content=data['content'],
            description=data['description'],
            category=data['category'],
            source_file=data['source_file'],
            language=data.get('language', ''),
            line_number=data.get('line_number', 0)
        )

    def format_for_rofi(self) -> str:
        """Format command for display in rofi."""
        if self.language:
            return f"{self.description} [{self.language}]"
        return self.description


class MarkdownParser:
    """Parser for extracting commands from markdown files."""

    def __init__(self):
        self.commands: List[Command] = []

    def parse_file(self, file_path: str) -> List[Command]:
        """Parse a single markdown file and return commands."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        return self.parse_content(content, str(path))

    def parse_content(self, content: str, source_file: str) -> List[Command]:
        """Parse markdown content and extract commands."""
        commands = []
        lines = content.split('\n')
        current_category = ""
        current_description = ""
        in_code_block = False
        code_block_content = []
        code_block_lang = ""
        description_command_count = {}  # Track how many commands per description

        for line_num, line in enumerate(lines, 1):
            line = line.rstrip()

            # Check for category headers (# Level 1)
            if line.startswith('# ') and not in_code_block:
                current_category = line[2:].strip()
                continue

            # Check for description headers (## Level 2)
            if line.startswith('## ') and not in_code_block:
                current_description = line[3:].strip()
                continue

            # Check for code block start
            if line.startswith('```') and not in_code_block:
                in_code_block = True
                code_block_lang = line[3:].strip()
                code_block_content = []
                continue

            # Check for code block end
            if line.startswith('```') and in_code_block:
                in_code_block = False
                if code_block_content and current_description:
                    # Include bash/shell/powershell/cmd code blocks or unspecified
                    if not code_block_lang or code_block_lang.lower() in ['bash', 'sh', 'shell', 'powershell', 'ps1', 'cmd', 'bat', 'batch']:
                        # Join and check if content has actual commands (not just whitespace/comments)
                        content = '\n'.join(code_block_content)

                        # Filter out empty commands (only whitespace or comments)
                        non_empty_lines = [line for line in code_block_content if line.strip() and not line.strip().startswith('#')]

                        # Only add commands that have actual content
                        if non_empty_lines:
                            # Track multiple code blocks under same description
                            if current_description not in description_command_count:
                                description_command_count[current_description] = 0
                            description_command_count[current_description] += 1

                            # Determine display language/number
                            display_lang = code_block_lang if code_block_lang else ""
                            if description_command_count[current_description] > 1 and not display_lang:
                                display_lang = str(description_command_count[current_description])

                            command = Command(
                                content=content,
                                description=current_description,
                                category=current_category,
                                source_file=source_file,
                                language=display_lang,
                                line_number=line_num - len(code_block_content) - 1
                            )
                            commands.append(command)

                # Reset for next code block (but keep description for multiple blocks)
                code_block_content = []
                code_block_lang = ""
                continue

            # Collect code block content
            if in_code_block:
                code_block_content.append(line)

        return commands

    def parse_files(self, file_paths: List[str]) -> List[Command]:
        """Parse multiple markdown files."""
        all_commands = []
        for file_path in file_paths:
            try:
                commands = self.parse_file(file_path)
                all_commands.extend(commands)
            except Exception as e:
                print(f"Error parsing {file_path}: {e}")

        # Deduplicate commands
        return self._deduplicate_commands(all_commands)

    def _deduplicate_commands(self, commands: List[Command]) -> List[Command]:
        """
        Deduplicate commands based on content similarity.

        Strategy:
        1. Commands with identical content hash are removed (keep first occurrence)
        2. Commands with same description from SAME file are numbered (#1, #2, etc.)
        3. Commands with same description from DIFFERENT files get source file in description
        """
        # First pass: remove exact content duplicates
        seen_content_hashes = set()
        unique_by_content = []

        for cmd in commands:
            content_hash = hashlib.md5(cmd.content.encode()).hexdigest()
            if content_hash not in seen_content_hashes:
                seen_content_hashes.add(content_hash)
                unique_by_content.append(cmd)

        # Second pass: group by (description, source_file) to handle same-file duplicates
        from collections import defaultdict
        file_desc_groups = defaultdict(list)

        for cmd in unique_by_content:
            key = (cmd.description, cmd.source_file)
            file_desc_groups[key].append(cmd)

        # Third pass: number commands from same file with same description
        numbered_commands = []
        for (description, source_file), cmds in file_desc_groups.items():
            if len(cmds) > 1:
                # Multiple commands with same description in same file - number them
                for idx, cmd in enumerate(cmds, 1):
                    cmd.description = f"{description} #{idx}"
                    numbered_commands.append(cmd)
            else:
                numbered_commands.append(cmds[0])

        # Fourth pass: group by description to handle cross-file duplicates
        desc_groups = defaultdict(list)
        for cmd in numbered_commands:
            desc_groups[cmd.description].append(cmd)

        # Final pass: add source file names to cross-file duplicates
        deduplicated = []
        for description, cmds in desc_groups.items():
            if len(cmds) > 1:
                # Multiple commands from different files with same description
                for cmd in cmds:
                    source_name = Path(cmd.source_file).stem
                    cmd.description = f"{description} ({source_name})"
                    deduplicated.append(cmd)
            else:
                deduplicated.append(cmds[0])

        return deduplicated


def main():
    """CLI interface for testing the parser."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m cmd_manager.parser <markdown_file>")
        sys.exit(1)

    file_path = sys.argv[1]
    parser = MarkdownParser()

    try:
        commands = parser.parse_file(file_path)
        print(f"Found {len(commands)} commands in {file_path}:")
        print()

        for i, cmd in enumerate(commands, 1):
            print(f"{i}. {cmd.description}")
            print(f"   Category: {cmd.category}")
            print(f"   Language: {cmd.language if cmd.language else 'None'}")
            print(f"   Command: {cmd.content}")
            print(f"   Rofi format: {cmd.format_for_rofi()}")
            print()

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()