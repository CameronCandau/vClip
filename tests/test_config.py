"""
Tests for the configuration module.
"""

import pytest
import tempfile
import yaml
from pathlib import Path
from cmd_manager.config import ConfigManager, VclipConfig, SourceConfig, RofiConfig, CacheConfig


class TestConfigManager:
    """Test the ConfigManager class."""

    def test_default_config(self):
        """Test that default config is properly structured."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.yaml"
            manager = ConfigManager(str(config_path))

            config = manager.load_config()

            assert isinstance(config, VclipConfig)
            assert isinstance(config.sources, SourceConfig)
            assert isinstance(config.rofi, RofiConfig)
            assert isinstance(config.cache, CacheConfig)
            assert isinstance(config.variables, dict)

    def test_load_config_from_file(self):
        """Test loading configuration from file."""
        config_data = {
            'sources': {
                'files': ['/test/file.md'],
                'directories': ['/test/dir'],
                'recursive': False,
                'file_patterns': ['*.md']
            },
            'rofi': {
                'args': ['-theme', 'dark'],
                'use_markup': False,
                'max_lines': 20,
                'prompt': 'Test Commands'
            },
            'cache': {
                'enabled': False,
                'directory': '/custom/cache',
                'auto_cleanup': False
            },
            'variables': {
                'TEST_VAR': 'test_value'
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name

        try:
            manager = ConfigManager(config_path)
            config = manager.load_config()

            # Check sources
            assert config.sources.files == ['/test/file.md']
            assert config.sources.directories == ['/test/dir']
            assert config.sources.recursive is False
            assert config.sources.file_patterns == ['*.md']

            # Check rofi
            assert config.rofi.args == ['-theme', 'dark']
            assert config.rofi.use_markup is False
            assert config.rofi.max_lines == 20
            assert config.rofi.prompt == 'Test Commands'

            # Check cache
            assert config.cache.enabled is False
            assert config.cache.directory == '/custom/cache'
            assert config.cache.auto_cleanup is False

            # Check variables
            assert config.variables == {'TEST_VAR': 'test_value'}

        finally:
            Path(config_path).unlink()

    def test_save_config(self):
        """Test saving configuration to file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.yaml"
            manager = ConfigManager(str(config_path))

            # Create custom config
            config = VclipConfig(
                sources=SourceConfig(
                    files=['/test.md'],
                    directories=['/test'],
                    recursive=True,
                    file_patterns=['*.md']
                ),
                rofi=RofiConfig(
                    args=[],
                    use_markup=True,
                    max_lines=15,
                    prompt="Commands"
                ),
                cache=CacheConfig(
                    enabled=True,
                    directory=None,
                    auto_cleanup=True
                ),
                variables={'VAR': 'value'}
            )

            # Save config
            success = manager.save_config(config)
            assert success is True
            assert config_path.exists()

            # Load and verify
            with open(config_path, 'r') as f:
                saved_data = yaml.safe_load(f)

            assert saved_data['sources']['files'] == ['/test.md']
            assert saved_data['rofi']['prompt'] == 'Commands'
            assert saved_data['variables'] == {'VAR': 'value'}

    def test_get_source_files_explicit_files(self):
        """Test getting source files from explicit file list."""
        config_data = {
            'sources': {
                'files': [],  # Will be set to existing files
                'directories': [],
                'recursive': True,
                'file_patterns': ['*.md']
            }
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            test_file1 = Path(temp_dir) / "test1.md"
            test_file2 = Path(temp_dir) / "test2.md"
            test_file1.write_text("# Test")
            test_file2.write_text("# Test")

            # Update config with actual file paths
            config_data['sources']['files'] = [str(test_file1), str(test_file2)]

            config_path = Path(temp_dir) / "config.yaml"
            with open(config_path, 'w') as f:
                yaml.dump(config_data, f)

            manager = ConfigManager(str(config_path))
            source_files = manager.get_source_files()

            assert len(source_files) == 2
            assert str(test_file1) in source_files
            assert str(test_file2) in source_files

    def test_get_source_files_from_directories(self):
        """Test getting source files from directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create directory structure
            sub_dir = temp_path / "subdir"
            sub_dir.mkdir()

            # Create test files
            (temp_path / "file1.md").write_text("# Test")
            (temp_path / "file2.markdown").write_text("# Test")
            (temp_path / "file3.txt").write_text("# Test")  # Should be ignored
            (sub_dir / "file4.md").write_text("# Test")

            config_data = {
                'sources': {
                    'files': [],
                    'directories': [str(temp_path)],
                    'recursive': True,
                    'file_patterns': ['*.md', '*.markdown']
                }
            }

            config_path = temp_path / "config.yaml"
            with open(config_path, 'w') as f:
                yaml.dump(config_data, f)

            manager = ConfigManager(str(config_path))
            source_files = manager.get_source_files()

            assert len(source_files) == 3  # file1.md, file2.markdown, file4.md
            assert str(temp_path / "file1.md") in source_files
            assert str(temp_path / "file2.markdown") in source_files
            assert str(sub_dir / "file4.md") in source_files
            assert str(temp_path / "file3.txt") not in source_files

    def test_get_source_files_non_recursive(self):
        """Test getting source files without recursion."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create directory structure
            sub_dir = temp_path / "subdir"
            sub_dir.mkdir()

            # Create test files
            (temp_path / "file1.md").write_text("# Test")
            (sub_dir / "file2.md").write_text("# Test")

            config_data = {
                'sources': {
                    'files': [],
                    'directories': [str(temp_path)],
                    'recursive': False,  # Non-recursive
                    'file_patterns': ['*.md']
                }
            }

            config_path = temp_path / "config.yaml"
            with open(config_path, 'w') as f:
                yaml.dump(config_data, f)

            manager = ConfigManager(str(config_path))
            source_files = manager.get_source_files()

            assert len(source_files) == 1  # Only file1.md
            assert str(temp_path / "file1.md") in source_files
            assert str(sub_dir / "file2.md") not in source_files

    def test_create_default_config_file(self):
        """Test creating default config file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.yaml"
            manager = ConfigManager(str(config_path))

            success = manager.create_default_config_file()
            assert success is True
            assert config_path.exists()

            # Verify it's valid YAML and contains expected sections
            with open(config_path, 'r') as f:
                data = yaml.safe_load(f)

            assert 'sources' in data
            assert 'rofi' in data
            assert 'cache' in data
            assert 'variables' in data

    def test_config_file_already_exists(self):
        """Test that create_default_config_file returns True if file exists."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("existing: config")
            config_path = f.name

        try:
            manager = ConfigManager(config_path)
            success = manager.create_default_config_file()
            assert success is True  # Should return True because file exists

        finally:
            Path(config_path).unlink()


class TestRofiConfig:
    """Test the RofiConfig class."""

    def test_get_rofi_args_with_markup(self):
        """Test rofi args generation with markup enabled."""
        rofi_config = RofiConfig(
            args=['-theme', 'dark'],
            use_markup=True,
            max_lines=20,
            prompt="Test"
        )

        args = rofi_config.get_rofi_args()

        assert '-dmenu' in args
        assert '-i' in args
        assert '-p' in args and 'Test' in args
        assert '-format' in args and 'i' in args
        assert '-no-custom' in args
        assert '-lines' in args and '20' in args
        assert '-markup-rows' in args
        assert '-theme' in args and 'dark' in args

    def test_get_rofi_args_without_markup(self):
        """Test rofi args generation with markup disabled."""
        rofi_config = RofiConfig(
            args=[],
            use_markup=False,
            max_lines=10,
            prompt="Commands"
        )

        args = rofi_config.get_rofi_args()

        assert '-markup-rows' not in args
        assert '-lines' in args and '10' in args


class TestSourceConfig:
    """Test the SourceConfig class."""

    def test_source_config_default_patterns(self):
        """Test that default file patterns are set correctly."""
        config = SourceConfig(
            files=[],
            directories=[],
            recursive=True
        )

        assert config.file_patterns == ["*.md", "*.markdown"]

    def test_source_config_custom_patterns(self):
        """Test custom file patterns."""
        config = SourceConfig(
            files=[],
            directories=[],
            recursive=True,
            file_patterns=["*.txt", "*.rst"]
        )

        assert config.file_patterns == ["*.txt", "*.rst"]