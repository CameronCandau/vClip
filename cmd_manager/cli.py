#!/usr/bin/env python3
"""
CLI entry point for OpIndex.
"""

import sys
import argparse
from pathlib import Path
from typing import List, Optional

from . import __version__
from .config import ConfigManager
from .cache import CachedMarkdownParser
from .rofi import RofiInterface
from .clipboard import ClipboardManager
from .lint import MarkdownLinter


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        description="Operational command memory for markdown notes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  opindex                    # Show command selector
  opindex --workspace-menu   # Choose a workspace, then search
  opindex --workspace oscp   # Search a named workspace
  opindex --all              # Search across all workspaces
  opindex --browse           # Browse by workspace, then document
  opindex --config-path      # Show config file path
  opindex --create-config    # Create default config file
  opindex --clear-cache      # Clear command cache
  opindex --list-files       # List source files
  opindex --list-commands    # List all commands
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
        "--list-workspaces",
        action="store_true",
        help="List configured workspaces and exit"
    )

    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable caching for this run"
    )

    parser.add_argument(
        "--workspace-menu",
        action="store_true",
        help="Choose a workspace interactively before searching"
    )

    parser.add_argument(
        "--workspace",
        help="Search a specific workspace"
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Search across all workspaces"
    )

    parser.add_argument(
        "--browse",
        action="store_true",
        help="Browse by workspace and document before selecting a command"
    )

    parser.add_argument(
        "--lint-files",
        nargs="*",
        metavar="PATH",
        help="Lint specific markdown files. If no paths are given, lint the selected workspace sources."
    )

    parser.add_argument(
        "--version", "-v",
        action="version",
        version=f"opindex {__version__}"
    )

    return parser


def load_commands(config_manager: ConfigManager, use_cache: bool, source_files: List[str]):
    """Load commands from the configured sources."""
    config = config_manager.load_config()
    if config.cache.enabled and use_cache:
        parser = CachedMarkdownParser(config.cache.directory)
        return parser.parse_files_cached(source_files)

    from .parser import MarkdownParser
    parser = MarkdownParser()
    return parser.parse_files(source_files)


def annotate_command_workspaces(commands, workspace_file_map):
    """Attach workspace labels to parsed commands."""
    for cmd in commands:
        cmd.workspace = workspace_file_map.get(cmd.source_file, cmd.workspace)
    return commands


def lint_files(
    config_manager: ConfigManager,
    file_paths: List[str],
    workspace: Optional[str] = None,
    all_workspaces: bool = False
) -> int:
    """Lint markdown files against the OpIndex authoring standard."""
    try:
        if not file_paths:
            file_paths = config_manager.get_source_files(workspace=workspace, all_workspaces=all_workspaces)

        if not file_paths:
            print("No markdown files found to lint.")
            return 1

        linter = MarkdownLinter()
        results = [linter.lint_file(file_path) for file_path in file_paths]

        total_errors = 0
        total_warnings = 0
        problematic_files = 0

        for result in results:
            if not result.issues:
                continue

            problematic_files += 1
            print(result.file_path)
            for issue in result.issues:
                print(f"  {issue.severity.upper()}:{issue.line_number} [{issue.code}] {issue.message}")
            print()

            total_errors += result.error_count
            total_warnings += result.warning_count

        print(
            f"Linted {len(results)} file(s): "
            f"{problematic_files} with issues, "
            f"{total_errors} error(s), {total_warnings} warning(s)."
        )

        return 1 if total_errors else 0

    except Exception as e:
        print(f"Error linting files: {e}")
        return 1


def list_commands(
    config_manager: ConfigManager,
    workspace: Optional[str] = None,
    all_workspaces: bool = False,
    use_cache: bool = True
) -> int:
    """List all available commands."""
    try:
        source_files = config_manager.get_source_files(workspace=workspace, all_workspaces=all_workspaces)
        if not source_files:
            print("No source files found. Check your configuration.")
            return 1

        workspace_file_map = config_manager.get_workspace_file_map(workspace=None if all_workspaces else workspace)
        commands = annotate_command_workspaces(
            load_commands(config_manager, use_cache, source_files),
            workspace_file_map
        )

        print(f"Found {len(commands)} commands from {len(source_files)} files:\n")

        current_category = None
        for cmd in commands:
            if cmd.category != current_category:
                current_category = cmd.category
                print(f"# {current_category}")

            lang_str = f" [{cmd.language}]" if cmd.language else ""
            print(f"  - {cmd.description}{lang_str}")
            if cmd.workspace:
                print(f"    Workspace: {cmd.workspace}")
            print(f"    Source: {Path(cmd.source_file).stem}")
            print(f"    {cmd.content}")
            print()

        return 0

    except Exception as e:
        print(f"Error listing commands: {e}")
        return 1


def select_workspace(
    config_manager: ConfigManager,
    rofi: RofiInterface,
    allow_all: bool = False
) -> Optional[str]:
    """Select a workspace interactively."""
    workspace_names = config_manager.get_workspace_names()
    if not workspace_names:
        return None

    selected_workspace = rofi.select_workspace(workspace_names, include_all=allow_all)
    if selected_workspace == "__all__":
        return "__all__"
    return selected_workspace


def filter_commands_by_document(commands, document_path: str):
    """Limit commands to those originating from the selected document."""
    return [cmd for cmd in commands if cmd.source_file == document_path]


def main_selection_flow(
    config_manager: ConfigManager,
    use_cache: bool = True,
    workspace: Optional[str] = None,
    all_workspaces: bool = False,
    browse: bool = False,
    workspace_menu: bool = False
) -> int:
    """Main command selection flow."""
    try:
        # Load configuration
        config = config_manager.load_config()
        rofi = RofiInterface(config.rofi.get_rofi_args())

        if workspace_menu or browse:
            selected_workspace = select_workspace(config_manager, rofi, allow_all=not browse)
            if not selected_workspace:
                return 0
            if selected_workspace == "__all__":
                all_workspaces = True
                workspace = None
            else:
                workspace = selected_workspace
                all_workspaces = False

        source_files = config_manager.get_source_files(workspace=workspace, all_workspaces=all_workspaces)
        if not source_files:
            print("No source files found.")
            print("Add markdown files to your workspace configuration.")
            print(f"\nConfig file: {config_manager.config_path}")
            return 1

        workspace_file_map = config_manager.get_workspace_file_map(workspace=None if all_workspaces else workspace)
        commands = annotate_command_workspaces(
            load_commands(config_manager, use_cache, source_files),
            workspace_file_map
        )

        if not commands:
            print(f"No commands found in {len(source_files)} source files.")
            return 1

        if browse:
            documents = sorted(set(cmd.source_file for cmd in commands))
            label_to_document = {}
            document_labels = []
            for doc in documents:
                label = Path(doc).stem
                if label in label_to_document:
                    label = f"{label} ({Path(doc).parent.name})"
                label_to_document[label] = doc
                document_labels.append(label)

            selected_document_label = rofi.select_document(document_labels)
            if not selected_document_label:
                return 0
            selected_document = label_to_document.get(selected_document_label)
            if not selected_document:
                return 0
            commands = filter_commands_by_document(commands, selected_document)

        if config.rofi.use_markup:
            selected_command = rofi.select_command_with_preview(commands)
        else:
            selected_command = rofi.select_command(commands)

        if not selected_command:
            return 0

        clipboard = ClipboardManager()

        if not clipboard.check_clipboard_availability():
            print("No clipboard tools available!")
            print("Install one of: xclip, xsel, wl-copy")
            return 1

        success = clipboard.copy_command(selected_command)

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
        try:
            source_files = config_manager.get_source_files(
                workspace=args.workspace,
                all_workspaces=args.all
            )
            print(f"Source files ({len(source_files)}):")
            for file_path in source_files:
                print(f"  {file_path}")
            return 0
        except Exception as e:
            print(f"Error listing source files: {e}")
            return 1

    if args.list_workspaces:
        workspaces = config_manager.get_workspace_names()
        print(f"Workspaces ({len(workspaces)}):")
        for workspace_name in workspaces:
            suffix = " (default)" if workspace_name == config_manager.get_default_workspace() else ""
            print(f"  {workspace_name}{suffix}")
        return 0

    if args.lint_files is not None:
        return lint_files(
            config_manager,
            args.lint_files,
            workspace=args.workspace,
            all_workspaces=args.all
        )

    if args.clear_cache:
        config = config_manager.load_config()
        from .cache import CommandCache
        cache = CommandCache(config.cache.directory)
        removed = cache.clear_cache()
        print(f"Removed {removed} cache files")
        return 0

    if args.list_commands:
        return list_commands(
            config_manager,
            workspace=args.workspace,
            all_workspaces=args.all,
            use_cache=not args.no_cache
        )

    # Main selection flow
    return main_selection_flow(
        config_manager,
        not args.no_cache,
        workspace=args.workspace,
        all_workspaces=args.all,
        browse=args.browse,
        workspace_menu=args.workspace_menu
    )


if __name__ == "__main__":
    sys.exit(main())
