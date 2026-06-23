"""
Clipboard integration for copying commands.
"""

import subprocess
from typing import Dict, Optional
from .parser import Command
from .variables import VariableDetector, VariableSubstitutor


class ClipboardManager:
    """Manages clipboard operations and variable substitution."""

    def __init__(self, config_variables: Dict[str, str] = None):
        self.available_tools = self._detect_clipboard_tools()
        self._substitutor = VariableSubstitutor(config_variables or {})

    def _detect_clipboard_tools(self) -> Dict[str, bool]:
        """Detect available clipboard tools on the system."""
        tools = {}

        for command, version_flag in (("xclip", "-version"), ("xsel", "--version"), ("wl-copy", "--version")):
            try:
                subprocess.run([command, version_flag], capture_output=True, check=True)
                tools[command] = True
            except (FileNotFoundError, subprocess.CalledProcessError):
                tools[command] = False

        return tools

    def copy_to_clipboard(self, text: str) -> bool:
        """Copy text to clipboard using the first available tool."""
        commands = [
            ("xclip", ["xclip", "-selection", "clipboard"]),
            ("xsel", ["xsel", "--clipboard", "--input"]),
            ("wl-copy", ["wl-copy"]),
        ]

        for tool_name, command in commands:
            if not self.available_tools.get(tool_name, False):
                continue
            try:
                subprocess.run(command, input=text, text=True, check=True, timeout=5)
                return True
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                pass

        return False

    def prepare_command_text(
        self,
        command: Command,
        rofi=None,
        no_prompt: bool = False,
        substitute_variables: bool = False
    ) -> Optional[str]:
        """Prepare command text for clipboard copy."""
        text = command.content

        if not substitute_variables or not VariableDetector.has_variables(text):
            return text

        variables = VariableDetector.detect(text)
        values = self._substitutor.resolve(variables, rofi=rofi, no_prompt=no_prompt)
        if values is None:
            return None

        return VariableDetector.substitute(text, values)

    def copy_command(
        self,
        command: Command,
        rofi=None,
        no_prompt: bool = False,
        substitute_variables: bool = False
    ) -> bool:
        """Copy command to clipboard."""
        text = self.prepare_command_text(
            command,
            rofi=rofi,
            no_prompt=no_prompt,
            substitute_variables=substitute_variables
        )
        if text is None:
            return False

        return self.copy_to_clipboard(text)

    def get_clipboard_status(self) -> Dict[str, bool]:
        """Get status of available clipboard tools."""
        return self.available_tools.copy()

    def check_clipboard_availability(self) -> bool:
        """Check if any clipboard tool is available."""
        return any(self.available_tools.values())
