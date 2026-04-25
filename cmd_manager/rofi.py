"""
Rofi integration for command selection.
"""

import subprocess
from pathlib import Path
from typing import List, Optional, Union
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

    def select_workspace(self, workspaces: List[str], include_all: bool = False) -> Optional[str]:
        """Display workspace names in rofi and return the selection."""
        if not workspaces:
            return None

        entries = list(workspaces)
        if include_all:
            entries.append("All Workspaces")

        selected_index = self._run_rofi_index(
            entries,
            ["-dmenu", "-i", "-p", "Workspace", "-format", "i", "-no-custom"]
        )
        if selected_index is None:
            return None

        selected_value = entries[selected_index]
        if selected_value == "All Workspaces":
            return "__all__"

        return selected_value

    def select_document(self, documents: List[str]) -> Optional[str]:
        """Display source document names in rofi and return the selection."""
        selected_index = self._run_rofi_index(
            documents,
            ["-dmenu", "-i", "-p", "Document", "-format", "i", "-no-custom"]
        )
        if selected_index is None:
            return None

        return documents[selected_index]

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
        selected_index = self._run_rofi_index(
            [self._format_command_plain(cmd) for cmd in commands],
            self.rofi_args
        )
        if selected_index is None:
            return None

        if 0 <= selected_index < len(commands):
            return commands[selected_index]

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
        selected_index = self._run_rofi_index(rofi_input, enhanced_args, use_joined_input=True)
        if selected_index is None:
            return None

        if 0 <= selected_index < len(commands):
            return commands[selected_index]

        return None

    def _format_command_with_markup(self, command: Command) -> str:
        """Format command with pango markup for rofi display."""
        # Escape special characters for pango markup
        description = self._escape_markup(command.description)
        language = self._escape_markup(command.language) if command.language else ""
        source_context = self._escape_markup(self._build_source_context(command))

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

        context_suffix = f"  <span alpha='50%'>{source_context}</span>" if source_context else ""
        cmd_line = f"<small><span alpha='60%'>{cmd_content}</span>{context_suffix}</small>"

        return f"{title_line}\n{cmd_line}"

    def _format_command_plain(self, command: Command) -> str:
        """Format command for non-markup rofi mode."""
        description = command.format_for_rofi()
        source_context = self._build_source_context(command)
        if source_context:
            return f"{description} - {source_context}"
        return description

    def _build_source_context(self, command: Command) -> str:
        """Build a short source label for display."""
        doc_name = Path(command.source_file).stem
        if command.workspace:
            return f"{command.workspace} / {doc_name}"
        return doc_name

    def _run_rofi_index(
        self,
        entries: Union[List[str], str],
        args: List[str],
        use_joined_input: bool = False
    ) -> Optional[int]:
        """Run rofi and return the selected index."""
        if use_joined_input:
            rofi_input = entries
        else:
            rofi_input = "\n".join(entries)

        try:
            result = subprocess.run(
                ["rofi"] + args,
                input=rofi_input,
                text=True,
                capture_output=True,
                check=False
            )

            if result.returncode != 0:
                return None

            try:
                return int(result.stdout.strip())
            except ValueError:
                return None

        except FileNotFoundError:
            raise RuntimeError("rofi not found. Please install rofi: sudo apt install rofi")
        except Exception as e:
            raise RuntimeError(f"Error running rofi: {e}")

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
