"""
Tests for the clipboard module.
"""

from unittest.mock import Mock, patch

from cmd_manager.clipboard import ClipboardManager
from cmd_manager.parser import Command


def make_clipboard(config_variables=None):
    with patch.object(ClipboardManager, "_detect_clipboard_tools", return_value={"xclip": False, "xsel": False, "wl-copy": False}):
        return ClipboardManager(config_variables or {})


class TestClipboardManager:
    """Test the ClipboardManager class."""

    def test_prepare_command_text_defaults_to_literal(self):
        clipboard = make_clipboard()
        command = Command(
            content="ping $HOST",
            description="Ping host",
            category="Network",
            source_file="test.md",
        )
        rofi = Mock()

        text = clipboard.prepare_command_text(command, rofi=rofi, substitute_variables=False)

        assert text == "ping $HOST"
        rofi.prompt_input.assert_not_called()

    def test_prepare_command_text_substitutes_config_variables(self):
        clipboard = make_clipboard({"HOST": "192.168.1.1"})
        command = Command(
            content="ping $HOST",
            description="Ping host",
            category="Network",
            source_file="test.md",
        )

        text = clipboard.prepare_command_text(command, substitute_variables=True)

        assert text == "ping 192.168.1.1"

    def test_prepare_command_text_uses_rofi_for_missing_variables(self):
        clipboard = make_clipboard()
        command = Command(
            content="ssh $USER@$HOST",
            description="SSH to host",
            category="Network",
            source_file="test.md",
        )
        rofi = Mock()
        rofi.prompt_input.side_effect = ["10.10.10.10", "admin"]

        text = clipboard.prepare_command_text(command, rofi=rofi, substitute_variables=True)

        assert text == "ssh admin@10.10.10.10"

    def test_prepare_command_text_cancelled_prompt_returns_none(self):
        clipboard = make_clipboard()
        command = Command(
            content="ssh $USER@$HOST",
            description="SSH to host",
            category="Network",
            source_file="test.md",
        )
        rofi = Mock()
        rofi.prompt_input.return_value = None

        text = clipboard.prepare_command_text(command, rofi=rofi, substitute_variables=True)

        assert text is None

    @patch("subprocess.run")
    def test_copy_to_clipboard_xclip(self, mock_run):
        clipboard = make_clipboard()
        clipboard.available_tools = {"xclip": True, "xsel": False, "wl-copy": False}

        mock_run.return_value = Mock()
        result = clipboard.copy_to_clipboard("test content")

        assert result is True
        mock_run.assert_called_once_with(
            ["xclip", "-selection", "clipboard"],
            input="test content",
            text=True,
            check=True,
            timeout=5,
        )

    @patch("subprocess.run")
    def test_copy_to_clipboard_xsel_fallback(self, mock_run):
        clipboard = make_clipboard()
        clipboard.available_tools = {"xclip": False, "xsel": True, "wl-copy": False}

        mock_run.return_value = Mock()
        result = clipboard.copy_to_clipboard("test content")

        assert result is True
        mock_run.assert_called_once_with(
            ["xsel", "--clipboard", "--input"],
            input="test content",
            text=True,
            check=True,
            timeout=5,
        )

    @patch("subprocess.run")
    def test_copy_to_clipboard_wl_copy(self, mock_run):
        clipboard = make_clipboard()
        clipboard.available_tools = {"xclip": False, "xsel": False, "wl-copy": True}

        mock_run.return_value = Mock()
        result = clipboard.copy_to_clipboard("test content")

        assert result is True
        mock_run.assert_called_once_with(
            ["wl-copy"],
            input="test content",
            text=True,
            check=True,
            timeout=5,
        )

    @patch("subprocess.run")
    def test_copy_to_clipboard_no_tools(self, mock_run):
        clipboard = make_clipboard()
        clipboard.available_tools = {"xclip": False, "xsel": False, "wl-copy": False}

        result = clipboard.copy_to_clipboard("test content")

        assert result is False
        mock_run.assert_not_called()

    def test_copy_command_with_variable_substitution(self):
        clipboard = make_clipboard({"HOST": "192.168.1.1"})
        command = Command(
            content="ping $HOST",
            description="Ping host",
            category="Network",
            source_file="test.md",
        )

        with patch.object(clipboard, "copy_to_clipboard", return_value=True) as mock_copy:
            result = clipboard.copy_command(command, substitute_variables=True)

        assert result is True
        mock_copy.assert_called_once_with("ping 192.168.1.1")

    def test_copy_command_cancelled_variable_prompt(self):
        clipboard = make_clipboard()
        command = Command(
            content="ping $HOST",
            description="Ping host",
            category="Network",
            source_file="test.md",
        )
        rofi = Mock()
        rofi.prompt_input.return_value = None

        with patch.object(clipboard, "copy_to_clipboard", return_value=True) as mock_copy:
            result = clipboard.copy_command(command, rofi=rofi, substitute_variables=True)

        assert result is False
        mock_copy.assert_not_called()

    def test_copy_and_paste_uses_rendered_text(self):
        clipboard = make_clipboard({"HOST": "10.10.10.10"})
        command = Command(
            content="ping $HOST",
            description="Ping host",
            category="Network",
            source_file="test.md",
        )

        copied = {}
        pasted = {}

        def fake_copy(text):
            copied["text"] = text
            return True

        def fake_paste(text):
            pasted["text"] = text
            return True

        with patch.object(clipboard, "copy_to_clipboard", side_effect=fake_copy):
            with patch.object(clipboard, "_auto_paste", side_effect=fake_paste):
                assert clipboard.copy_and_paste_command(command, substitute_variables=True) is True

        assert copied["text"] == "ping 10.10.10.10"
        assert pasted["text"] == "ping 10.10.10.10"

    def test_check_clipboard_availability(self):
        clipboard = make_clipboard()

        clipboard.available_tools = {"xclip": True, "xsel": True, "wl-copy": True}
        assert clipboard.check_clipboard_availability() is True

        clipboard.available_tools = {"xclip": False, "xsel": True, "wl-copy": False}
        assert clipboard.check_clipboard_availability() is True

        clipboard.available_tools = {"xclip": False, "xsel": False, "wl-copy": False}
        assert clipboard.check_clipboard_availability() is False

    def test_get_clipboard_status(self):
        clipboard = make_clipboard()
        clipboard.available_tools = {"xclip": True, "xsel": False, "wl-copy": True}

        status = clipboard.get_clipboard_status()
        assert status == {"xclip": True, "xsel": False, "wl-copy": True}

        status["xclip"] = False
        assert clipboard.available_tools["xclip"] is True
