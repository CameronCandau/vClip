"""
Rofi integration for command selection.
"""

import subprocess
from typing import List, Optional, Tuple
from .parser import Command


class RofiInterface:
    """Interface for rofi command selection."""

    def __init__(self, rofi_args: Optional[List[str]] = None):
        """
        Initialize rofi interface.

        Args:
            rofi_args: Additional arguments to pass to rofi
        """
        self.rofi_args = rofi_args or [
            "-dmenu",
            "-i",  # case-insensitive
            "-p", "Commands",  # prompt
            "-format", "i",  # return index
            "-no-custom",  # don't allow custom input
        ]

    def select_command(self, commands: List[Command]) -> Optional[Command]:
        """
        Display commands in rofi and return selected command.

        Args:
            commands: List of Command objects to display

        Returns:
            Selected Command object or None if cancelled
        """
        if not commands:
            return None

        # Prepare rofi input - each line is a command formatted for display
        rofi_input = "\n".join(cmd.format_for_rofi() for cmd in commands)

        try:
            # Run rofi and get the selected index
            result = subprocess.run(
                ["rofi"] + self.rofi_args,
                input=rofi_input,
                text=True,
                capture_output=True,
                check=False
            )

            # Check if user cancelled (ESC pressed)
            if result.returncode != 0:
                return None

            # Parse the returned index
            try:
                selected_index = int(result.stdout.strip())
                if 0 <= selected_index < len(commands):
                    return commands[selected_index]
            except (ValueError, IndexError):
                return None

        except FileNotFoundError:
            raise RuntimeError("rofi not found. Please install rofi: sudo apt install rofi")
        except Exception as e:
            raise RuntimeError(f"Error running rofi: {e}")

        return None

    def select_command_with_preview(self, commands: List[Command]) -> Optional[Command]:
        """
        Display commands with preview using rofi's advanced features.

        Args:
            commands: List of Command objects to display

        Returns:
            Selected Command object or None if cancelled
        """
        if not commands:
            return None

        # Use a unique separator between entries so each two-line command is treated as one entry
        # We use a character sequence that's unlikely to appear in commands or markup
        ENTRY_SEPARATOR = "\x1f"  # ASCII Unit Separator

        # Enhanced rofi args with preview
        enhanced_args = [
            "-dmenu",
            "-i",
            "-p", "Commands",
            "-format", "i",
            "-no-custom",
            "-markup-rows",  # Enable markup
            "-columns", "1",
            "-lines", str(min(15, len(commands))),  # Show up to 15 items
            "-width", "60",  # Window width as percentage of screen
            "-eh", "2",  # Element height (2 lines per entry for our two-line format)
            "-sep", ENTRY_SEPARATOR,  # Use ASCII Unit Separator to separate entries
            "-theme-str", "listview { scrollbar: true; }",  # Show scrollbar
            "-theme-str", "window { width: 60%; }",  # Alternative width setting
        ]

        # Format commands with markup for better display
        # Each command is 2 lines (description + content preview), separated by unit separators
        rofi_input = ENTRY_SEPARATOR.join(self._format_command_with_markup(cmd) for cmd in commands)

        try:
            result = subprocess.run(
                ["rofi"] + enhanced_args,
                input=rofi_input,
                text=True,
                capture_output=True,
                check=False
            )

            if result.returncode != 0:
                return None

            try:
                # Now rofi returns the ENTRY index directly (since we're using custom separator)
                selected_index = int(result.stdout.strip())
                if 0 <= selected_index < len(commands):
                    return commands[selected_index]
            except (ValueError, IndexError):
                return None

        except FileNotFoundError:
            raise RuntimeError("rofi not found. Please install rofi: sudo apt install rofi")
        except Exception as e:
            raise RuntimeError(f"Error running rofi: {e}")

        return None

    def _format_command_with_markup(self, command: Command) -> str:
        """Format command with pango markup for rofi display."""
        # Escape special characters for pango markup
        description = self._escape_markup(command.description)
        language = self._escape_markup(command.language) if command.language else ""

        # Escape and truncate command content for display
        cmd_content = self._escape_markup(command.content)
        # Truncate long commands (keep first line if multiline, or truncate at 80 chars)
        if '\n' in cmd_content:
            cmd_content = cmd_content.split('\n')[0] + '...'
        if len(cmd_content) > 80:
            cmd_content = cmd_content[:77] + '...'

        # Format with markup: bold description, optional language tag, and command in small dimmed text
        title_line = f"<b>{description}</b>"
        if language:
            title_line += f" <i>[{language}]</i>"

        # Add command content on second line with small, dimmed text
        cmd_line = f"<small><span alpha='60%'>{cmd_content}</span></small>"

        return f"{title_line}\n{cmd_line}"

    def _escape_markup(self, text: str) -> str:
        """Escape special characters for pango markup."""
        return (text.replace("&", "&amp;")
                   .replace("<", "&lt;")
                   .replace(">", "&gt;")
                   .replace("'", "&apos;")
                   .replace('"', "&quot;"))

    def prompt_input(self, prompt: str, default: str = '') -> Optional[str]:
        """
        Show a rofi text-input dialog and return what the user typed.

        Args:
            prompt: Label shown next to the input field.
            default: Pre-filled value (user can clear or keep it).

        Returns:
            The entered string (may be empty), or None if user cancelled (ESC).
        """
        args = ['rofi', '-dmenu', '-p', prompt, '-lines', '0', '-i']
        if default:
            args += ['-filter', default]

        try:
            result = subprocess.run(
                args,
                input='',
                text=True,
                capture_output=True,
                check=False
            )
            if result.returncode != 0:
                return None
            return result.stdout.strip()
        except FileNotFoundError:
            raise RuntimeError("rofi not found. Please install rofi: sudo apt install rofi")

    def filter_commands(self, commands: List[Command], query: str) -> List[Command]:
        """
        Filter commands based on a search query.

        Args:
            commands: List of commands to filter
            query: Search query

        Returns:
            Filtered list of commands
        """
        if not query:
            return commands

        query = query.lower()
        filtered = []

        for cmd in commands:
            # Search in description, category, and command content
            searchable_text = " ".join([
                cmd.description.lower(),
                cmd.category.lower(),
                cmd.content.lower()
            ])

            if query in searchable_text:
                filtered.append(cmd)

        return filtered


def main():
    """CLI interface for testing rofi integration."""
    import sys
    from .parser import MarkdownParser

    if len(sys.argv) < 2:
        print("Usage: python -m cmd_manager.rofi <markdown_file>")
        sys.exit(1)

    file_path = sys.argv[1]
    parser = MarkdownParser()
    rofi = RofiInterface()

    try:
        commands = parser.parse_file(file_path)
        print(f"Loaded {len(commands)} commands from {file_path}")

        selected = rofi.select_command_with_preview(commands)
        if selected:
            print(f"Selected command: {selected.description}")
            print(f"Command: {selected.content}")
            print(f"Language: {selected.language if selected.language else 'None'}")
        else:
            print("No command selected")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()