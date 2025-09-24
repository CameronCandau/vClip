"""
Tests for the markdown parser module.
"""

import pytest
import tempfile
from pathlib import Path
from cmd_manager.parser import Command, MarkdownParser


class TestCommand:
    """Test the Command dataclass."""

    def test_command_creation(self):
        """Test basic command creation."""
        cmd = Command(
            content="ls -la",
            description="List files",
            tags=["files", "listing"],
            category="System",
            source_file="/test.md",
            line_number=10
        )

        assert cmd.content == "ls -la"
        assert cmd.description == "List files"
        assert cmd.tags == ["files", "listing"]
        assert cmd.category == "System"
        assert cmd.source_file == "/test.md"
        assert cmd.line_number == 10

    def test_command_post_init_cleaning(self):
        """Test that __post_init__ cleans up the data."""
        cmd = Command(
            content="  ls -la  \n",
            description="  List files  ",
            tags=["  files  ", "", "  listing  "],
            category="System",
            source_file="/test.md"
        )

        assert cmd.content == "ls -la"
        assert cmd.description == "List files"
        assert cmd.tags == ["files", "listing"]

    def test_to_dict(self):
        """Test conversion to dictionary."""
        cmd = Command(
            content="ls -la",
            description="List files",
            tags=["files"],
            category="System",
            source_file="/test.md",
            line_number=5
        )

        expected = {
            'content': 'ls -la',
            'description': 'List files',
            'tags': ['files'],
            'category': 'System',
            'source_file': '/test.md',
            'line_number': 5
        }

        assert cmd.to_dict() == expected

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            'content': 'ls -la',
            'description': 'List files',
            'tags': ['files'],
            'category': 'System',
            'source_file': '/test.md',
            'line_number': 5
        }

        cmd = Command.from_dict(data)
        assert cmd.content == "ls -la"
        assert cmd.description == "List files"
        assert cmd.tags == ["files"]
        assert cmd.category == "System"
        assert cmd.source_file == "/test.md"
        assert cmd.line_number == 5

    def test_format_for_rofi(self):
        """Test rofi formatting."""
        cmd = Command(
            content="ls -la",
            description="List files",
            tags=["files", "listing"],
            category="System",
            source_file="/test.md"
        )

        expected = "List files (files, listing)"
        assert cmd.format_for_rofi() == expected

    def test_format_for_rofi_no_tags(self):
        """Test rofi formatting without tags."""
        cmd = Command(
            content="ls -la",
            description="List files",
            tags=[],
            category="System",
            source_file="/test.md"
        )

        assert cmd.format_for_rofi() == "List files"


class TestMarkdownParser:
    """Test the MarkdownParser class."""

    def test_parse_simple_command(self):
        """Test parsing a simple command."""
        content = """
# System Commands

## List files
<!-- tags: files, listing -->
```bash
ls -la
```
"""
        parser = MarkdownParser()
        commands = parser.parse_content(content, "test.md")

        assert len(commands) == 1
        cmd = commands[0]
        assert cmd.content == "ls -la"
        assert cmd.description == "List files"
        assert cmd.tags == ["files", "listing"]
        assert cmd.category == "System Commands"
        assert cmd.source_file == "test.md"

    def test_parse_multiple_commands(self):
        """Test parsing multiple commands."""
        content = """
# System Commands

## List files
<!-- tags: files -->
```bash
ls -la
```

## Check disk usage
<!-- tags: disk, monitoring -->
```bash
df -h
```

# Network Commands

## Ping host
<!-- tags: network, testing -->
```bash
ping $HOST
```
"""
        parser = MarkdownParser()
        commands = parser.parse_content(content, "test.md")

        assert len(commands) == 3

        # First command
        assert commands[0].description == "List files"
        assert commands[0].category == "System Commands"
        assert commands[0].tags == ["files"]

        # Second command
        assert commands[1].description == "Check disk usage"
        assert commands[1].category == "System Commands"
        assert commands[1].tags == ["disk", "monitoring"]

        # Third command
        assert commands[2].description == "Ping host"
        assert commands[2].category == "Network Commands"
        assert commands[2].tags == ["network", "testing"]

    def test_parse_no_tags(self):
        """Test parsing command without tags."""
        content = """
# System Commands

## List files
```bash
ls -la
```
"""
        parser = MarkdownParser()
        commands = parser.parse_content(content, "test.md")

        assert len(commands) == 1
        assert commands[0].tags == []

    def test_parse_different_code_block_languages(self):
        """Test that only bash/shell blocks are parsed."""
        content = """
# Commands

## Bash command
```bash
ls -la
```

## Shell command
```sh
ps aux
```

## Python code (should be ignored)
```python
print("hello")
```

## Generic code block
```
echo "generic"
```
"""
        parser = MarkdownParser()
        commands = parser.parse_content(content, "test.md")

        assert len(commands) == 3  # bash, sh, and generic
        assert commands[0].content == "ls -la"
        assert commands[1].content == "ps aux"
        assert commands[2].content == 'echo "generic"'

    def test_parse_multiline_command(self):
        """Test parsing multiline commands."""
        content = """
# System Commands

## Complex command
<!-- tags: complex -->
```bash
for file in *.txt; do
    echo "Processing $file"
    cp "$file" backup/
done
```
"""
        parser = MarkdownParser()
        commands = parser.parse_content(content, "test.md")

        assert len(commands) == 1
        expected_content = """for file in *.txt; do
    echo "Processing $file"
    cp "$file" backup/
done"""
        assert commands[0].content == expected_content

    def test_parse_file_not_found(self):
        """Test parsing non-existent file."""
        parser = MarkdownParser()

        with pytest.raises(FileNotFoundError):
            parser.parse_file("non_existent_file.md")

    def test_parse_file(self):
        """Test parsing an actual file."""
        content = """
# Test Commands

## Test command
<!-- tags: test -->
```bash
echo "test"
```
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content)
            temp_file = f.name

        try:
            parser = MarkdownParser()
            commands = parser.parse_file(temp_file)

            assert len(commands) == 1
            assert commands[0].description == "Test command"
            assert commands[0].source_file == temp_file
        finally:
            Path(temp_file).unlink()

    def test_parse_files(self):
        """Test parsing multiple files."""
        content1 = """
# File 1 Commands

## Command 1
```bash
echo "file1"
```
"""
        content2 = """
# File 2 Commands

## Command 2
```bash
echo "file2"
```
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            file1 = Path(temp_dir) / "file1.md"
            file2 = Path(temp_dir) / "file2.md"

            file1.write_text(content1)
            file2.write_text(content2)

            parser = MarkdownParser()
            commands = parser.parse_files([str(file1), str(file2)])

            assert len(commands) == 2
            assert commands[0].source_file == str(file1)
            assert commands[1].source_file == str(file2)

    def test_parse_files_with_error(self):
        """Test parsing files with one that doesn't exist."""
        content = """
# Valid Commands

## Valid command
```bash
echo "valid"
```
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content)
            valid_file = f.name

        try:
            parser = MarkdownParser()
            # This should not raise an exception, just skip the invalid file
            commands = parser.parse_files([valid_file, "invalid_file.md"])

            assert len(commands) == 1
            assert commands[0].description == "Valid command"
        finally:
            Path(valid_file).unlink()