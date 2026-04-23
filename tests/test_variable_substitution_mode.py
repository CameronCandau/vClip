from unittest.mock import Mock

from cmd_manager.clipboard import ClipboardManager
from cmd_manager.cli import main_selection_flow
from cmd_manager.config import CacheConfig, RofiConfig, SourceConfig, VclipConfig
from cmd_manager.parser import Command


def make_command(content="ping $HOST", description="Ping host"):
    return Command(
        content=content,
        description=description,
        category="Network",
        source_file="test.md",
    )


def test_prepare_command_text_defaults_to_literal():
    clipboard = ClipboardManager()
    command = make_command()
    rofi = Mock()

    text = clipboard.prepare_command_text(command, rofi=rofi, substitute_variables=False)

    assert text == "ping $HOST"
    rofi.prompt_input.assert_not_called()


def test_prepare_command_text_substitutes_when_enabled():
    clipboard = ClipboardManager({"HOST": "10.10.10.10"})
    command = make_command()

    text = clipboard.prepare_command_text(command, substitute_variables=True)

    assert text == "ping 10.10.10.10"


def test_copy_and_paste_uses_rendered_text(monkeypatch):
    clipboard = ClipboardManager({"HOST": "10.10.10.10"})
    command = make_command()
    copied = {}
    pasted = {}

    def fake_copy(text):
        copied["text"] = text
        return True

    def fake_paste(text):
        pasted["text"] = text
        return True

    monkeypatch.setattr(clipboard, "copy_to_clipboard", fake_copy)
    monkeypatch.setattr(clipboard, "_auto_paste", fake_paste)

    assert clipboard.copy_and_paste_command(command, substitute_variables=True) is True
    assert copied["text"] == "ping 10.10.10.10"
    assert pasted["text"] == "ping 10.10.10.10"


def test_main_selection_flow_toggle_entry_persists_and_enables_substitution(monkeypatch):
    config = VclipConfig(
        sources=SourceConfig(files=[], directories=[]),
        rofi=RofiConfig(args=[], use_markup=False),
        cache=CacheConfig(enabled=True, directory=None, auto_cleanup=True),
        substitute_variables=False,
        variables={},
    )
    selected_modes = []
    saved_configs = []
    command = make_command()

    class FakeConfigManager:
        config_path = "/tmp/vclip-config.yaml"

        def __init__(self):
            self.config = config

        def load_config(self):
            return self.config

        def get_source_files(self):
            return ["test.md"]

        def save_config(self, cfg):
            saved_configs.append(cfg.substitute_variables)
            self.config = cfg
            return True

    class FakeParser:
        def __init__(self, _directory):
            pass

        def parse_files_cached(self, _source_files):
            return [command]

    class FakeRofi:
        def __init__(self, _args):
            self.calls = 0

        def select_command(self, menu_commands):
            self.calls += 1
            if self.calls == 1:
                return menu_commands[0]
            return menu_commands[1]

    class FakeClipboard:
        def __init__(self, _variables):
            pass

        def check_clipboard_availability(self):
            return True

        def copy_command(self, selected_command, rofi=None, no_prompt=False, substitute_variables=False):
            selected_modes.append(substitute_variables)
            return selected_command is command

    monkeypatch.setattr("cmd_manager.cli.CachedMarkdownParser", FakeParser)
    monkeypatch.setattr("cmd_manager.cli.RofiInterface", FakeRofi)
    monkeypatch.setattr("cmd_manager.cli.ClipboardManager", FakeClipboard)

    assert main_selection_flow(FakeConfigManager(), use_cache=True, no_prompt=False, auto_paste=False) == 0
    assert saved_configs == [True]
    assert selected_modes == [True]
