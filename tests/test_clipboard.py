"""
Tests for the clipboard module.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from cmd_manager.clipboard import ClipboardManager
from cmd_manager.parser import Command


class TestClipboardManager:
    """Test the ClipboardManager class."""

    def test_substitute_variables_basic(self):
        """Test basic variable substitution."""
        clipboard = ClipboardManager()
        command_text = "ping $HOST"
        variables = {"HOST": "192.168.1.1"}

        result = clipboard.substitute_variables(command_text, variables)
        assert result == "ping 192.168.1.1"

    def test_substitute_variables_multiple(self):
        """Test substitution of multiple variables."""
        clipboard = ClipboardManager()
        command_text = "ssh $USER@$HOST -p $PORT"
        variables = {
            "USER": "admin",
            "HOST": "192.168.1.1",
            "PORT": "2222"
        }

        result = clipboard.substitute_variables(command_text, variables)
        assert result == "ssh admin@192.168.1.1 -p 2222"

    def test_substitute_variables_missing(self):
        """Test substitution with missing variables."""
        clipboard = ClipboardManager()
        command_text = "ssh $USER@$HOST"
        variables = {"USER": "admin"}  # Missing HOST

        result = clipboard.substitute_variables(command_text, variables)
        assert result == "ssh admin@$HOST"  # $HOST remains unchanged

    def test_substitute_variables_none(self):
        """Test substitution with no variables."""
        clipboard = ClipboardManager()
        command_text = "ls -la"
        variables = {}

        result = clipboard.substitute_variables(command_text, variables)
        assert result == "ls -la"

    def test_get_variables_from_command(self):
        """Test extracting variables from command text."""
        clipboard = ClipboardManager()

        # Single variable
        variables = clipboard.get_variables_from_command("ping $HOST")
        assert variables == ["HOST"]

        # Multiple variables
        variables = clipboard.get_variables_from_command("ssh $USER@$HOST -p $PORT")
        assert set(variables) == {"USER", "HOST", "PORT"}

        # No variables
        variables = clipboard.get_variables_from_command("ls -la")
        assert variables == []

        # Duplicate variables
        variables = clipboard.get_variables_from_command("echo $VAR $VAR")
        assert variables == ["VAR", "VAR"]  # Should include duplicates

    def test_get_variables_case_sensitivity(self):
        """Test that variable extraction is case sensitive."""
        clipboard = ClipboardManager()
        variables = clipboard.get_variables_from_command("echo $var $VAR")
        assert "VAR" in variables
        assert "var" not in variables  # lowercase variables are not matched

    @patch('subprocess.run')
    def test_copy_to_clipboard_xclip(self, mock_run):
        """Test copying with xclip."""
        clipboard = ClipboardManager()
        clipboard.available_tools = {'xclip': True, 'xsel': False, 'wl-copy': False}

        mock_run.return_value = Mock()
        result = clipboard.copy_to_clipboard("test content")

        assert result is True
        mock_run.assert_called_once_with(
            ['xclip', '-selection', 'clipboard'],
            input='test content',
            text=True,
            check=True
        )

    @patch('subprocess.run')
    def test_copy_to_clipboard_xsel_fallback(self, mock_run):
        """Test copying with xsel as fallback."""
        clipboard = ClipboardManager()
        clipboard.available_tools = {'xclip': False, 'xsel': True, 'wl-copy': False}

        mock_run.return_value = Mock()
        result = clipboard.copy_to_clipboard("test content")

        assert result is True
        mock_run.assert_called_once_with(
            ['xsel', '--clipboard', '--input'],
            input='test content',
            text=True,
            check=True
        )

    @patch('subprocess.run')
    def test_copy_to_clipboard_wl_copy(self, mock_run):
        """Test copying with wl-copy."""
        clipboard = ClipboardManager()
        clipboard.available_tools = {'xclip': False, 'xsel': False, 'wl-copy': True}

        mock_run.return_value = Mock()
        result = clipboard.copy_to_clipboard("test content")

        assert result is True
        mock_run.assert_called_once_with(
            ['wl-copy'],
            input='test content',
            text=True,
            check=True
        )

    @patch('subprocess.run')
    def test_copy_to_clipboard_no_tools(self, mock_run):
        """Test copying when no tools are available."""
        clipboard = ClipboardManager()
        clipboard.available_tools = {'xclip': False, 'xsel': False, 'wl-copy': False}

        result = clipboard.copy_to_clipboard("test content")
        assert result is False
        mock_run.assert_not_called()

    @patch('subprocess.run')
    def test_copy_command_with_variables(self, mock_run):
        """Test copying command with variable substitution."""
        clipboard = ClipboardManager()
        clipboard.available_tools = {'xclip': True, 'xsel': False, 'wl-copy': False}

        command = Command(
            content="ping $HOST",
            description="Ping host",
            tags=["network"],
            category="Network",
            source_file="test.md"
        )

        variables = {"HOST": "192.168.1.1"}
        mock_run.return_value = Mock()

        result = clipboard.copy_command(command, variables)

        assert result is True
        mock_run.assert_called_once_with(
            ['xclip', '-selection', 'clipboard'],
            input='ping 192.168.1.1',
            text=True,
            check=True
        )

    @patch('subprocess.run')
    def test_copy_command_no_variables(self, mock_run):
        """Test copying command without variables."""
        clipboard = ClipboardManager()
        clipboard.available_tools = {'xclip': True, 'xsel': False, 'wl-copy': False}

        command = Command(
            content="ls -la",
            description="List files",
            tags=["files"],
            category="System",
            source_file="test.md"
        )

        mock_run.return_value = Mock()
        result = clipboard.copy_command(command)

        assert result is True
        mock_run.assert_called_once_with(
            ['xclip', '-selection', 'clipboard'],
            input='ls -la',
            text=True,
            check=True
        )

    def test_check_clipboard_availability(self):
        """Test checking clipboard tool availability."""
        clipboard = ClipboardManager()

        # All tools available
        clipboard.available_tools = {'xclip': True, 'xsel': True, 'wl-copy': True}
        assert clipboard.check_clipboard_availability() is True

        # Some tools available
        clipboard.available_tools = {'xclip': False, 'xsel': True, 'wl-copy': False}
        assert clipboard.check_clipboard_availability() is True

        # No tools available
        clipboard.available_tools = {'xclip': False, 'xsel': False, 'wl-copy': False}
        assert clipboard.check_clipboard_availability() is False

    def test_get_clipboard_status(self):
        """Test getting clipboard status."""
        clipboard = ClipboardManager()
        clipboard.available_tools = {'xclip': True, 'xsel': False, 'wl-copy': True}

        status = clipboard.get_clipboard_status()
        expected = {'xclip': True, 'xsel': False, 'wl-copy': True}
        assert status == expected

        # Ensure it returns a copy, not the original
        status['xclip'] = False
        assert clipboard.available_tools['xclip'] is True

    @patch('builtins.input')
    def test_prompt_for_variables(self, mock_input):
        """Test prompting for variable values."""
        clipboard = ClipboardManager()
        command = Command(
            content="ssh $USER@$HOST",
            description="SSH to host",
            tags=["ssh"],
            category="Network",
            source_file="test.md"
        )

        mock_input.side_effect = ["admin", "192.168.1.1"]

        with patch('builtins.print'):  # Suppress print output
            variables = clipboard.prompt_for_variables(command)

        expected = {"USER": "admin", "HOST": "192.168.1.1"}
        assert variables == expected

    @patch('builtins.input')
    def test_prompt_for_variables_empty_input(self, mock_input):
        """Test prompting with empty input."""
        clipboard = ClipboardManager()
        command = Command(
            content="ssh $USER@$HOST",
            description="SSH to host",
            tags=["ssh"],
            category="Network",
            source_file="test.md"
        )

        mock_input.side_effect = ["admin", ""]  # Empty input for HOST

        with patch('builtins.print'):  # Suppress print output
            variables = clipboard.prompt_for_variables(command)

        expected = {"USER": "admin"}  # HOST should not be included
        assert variables == expected