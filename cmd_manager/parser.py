"""
Markdown parser for extracting command snippets with metadata.
"""

import re
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from pathlib import Path


@dataclass
class Command:
    """Represents a command snippet with metadata."""
    content: str
    description: str
    tags: List[str]
    category: str
    source_file: str
    line_number: int = 0

    def __post_init__(self):
        """Clean up command content."""
        self.content = self.content.strip()
        self.description = self.description.strip()
        self.tags = [tag.strip() for tag in self.tags if tag.strip()]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'content': self.content,
            'description': self.description,
            'tags': self.tags,
            'category': self.category,
            'source_file': self.source_file,
            'line_number': self.line_number
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Command':
        """Create Command from dictionary."""
        return cls(
            content=data['content'],
            description=data['description'],
            tags=data['tags'],
            category=data['category'],
            source_file=data['source_file'],
            line_number=data.get('line_number', 0)
        )

    def format_for_rofi(self) -> str:
        """Format command for display in rofi."""
        tags_str = f"({', '.join(self.tags)})" if self.tags else ""
        return f"{self.description} {tags_str}".strip()


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
        current_tags = []
        in_code_block = False
        code_block_content = []
        code_block_lang = ""

        for line_num, line in enumerate(lines, 1):
            line = line.rstrip()

            # Check for category headers (# Level 1)
            if line.startswith('# ') and not in_code_block:
                current_category = line[2:].strip()
                continue

            # Check for description headers (## Level 2)
            if line.startswith('## ') and not in_code_block:
                current_description = line[3:].strip()
                current_tags = []
                continue

            # Check for tags in HTML comments
            if '<!-- tags:' in line and not in_code_block:
                tags_match = re.search(r'<!-- tags:\s*([^-]+)\s*-->', line)
                if tags_match:
                    tags_str = tags_match.group(1)
                    current_tags = [tag.strip() for tag in tags_str.split(',')]
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
                    # Only include bash/shell code blocks or unspecified
                    if not code_block_lang or code_block_lang.lower() in ['bash', 'sh', 'shell']:
                        command = Command(
                            content='\n'.join(code_block_content),
                            description=current_description,
                            tags=current_tags.copy(),
                            category=current_category,
                            source_file=source_file,
                            line_number=line_num - len(code_block_content) - 1
                        )
                        commands.append(command)

                # Reset for next command
                current_description = ""
                current_tags = []
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

        return all_commands


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
            print(f"   Tags: {', '.join(cmd.tags) if cmd.tags else 'None'}")
            print(f"   Command: {cmd.content}")
            print(f"   Rofi format: {cmd.format_for_rofi()}")
            print()

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()