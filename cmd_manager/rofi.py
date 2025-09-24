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
        ]

        # Format commands with markup for better display
        rofi_input = "\n".join(self._format_command_with_markup(cmd) for cmd in commands)

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
        tags = self._escape_markup(", ".join(command.tags)) if command.tags else ""
        category = self._escape_markup(command.category) if command.category else ""

        # Format with markup
        if tags:
            return f"<b>{description}</b> <i>({tags})</i>"
        else:
            return f"<b>{description}</b>"

    def _escape_markup(self, text: str) -> str:
        """Escape special characters for pango markup."""
        return (text.replace("&", "&amp;")
                   .replace("<", "&lt;")
                   .replace(">", "&gt;")
                   .replace("'", "&apos;")
                   .replace('"', "&quot;"))

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
            # Search in description, tags, category, and command content
            searchable_text = " ".join([
                cmd.description.lower(),
                " ".join(cmd.tags).lower(),
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
            print(f"Tags: {', '.join(selected.tags)}")
        else:
            print("No command selected")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()