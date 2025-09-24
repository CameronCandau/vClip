"""
Clipboard integration for copying commands.
"""

import subprocess
import re
import time
import platform
from typing import Dict, Optional
from .parser import Command


class ClipboardManager:
    """Manages clipboard operations and variable substitution."""

    def __init__(self):
        self.available_tools = self._detect_clipboard_tools()

    def _detect_clipboard_tools(self) -> Dict[str, bool]:
        """Detect available clipboard tools on the system."""
        tools = {}

        # Test xclip (uses -version, not --version)
        try:
            subprocess.run(['xclip', '-version'],
                         capture_output=True, check=True)
            tools['xclip'] = True
        except (FileNotFoundError, subprocess.CalledProcessError):
            tools['xclip'] = False

        # Test xsel (uses --version)
        try:
            subprocess.run(['xsel', '--version'],
                         capture_output=True, check=True)
            tools['xsel'] = True
        except (FileNotFoundError, subprocess.CalledProcessError):
            tools['xsel'] = False

        # Test wl-copy (uses --version)
        try:
            subprocess.run(['wl-copy', '--version'],
                         capture_output=True, check=True)
            tools['wl-copy'] = True
        except (FileNotFoundError, subprocess.CalledProcessError):
            tools['wl-copy'] = False

        return tools

    def copy_to_clipboard(self, text: str) -> bool:
        """
        Copy text to clipboard using available tools.

        Args:
            text: Text to copy to clipboard

        Returns:
            True if successful, False otherwise
        """
        # Try xclip first (most common on X11)
        if self.available_tools.get('xclip', False):
            try:
                subprocess.run(['xclip', '-selection', 'clipboard'],
                             input=text, text=True, check=True, timeout=5)
                return True
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                pass

        # Try xsel as fallback
        if self.available_tools.get('xsel', False):
            try:
                subprocess.run(['xsel', '--clipboard', '--input'],
                             input=text, text=True, check=True, timeout=5)
                return True
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                pass

        # Try wl-copy for Wayland
        if self.available_tools.get('wl-copy', False):
            try:
                subprocess.run(['wl-copy'], input=text, text=True, check=True, timeout=5)
                return True
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                pass

        return False

    def copy_command(self, command: Command, variables: Optional[Dict[str, str]] = None) -> bool:
        """
        Copy command to clipboard with variable substitution.

        Args:
            command: Command object to copy
            variables: Dictionary of variable substitutions

        Returns:
            True if successful, False otherwise
        """
        processed_command = self.substitute_variables(command.content, variables or {})
        return self.copy_to_clipboard(processed_command)

    def copy_and_paste_command(self, command: Command, variables: Optional[Dict[str, str]] = None) -> bool:
        """
        Copy command to clipboard and automatically paste it.

        Args:
            command: Command object to copy and paste
            variables: Dictionary of variable substitutions

        Returns:
            True if successful, False otherwise
        """
        # First copy to clipboard
        if not self.copy_command(command, variables):
            return False

        # Then attempt auto-paste
        processed_command = self.substitute_variables(command.content, variables or {})
        return self._auto_paste(processed_command)

    def _auto_paste(self, text: str) -> bool:
        """
        Automatically paste text using platform-appropriate method.

        Args:
            text: Text to paste

        Returns:
            True if successful, False otherwise
        """
        system = platform.system().lower()

        # Small delay to ensure clipboard is ready
        time.sleep(0.1)

        try:
            if system == "linux":
                return self._auto_paste_linux(text)
            elif system == "darwin":  # macOS
                return self._auto_paste_macos(text)
            elif system == "windows":
                return self._auto_paste_windows(text)
            else:
                print(f"Auto-paste not supported on {system}")
                return False
        except Exception as e:
            print(f"Auto-paste failed: {e}")
            return False

    def _auto_paste_linux(self, text: str) -> bool:
        """Auto-paste on Linux using available tools."""
        # Try xdotool first (X11)
        try:
            subprocess.run(['xdotool', 'key', 'ctrl+shift+v'],
                         check=True, timeout=2)
            return True
        except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            pass

        # Try wtype (Wayland)
        try:
            subprocess.run(['wtype', '-M', 'ctrl', '-M', 'shift', 'v'],
                         check=True, timeout=2)
            return True
        except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            pass

        # Fallback: try basic Ctrl+V
        try:
            subprocess.run(['xdotool', 'key', 'ctrl+v'],
                         check=True, timeout=2)
            return True
        except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            pass

        return False

    def _auto_paste_macos(self, text: str) -> bool:
        """Auto-paste on macOS using AppleScript."""
        try:
            # Use Cmd+V on macOS
            subprocess.run([
                'osascript', '-e',
                'tell application "System Events" to keystroke "v" using command down'
            ], check=True, timeout=2)
            return True
        except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False

    def _auto_paste_windows(self, text: str) -> bool:
        """Auto-paste on Windows using PowerShell."""
        try:
            # Use Ctrl+V on Windows
            powershell_cmd = '''
            Add-Type -AssemblyName System.Windows.Forms
            [System.Windows.Forms.SendKeys]::SendWait("^v")
            '''
            subprocess.run(['powershell', '-Command', powershell_cmd],
                         check=True, timeout=2)
            return True
        except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False






    def substitute_variables(self, command_text: str, variables: Dict[str, str]) -> str:
        """
        Substitute variables in command text.

        Args:
            command_text: Original command text
            variables: Dictionary of variable substitutions

        Returns:
            Command text with variables substituted
        """
        result = command_text

        # Find all variables in the format $VARIABLE_NAME
        variable_pattern = r'\$([A-Z_][A-Z0-9_]*)'
        found_variables = re.findall(variable_pattern, command_text)

        for var_name in found_variables:
            if var_name in variables:
                # Replace $VARIABLE_NAME with the provided value
                result = result.replace(f'${var_name}', variables[var_name])

        return result

    def get_variables_from_command(self, command_text: str) -> list:
        """
        Extract variable names from command text.

        Args:
            command_text: Command text to analyze

        Returns:
            List of variable names found in the command
        """
        variable_pattern = r'\$([A-Z_][A-Z0-9_]*)'
        return re.findall(variable_pattern, command_text)

    def prompt_for_variables(self, command: Command) -> Dict[str, str]:
        """
        Prompt user for variable values using simple input.

        Args:
            command: Command object to get variables from

        Returns:
            Dictionary of variable name to value mappings
        """
        variables = self.get_variables_from_command(command.content)
        if not variables:
            return {}

        print(f"Command '{command.description}' requires the following variables:")
        values = {}

        for var_name in variables:
            value = input(f"Enter value for ${var_name}: ").strip()
            if value:
                values[var_name] = value

        return values

    def get_clipboard_status(self) -> Dict[str, bool]:
        """Get status of available clipboard tools."""
        return self.available_tools.copy()

    def check_clipboard_availability(self) -> bool:
        """Check if any clipboard tool is available."""
        return any(self.available_tools.values())


def main():
    """CLI interface for testing clipboard functionality."""
    import sys
    from .parser import MarkdownParser

    if len(sys.argv) < 2:
        print("Usage: python -m cmd_manager.clipboard <markdown_file>")
        sys.exit(1)

    file_path = sys.argv[1]
    parser = MarkdownParser()
    clipboard = ClipboardManager()

    try:
        commands = parser.parse_file(file_path)
        print(f"Loaded {len(commands)} commands from {file_path}")
        print(f"Clipboard tools available: {clipboard.get_clipboard_status()}")

        if not clipboard.check_clipboard_availability():
            print("No clipboard tools available! Install xclip, xsel, or wl-copy.")
            sys.exit(1)

        # Test with first command that has variables
        for cmd in commands:
            variables = clipboard.get_variables_from_command(cmd.content)
            if variables:
                print(f"\nTesting command: {cmd.description}")
                print(f"Original: {cmd.content}")
                print(f"Variables found: {variables}")

                # Test substitution
                test_vars = {var: f"TEST_{var}" for var in variables}
                substituted = clipboard.substitute_variables(cmd.content, test_vars)
                print(f"Substituted: {substituted}")

                success = clipboard.copy_to_clipboard(substituted)
                print(f"Copied to clipboard: {success}")
                break
        else:
            # Test with first command
            if commands:
                cmd = commands[0]
                print(f"\nTesting command: {cmd.description}")
                print(f"Command: {cmd.content}")
                success = clipboard.copy_command(cmd)
                print(f"Copied to clipboard: {success}")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()