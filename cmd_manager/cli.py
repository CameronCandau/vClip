#!/usr/bin/env python3
"""
CLI entry point for vclip - Command Snippet Manager
"""

import sys
import argparse
from pathlib import Path

from .config import ConfigManager
from .cache import CachedMarkdownParser
from .rofi import RofiInterface
from .clipboard import ClipboardManager


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        description="Command Snippet Manager with rofi integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  vclip                    # Show command selector
  vclip --config-path      # Show config file path
  vclip --create-config    # Create default config file
  vclip --clear-cache      # Clear command cache
  vclip --list-files       # List source files
  vclip --list-commands    # List all commands
        """
    )

    parser.add_argument(
        "--config", "-c",
        help="Path to configuration file"
    )

    parser.add_argument(
        "--config-path",
        action="store_true",
        help="Show configuration file path and exit"
    )

    parser.add_argument(
        "--create-config",
        action="store_true",
        help="Create default configuration file"
    )

    parser.add_argument(
        "--clear-cache",
        action="store_true",
        help="Clear command cache"
    )

    parser.add_argument(
        "--list-files",
        action="store_true",
        help="List source files and exit"
    )

    parser.add_argument(
        "--list-commands",
        action="store_true",
        help="List all commands and exit"
    )

    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable caching for this run"
    )

    parser.add_argument(
        "--no-prompt",
        action="store_true",
        help="Don't prompt for missing variables (useful for keyboard shortcuts)"
    )

    parser.add_argument(
        "--auto-paste",
        action="store_true",
        help="Automatically paste the command after copying to clipboard"
    )

    parser.add_argument(
        "--version", "-v",
        action="version",
        version="vclip 0.1.0"
    )

    return parser


def list_commands(config_manager: ConfigManager) -> int:
    """List all available commands."""
    try:
        source_files = config_manager.get_source_files()
        if not source_files:
            print("No source files found. Check your configuration.")
            return 1

        config = config_manager.load_config()
        if config.cache.enabled:
            parser = CachedMarkdownParser(config.cache.directory)
            commands = parser.parse_files_cached(source_files)
        else:
            from .parser import MarkdownParser
            parser = MarkdownParser()
            commands = parser.parse_files(source_files)

        print(f"Found {len(commands)} commands from {len(source_files)} files:\n")

        current_category = None
        for cmd in commands:
            if cmd.category != current_category:
                current_category = cmd.category
                print(f"# {current_category}")

            lang_str = f" [{cmd.language}]" if cmd.language else ""
            print(f"  - {cmd.description}{lang_str}")
            print(f"    {cmd.content}")
            print()

        return 0

    except Exception as e:
        print(f"Error listing commands: {e}")
        return 1


def main_selection_flow(config_manager: ConfigManager, use_cache: bool = True, no_prompt: bool = False, auto_paste: bool = False) -> int:
    """Main command selection flow."""
    try:
        # Load configuration
        config = config_manager.load_config()

        # Get source files
        source_files = config_manager.get_source_files()
        if not source_files:
            print("No source files found.")
            print("Add markdown files to your configuration or check the default paths:")
            print("  - ~/Documents/commands/")
            print("  - ~/.local/share/vclip/")
            print(f"\nConfig file: {config_manager.config_path}")
            return 1

        # Parse commands
        if config.cache.enabled and use_cache:
            parser = CachedMarkdownParser(config.cache.directory)
            commands = parser.parse_files_cached(source_files)
        else:
            from .parser import MarkdownParser
            parser = MarkdownParser()
            commands = parser.parse_files(source_files)

        if not commands:
            print(f"No commands found in {len(source_files)} source files.")
            return 1

        # Initialize rofi interface
        rofi = RofiInterface(config.rofi.get_rofi_args())

        # Select command
        if config.rofi.use_markup:
            selected_command = rofi.select_command_with_preview(commands)
        else:
            selected_command = rofi.select_command(commands)

        if not selected_command:
            # User cancelled selection
            return 0

        # Initialize clipboard manager with config-defined variables
        clipboard = ClipboardManager(config.variables)

        if not clipboard.check_clipboard_availability():
            print("No clipboard tools available!")
            print("Install one of: xclip, xsel, wl-copy")
            return 1

        # Copy command to clipboard (variable substitution happens inside)
        if auto_paste:
            success = clipboard.copy_and_paste_command(selected_command, rofi=rofi, no_prompt=no_prompt)
        else:
            success = clipboard.copy_command(selected_command, rofi=rofi, no_prompt=no_prompt)

        if success:
            print(f"Copied: {selected_command.description}")
        else:
            print("Failed to copy command to clipboard")
            return 1

        return 0

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


def main():
    """Main entry point."""
    parser = create_argument_parser()
    args = parser.parse_args()

    # Initialize config manager
    config_manager = ConfigManager(args.config)

    # Handle config-related commands
    if args.config_path:
        print(f"Configuration file: {config_manager.config_path}")
        return 0

    if args.create_config:
        if config_manager.create_default_config_file():
            print(f"Created configuration file: {config_manager.config_path}")
        else:
            print("Failed to create configuration file")
            return 1
        return 0

    if args.list_files:
        source_files = config_manager.get_source_files()
        print(f"Source files ({len(source_files)}):")
        for file_path in source_files:
            print(f"  {file_path}")
        return 0

    if args.clear_cache:
        config = config_manager.load_config()
        from .cache import CommandCache
        cache = CommandCache(config.cache.directory)
        removed = cache.clear_cache()
        print(f"Removed {removed} cache files")
        return 0

    if args.list_commands:
        return list_commands(config_manager)

    # Main selection flow
    return main_selection_flow(config_manager, not args.no_cache, args.no_prompt, args.auto_paste)


if __name__ == "__main__":
    sys.exit(main())