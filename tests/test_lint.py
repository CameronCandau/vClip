"""
Tests for the vclip markdown linter.
"""

from cmd_manager.lint import MarkdownLinter


class TestMarkdownLinter:
    """Test the markdown linter."""

    def test_valid_vclip_note(self):
        content = """
# Azure CLI

## Login with device code
```bash
az login --use-device-code
```
"""
        result = MarkdownLinter().lint_content(content, "azure.md")

        assert result.error_count == 0
        assert result.warning_count == 0

    def test_missing_task_heading_is_error(self):
        content = """
# Azure CLI

```bash
az login --use-device-code
```
"""
        result = MarkdownLinter().lint_content(content, "azure.md")

        assert result.error_count >= 1
        assert any(issue.code == "missing-description" for issue in result.issues)

    def test_unsupported_language_is_warning(self):
        content = """
# Azure CLI

## Login helper
```python
print("az login")
```
"""
        result = MarkdownLinter().lint_content(content, "azure.md")

        assert any(issue.code == "unsupported-language" for issue in result.issues)
        assert any(issue.code == "no-commands" for issue in result.issues)

    def test_empty_command_block_is_error(self):
        content = """
# SMB

## Enumerate shares
```bash
# TODO add real command
```
"""
        result = MarkdownLinter().lint_content(content, "smb.md")

        assert any(issue.code == "empty-command" for issue in result.issues)

    def test_heading_without_command_is_warning(self):
        content = """
# SMB

## Enumerate shares
Some prose here, but no fenced command.
"""
        result = MarkdownLinter().lint_content(content, "smb.md")

        assert any(issue.code == "heading-without-command" for issue in result.issues)
