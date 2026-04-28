"""
Tests for the markdown parser module.
"""

import tempfile
from pathlib import Path

import pytest

from cmd_manager.parser import Command, MarkdownParser


class TestCommand:
    """Test the Command dataclass."""

    def test_command_creation(self):
        cmd = Command(
            content="ls -la",
            description="List files",
            category="System",
            source_file="/test.md",
            workspace="notes",
            language="bash",
            line_number=10,
        )

        assert cmd.content == "ls -la"
        assert cmd.description == "List files"
        assert cmd.category == "System"
        assert cmd.source_file == "/test.md"
        assert cmd.workspace == "notes"
        assert cmd.language == "bash"
        assert cmd.line_number == 10

    def test_command_post_init_cleaning(self):
        cmd = Command(
            content="  ls -la  \n",
            description="  List files  ",
            category="  System  ",
            source_file="/test.md",
            workspace="  notes  ",
            language="  bash  ",
        )

        assert cmd.content == "ls -la"
        assert cmd.description == "List files"
        assert cmd.category == "System"
        assert cmd.workspace == "notes"
        assert cmd.language == "bash"

    def test_to_dict(self):
        cmd = Command(
            content="ls -la",
            description="List files",
            category="System",
            source_file="/test.md",
            workspace="notes",
            language="bash",
            line_number=5,
        )

        assert cmd.to_dict() == {
            "content": "ls -la",
            "description": "List files",
            "category": "System",
            "source_file": "/test.md",
            "workspace": "notes",
            "language": "bash",
            "line_number": 5,
        }

    def test_from_dict(self):
        data = {
            "content": "ls -la",
            "description": "List files",
            "category": "System",
            "source_file": "/test.md",
            "workspace": "notes",
            "language": "bash",
            "line_number": 5,
        }

        cmd = Command.from_dict(data)

        assert cmd.content == "ls -la"
        assert cmd.description == "List files"
        assert cmd.category == "System"
        assert cmd.source_file == "/test.md"
        assert cmd.workspace == "notes"
        assert cmd.language == "bash"
        assert cmd.line_number == 5

    def test_format_for_rofi(self):
        cmd = Command(
            content="ls -la",
            description="List files",
            category="System",
            source_file="/test.md",
            language="bash",
        )

        assert cmd.format_for_rofi() == "List files [bash]"

    def test_format_for_rofi_no_language(self):
        cmd = Command(
            content="ls -la",
            description="List files",
            category="System",
            source_file="/test.md",
        )

        assert cmd.format_for_rofi() == "List files"


class TestMarkdownParser:
    """Test the MarkdownParser class."""

    def test_parse_simple_command(self):
        content = """
# System Commands

## List files
```bash
ls -la
```
"""
        commands = MarkdownParser().parse_content(content, "test.md")

        assert len(commands) == 1
        cmd = commands[0]
        assert cmd.content == "ls -la"
        assert cmd.description == "List files"
        assert cmd.category == "System Commands"
        assert cmd.source_file == "test.md"
        assert cmd.language == "bash"

    def test_parse_multiple_commands(self):
        content = """
# System Commands

## List files
```bash
ls -la
```

## Check disk usage
```bash
df -h
```

# Network Commands

## Ping host
```bash
ping $HOST
```
"""
        commands = MarkdownParser().parse_content(content, "test.md")

        assert len(commands) == 3
        assert commands[0].description == "List files"
        assert commands[0].category == "System Commands"
        assert commands[1].description == "Check disk usage"
        assert commands[1].category == "System Commands"
        assert commands[2].description == "Ping host"
        assert commands[2].category == "Network Commands"

    def test_parse_different_code_block_languages(self):
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
        commands = MarkdownParser().parse_content(content, "test.md")

        assert len(commands) == 3
        assert commands[0].content == "ls -la"
        assert commands[1].content == "ps aux"
        assert commands[2].content == 'echo "generic"'

    def test_parse_multiline_command(self):
        content = """
# System Commands

## Complex command
```bash
for file in *.txt; do
    echo "Processing $file"
    cp "$file" backup/
done
```
"""
        commands = MarkdownParser().parse_content(content, "test.md")

        assert len(commands) == 1
        assert commands[0].content == """for file in *.txt; do
    echo "Processing $file"
    cp "$file" backup/
done"""

    def test_parse_file_not_found(self):
        parser = MarkdownParser()

        with pytest.raises(FileNotFoundError):
            parser.parse_file("non_existent_file.md")

    def test_parse_file(self):
        content = """
# Test Commands

## Test command
```bash
echo "test"
```
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            temp_file = f.name

        try:
            commands = MarkdownParser().parse_file(temp_file)
            assert len(commands) == 1
            assert commands[0].description == "Test command"
            assert commands[0].source_file == temp_file
        finally:
            Path(temp_file).unlink()

    def test_parse_files(self):
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

            commands = MarkdownParser().parse_files([str(file1), str(file2)])

            assert len(commands) == 2
            assert commands[0].source_file == str(file1)
            assert commands[1].source_file == str(file2)

    def test_parse_files_with_error(self):
        content = """
# Valid Commands

## Valid command
```bash
echo "valid"
```
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            valid_file = f.name

        try:
            commands = MarkdownParser().parse_files([valid_file, "invalid_file.md"])
            assert len(commands) == 1
            assert commands[0].description == "Valid command"
        finally:
            Path(valid_file).unlink()

    def test_deduplicate_same_content(self):
        content1 = """
# Commands

## Same command
```bash
echo "same"
```
"""
        content2 = """
# Commands

## Same command
```bash
echo "same"
```
"""
        with tempfile.TemporaryDirectory() as temp_dir:
            file1 = Path(temp_dir) / "file1.md"
            file2 = Path(temp_dir) / "file2.md"
            file1.write_text(content1)
            file2.write_text(content2)

            commands = MarkdownParser().parse_files([str(file1), str(file2)])
            assert len(commands) == 1

    def test_number_multiple_code_blocks_under_same_heading(self):
        content = """
# Commands

## Enumerate SMB
```bash
netexec smb $IP --shares
```

```
smbclient -L //$IP
```
"""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.md"
            file_path.write_text(content)

            commands = MarkdownParser().parse_files([str(file_path)])

            assert len(commands) == 2
            assert commands[0].description == "Enumerate SMB #1"
            assert commands[1].description == "Enumerate SMB #2"
