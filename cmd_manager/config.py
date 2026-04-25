"""
Configuration management for vclip.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict, field


@dataclass
class RofiConfig:
    """Configuration for rofi interface."""
    args: List[str]
    use_markup: bool = True
    max_lines: int = 15
    prompt: str = "Commands"
    window_width: int = 60  # Window width as percentage (0-100)
    element_height: int = 2  # Lines per entry

    def get_rofi_args(self) -> List[str]:
        """Get complete rofi arguments list."""
        base_args = [
            "-dmenu",
            "-i",  # case-insensitive
            "-p", self.prompt,
            "-format", "i",  # return index
            "-no-custom",  # don't allow custom input
            "-lines", str(self.max_lines),
        ]

        if self.use_markup:
            base_args.append("-markup-rows")

        # Add window size configuration
        if self.window_width:
            base_args.extend(["-width", str(self.window_width)])

        if self.element_height:
            base_args.extend(["-eh", str(self.element_height)])

        # Add scrollbar for better navigation
        base_args.extend(["-theme-str", "listview { scrollbar: true; }"])

        # Add custom args
        return base_args + self.args


@dataclass
class SourceConfig:
    """Configuration for source files and directories."""
    files: List[str]
    directories: List[str]
    recursive: bool = True
    file_patterns: List[str] = None

    def __post_init__(self):
        if self.file_patterns is None:
            self.file_patterns = ["*.md", "*.markdown"]


@dataclass
class CacheConfig:
    """Configuration for caching system."""
    enabled: bool = True
    directory: Optional[str] = None
    auto_cleanup: bool = True


@dataclass
class VclipConfig:
    """Main configuration class for vclip."""
    sources: Optional[SourceConfig]
    rofi: RofiConfig
    cache: CacheConfig
    workspaces: Dict[str, SourceConfig] = field(default_factory=dict)
    default_workspace: Optional[str] = None
    substitute_variables: bool = False
    variables: Dict[str, str] = None

    def __post_init__(self):
        if self.variables is None:
            self.variables = {}


class ConfigManager:
    """Manages configuration loading and saving."""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager.

        Args:
            config_path: Path to config file. If None, uses default locations.
        """
        self.config_path = self._resolve_config_path(config_path)
        self.config: Optional[VclipConfig] = None

    def _resolve_config_path(self, config_path: Optional[str]) -> Path:
        """Resolve configuration file path using XDG standards."""
        if config_path:
            return Path(config_path)

        # Try XDG_CONFIG_HOME first
        xdg_config = os.environ.get('XDG_CONFIG_HOME')
        if xdg_config:
            config_dir = Path(xdg_config) / 'vclip'
        else:
            config_dir = Path.home() / '.config' / 'vclip'

        return config_dir / 'config.yaml'

    def _get_default_config(self) -> VclipConfig:
        """Get default configuration."""
        home_dir = Path.home()
        default_sources = SourceConfig(
            files=[],
            directories=[
                str(home_dir / 'Documents' / 'commands'),
                str(home_dir / '.local' / 'share' / 'vclip'),
            ],
            recursive=True,
            file_patterns=["*.md", "*.markdown"]
        )

        return VclipConfig(
            sources=None,
            workspaces={'default': default_sources},
            default_workspace='default',
            rofi=RofiConfig(
                args=[],
                use_markup=True,
                max_lines=15,
                prompt="Commands",
                window_width=60,
                element_height=2
            ),
            cache=CacheConfig(
                enabled=True,
                directory=None,  # Will use default cache directory
                auto_cleanup=True
            ),
            substitute_variables=False,
            variables={}
        )

    def load_config(self) -> VclipConfig:
        """Load configuration from file or create default."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f) or {}

                # Convert dict to config objects
                config = self._dict_to_config(data)
                self.config = config
                return config

            except (yaml.YAMLError, KeyError, TypeError) as e:
                print(f"Warning: Error loading config from {self.config_path}: {e}")
                print("Using default configuration.")

        # Return default config
        self.config = self._get_default_config()
        return self.config

    def save_config(self, config: Optional[VclipConfig] = None) -> bool:
        """Save configuration to file."""
        if config is None:
            config = self.config

        if config is None:
            return False

        try:
            # Create config directory if it doesn't exist
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            # Convert config to dict
            config_dict = self._config_to_dict(config)

            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_dict, f, default_flow_style=False, indent=2)

            return True

        except (OSError, yaml.YAMLError) as e:
            print(f"Error saving config to {self.config_path}: {e}")
            return False

    def _dict_to_config(self, data: Dict[str, Any]) -> VclipConfig:
        """Convert dictionary to VclipConfig object."""
        sources = None
        sources_data = data.get('sources')
        if isinstance(sources_data, dict):
            sources = self._parse_source_config(sources_data)

        workspaces_data = data.get('workspaces', {})
        workspaces = {
            name: self._parse_source_config(workspace_data)
            for name, workspace_data in workspaces_data.items()
            if isinstance(workspace_data, dict)
        }

        if not workspaces and sources is not None:
            workspaces = {'default': sources}

        rofi_data = data.get('rofi', {})
        rofi = RofiConfig(
            args=rofi_data.get('args', []),
            use_markup=rofi_data.get('use_markup', True),
            max_lines=rofi_data.get('max_lines', 15),
            prompt=rofi_data.get('prompt', "Commands"),
            window_width=rofi_data.get('window_width', 60),
            element_height=rofi_data.get('element_height', 2)
        )

        cache_data = data.get('cache', {})
        cache = CacheConfig(
            enabled=cache_data.get('enabled', True),
            directory=cache_data.get('directory'),
            auto_cleanup=cache_data.get('auto_cleanup', True)
        )

        return VclipConfig(
            sources=sources,
            workspaces=workspaces,
            default_workspace=data.get('default_workspace') or self._get_initial_default_workspace(workspaces),
            rofi=rofi,
            cache=cache,
            substitute_variables=data.get('substitute_variables', False),
            variables=data.get('variables', {})
        )

    def _parse_source_config(self, data: Dict[str, Any]) -> SourceConfig:
        """Convert source configuration dictionary into SourceConfig."""
        return SourceConfig(
            files=data.get('files', []),
            directories=data.get('directories', []),
            recursive=data.get('recursive', True),
            file_patterns=data.get('file_patterns', ["*.md", "*.markdown"])
        )

    def _get_initial_default_workspace(self, workspaces: Dict[str, SourceConfig]) -> Optional[str]:
        """Pick a default workspace when one is not explicitly configured."""
        if 'default' in workspaces:
            return 'default'
        if workspaces:
            return sorted(workspaces.keys())[0]
        return None

    def _config_to_dict(self, config: VclipConfig) -> Dict[str, Any]:
        """Convert VclipConfig object to dictionary."""
        config_dict = {
            'rofi': asdict(config.rofi),
            'cache': asdict(config.cache),
            'substitute_variables': config.substitute_variables,
            'variables': config.variables
        }

        if config.default_workspace:
            config_dict['default_workspace'] = config.default_workspace

        if config.workspaces:
            config_dict['workspaces'] = {
                name: asdict(source_config)
                for name, source_config in config.workspaces.items()
            }
        elif config.sources is not None:
            config_dict['sources'] = asdict(config.sources)

        return config_dict

    def get_workspace_names(self) -> List[str]:
        """Return configured workspace names."""
        if not self.config:
            self.load_config()

        return sorted(self.config.workspaces.keys())

    def get_default_workspace(self) -> Optional[str]:
        """Return the configured default workspace."""
        if not self.config:
            self.load_config()

        default_workspace = self.config.default_workspace
        if default_workspace in self.config.workspaces:
            return default_workspace

        return self._get_initial_default_workspace(self.config.workspaces)

    def get_source_files(
        self,
        workspace: Optional[str] = None,
        all_workspaces: bool = False
    ) -> List[str]:
        """Get source files for a workspace, or across all workspaces."""
        if not self.config:
            self.load_config()

        source_configs = self._get_selected_source_configs(workspace, all_workspaces)
        all_files: List[str] = []

        for source_config in source_configs:
            all_files.extend(self._collect_source_files(source_config))

        # Remove duplicates and sort
        return sorted(list(set(all_files)))

    def get_workspace_file_map(self, workspace: Optional[str] = None) -> Dict[str, str]:
        """Return a mapping of source file to workspace name."""
        if not self.config:
            self.load_config()

        workspace_file_map: Dict[str, str] = {}

        for workspace_name, source_config in self.config.workspaces.items():
            if workspace and workspace_name != workspace:
                continue

            for file_path in self._collect_source_files(source_config):
                workspace_file_map[file_path] = workspace_name

        return workspace_file_map

    def _get_selected_source_configs(
        self,
        workspace: Optional[str],
        all_workspaces: bool
    ) -> List[SourceConfig]:
        """Resolve the source configs addressed by the current CLI mode."""
        if all_workspaces:
            return [self.config.workspaces[name] for name in self.get_workspace_names()]

        if workspace:
            if workspace not in self.config.workspaces:
                raise ValueError(f"Workspace not found: {workspace}")
            return [self.config.workspaces[workspace]]

        default_workspace = self.get_default_workspace()
        if default_workspace:
            return [self.config.workspaces[default_workspace]]

        if self.config.sources is not None:
            return [self.config.sources]

        return []

    def _collect_source_files(self, source_config: SourceConfig) -> List[str]:
        """Collect files for a single source configuration."""
        all_files = []

        # Add explicitly configured files
        for file_path in source_config.files:
            path = Path(file_path).expanduser()
            if path.exists() and path.is_file():
                all_files.append(str(path))

        # Add files from directories
        for dir_path in source_config.directories:
            path = Path(dir_path).expanduser()
            if path.exists() and path.is_dir():
                for pattern in source_config.file_patterns:
                    if source_config.recursive:
                        files = path.rglob(pattern)
                    else:
                        files = path.glob(pattern)

                    for file_path in files:
                        if file_path.is_file():
                            all_files.append(str(file_path))

        return sorted(list(set(all_files)))

    def create_default_config_file(self) -> bool:
        """Create default config file if it doesn't exist."""
        if self.config_path.exists():
            return True

        default_config = self._get_default_config()
        return self.save_config(default_config)


def main():
    """CLI interface for testing configuration."""
    import sys

    action = sys.argv[1] if len(sys.argv) > 1 else "show"

    config_manager = ConfigManager()

    if action == "show":
        config = config_manager.load_config()
        print("Current configuration:")
        print(yaml.dump(config_manager._config_to_dict(config), indent=2))

    elif action == "create":
        success = config_manager.create_default_config_file()
        if success:
            print(f"Created default config at: {config_manager.config_path}")
        else:
            print("Failed to create config file")

    elif action == "files":
        files = config_manager.get_source_files()
        print(f"Source files ({len(files)}):")
        for file_path in files:
            print(f"  {file_path}")

    elif action == "path":
        print(f"Config file path: {config_manager.config_path}")

    else:
        print("Usage: python -m cmd_manager.config [show|create|files|path]")
        sys.exit(1)


if __name__ == "__main__":
    main()
