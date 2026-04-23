"""
Clipboard integration for copying commands.
"""

import subprocess
import time
import platform
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

    def prepare_command_text(
        self,
        command: Command,
        rofi=None,
        no_prompt: bool = False,
        substitute_variables: bool = False
    ) -> Optional[str]:
        """
        Prepare command text for clipboard copy.

        Args:
            command: Command object to render
            rofi: RofiInterface instance for prompting (None skips interactive prompts)
            no_prompt: If True, use config + cache only, no interactive prompts
            substitute_variables: If True, resolve and substitute $VARS before copying

        Returns:
            Final text to copy, or None if user cancelled.
        """
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
        """
        Copy command to clipboard.

        If variable substitution is enabled and the command contains $UPPERCASE_VARS,
        prompts the user via rofi for values, pre-filled from the session cache.
        Config-defined vars are substituted silently. If the user cancels (ESC),
        the copy is aborted.

        Args:
            command: Command object to copy
            rofi: RofiInterface instance for prompting (None skips interactive prompts)
            no_prompt: If True, use config + cache only, no interactive prompts
            substitute_variables: If True, resolve and substitute $VARS before copying

        Returns:
            True if successful, False otherwise
        """
        text = self.prepare_command_text(
            command,
            rofi=rofi,
            no_prompt=no_prompt,
            substitute_variables=substitute_variables
        )
        if text is None:
            return False

        return self.copy_to_clipboard(text)

    def copy_and_paste_command(
        self,
        command: Command,
        rofi=None,
        no_prompt: bool = False,
        substitute_variables: bool = False
    ) -> bool:
        """
        Copy command to clipboard and automatically paste it.

        Args:
            command: Command object to copy and paste
            rofi: RofiInterface instance for variable prompting
            no_prompt: If True, use config + cache only, no interactive prompts
            substitute_variables: If True, resolve and substitute $VARS before copying

        Returns:
            True if successful, False otherwise
        """
        text = self.prepare_command_text(
            command,
            rofi=rofi,
            no_prompt=no_prompt,
            substitute_variables=substitute_variables
        )
        if text is None:
            return False
        if not self.copy_to_clipboard(text):
            return False
        return self._auto_paste(text)

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
