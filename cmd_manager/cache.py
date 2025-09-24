"""
Caching system for parsed commands.
"""

import json
import os
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
from .parser import Command, MarkdownParser


class CommandCache:
    """Manages caching of parsed commands for fast startup."""

    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize cache manager.

        Args:
            cache_dir: Directory for cache files. Defaults to ~/.cache/vclip
        """
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            # Use XDG cache directory or fallback to ~/.cache
            xdg_cache = os.environ.get('XDG_CACHE_HOME')
            if xdg_cache:
                self.cache_dir = Path(xdg_cache) / 'vclip'
            else:
                self.cache_dir = Path.home() / '.cache' / 'vclip'

        # Create cache directory if it doesn't exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_file_hash(self, file_path: str) -> str:
        """Calculate MD5 hash of file content and modification time."""
        path = Path(file_path)
        if not path.exists():
            return ""

        # Combine file content hash with modification time
        with open(path, 'rb') as f:
            content_hash = hashlib.md5(f.read()).hexdigest()

        mtime = str(path.stat().st_mtime)
        combined = f"{content_hash}:{mtime}"
        return hashlib.md5(combined.encode()).hexdigest()

    def _get_cache_file_path(self, source_files: List[str]) -> Path:
        """Get cache file path for given source files."""
        # Create a hash of all source file paths for cache filename
        files_str = ":".join(sorted(source_files))
        files_hash = hashlib.md5(files_str.encode()).hexdigest()
        return self.cache_dir / f"commands_{files_hash}.json"

    def _create_cache_entry(self, commands: List[Command], source_files: List[str]) -> Dict[str, Any]:
        """Create cache entry with metadata."""
        return {
            'version': '1.0',
            'created_at': datetime.now().isoformat(),
            'source_files': source_files,
            'file_hashes': {file_path: self._get_file_hash(file_path) for file_path in source_files},
            'commands': [cmd.to_dict() for cmd in commands]
        }

    def _is_cache_valid(self, cache_entry: Dict[str, Any]) -> bool:
        """Check if cache entry is still valid."""
        try:
            # Check if all source files still exist and haven't changed
            for file_path, cached_hash in cache_entry['file_hashes'].items():
                if not Path(file_path).exists():
                    return False

                current_hash = self._get_file_hash(file_path)
                if current_hash != cached_hash:
                    return False

            return True
        except (KeyError, TypeError):
            return False

    def get_cached_commands(self, source_files: List[str]) -> Optional[List[Command]]:
        """
        Get cached commands for source files if cache is valid.

        Args:
            source_files: List of source file paths

        Returns:
            List of cached commands or None if cache is invalid/missing
        """
        cache_file = self._get_cache_file_path(source_files)

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_entry = json.load(f)

            if not self._is_cache_valid(cache_entry):
                # Cache is invalid, remove it
                cache_file.unlink(missing_ok=True)
                return None

            # Convert cached data back to Command objects
            commands = [Command.from_dict(cmd_data) for cmd_data in cache_entry['commands']]
            return commands

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            # Cache file is corrupted, remove it
            cache_file.unlink(missing_ok=True)
            return None

    def cache_commands(self, commands: List[Command], source_files: List[str]) -> bool:
        """
        Cache parsed commands.

        Args:
            commands: List of commands to cache
            source_files: List of source file paths

        Returns:
            True if caching was successful, False otherwise
        """
        try:
            cache_file = self._get_cache_file_path(source_files)
            cache_entry = self._create_cache_entry(commands, source_files)

            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_entry, f, indent=2)

            return True

        except (OSError, json.JSONEncodeError) as e:
            return False

    def clear_cache(self, source_files: Optional[List[str]] = None) -> int:
        """
        Clear cache files.

        Args:
            source_files: Specific source files to clear cache for, or None to clear all

        Returns:
            Number of cache files removed
        """
        removed_count = 0

        if source_files:
            # Clear specific cache file
            cache_file = self._get_cache_file_path(source_files)
            if cache_file.exists():
                cache_file.unlink()
                removed_count = 1
        else:
            # Clear all cache files
            for cache_file in self.cache_dir.glob("commands_*.json"):
                try:
                    cache_file.unlink()
                    removed_count += 1
                except OSError:
                    pass

        return removed_count

    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about cache directory and files."""
        cache_files = list(self.cache_dir.glob("commands_*.json"))
        total_size = sum(f.stat().st_size for f in cache_files)

        return {
            'cache_dir': str(self.cache_dir),
            'cache_files_count': len(cache_files),
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2)
        }

    def cleanup_invalid_cache(self) -> int:
        """Remove all invalid cache entries."""
        removed_count = 0
        cache_files = list(self.cache_dir.glob("commands_*.json"))

        for cache_file in cache_files:
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_entry = json.load(f)

                if not self._is_cache_valid(cache_entry):
                    cache_file.unlink()
                    removed_count += 1

            except (json.JSONDecodeError, KeyError, TypeError, OSError):
                # File is corrupted or unreadable, remove it
                try:
                    cache_file.unlink()
                    removed_count += 1
                except OSError:
                    pass

        return removed_count


class CachedMarkdownParser(MarkdownParser):
    """MarkdownParser with caching support."""

    def __init__(self, cache_dir: Optional[str] = None):
        super().__init__()
        self.cache = CommandCache(cache_dir)

    def parse_files_cached(self, file_paths: List[str]) -> List[Command]:
        """
        Parse multiple markdown files with caching.

        Args:
            file_paths: List of file paths to parse

        Returns:
            List of parsed commands
        """
        # Try to get commands from cache first
        cached_commands = self.cache.get_cached_commands(file_paths)
        if cached_commands is not None:
            return cached_commands

        # Cache miss - parse files and cache results
        commands = self.parse_files(file_paths)
        self.cache.cache_commands(commands, file_paths)
        return commands

    def parse_file_cached(self, file_path: str) -> List[Command]:
        """Parse a single file with caching."""
        return self.parse_files_cached([file_path])


def main():
    """CLI interface for testing cache functionality."""
    import sys
    import time

    if len(sys.argv) < 2:
        print("Usage: python -m cmd_manager.cache <markdown_file> [action]")
        print("Actions: parse, info, clear, cleanup")
        sys.exit(1)

    file_path = sys.argv[1]
    action = sys.argv[2] if len(sys.argv) > 2 else "parse"

    parser = CachedMarkdownParser()

    if action == "parse":
        # Test parsing with caching
        print(f"Parsing {file_path} with caching...")

        # First parse (cache miss)
        start_time = time.time()
        commands = parser.parse_file_cached(file_path)
        first_time = time.time() - start_time
        print(f"First parse: {len(commands)} commands in {first_time:.4f}s")

        # Second parse (cache hit)
        start_time = time.time()
        commands = parser.parse_file_cached(file_path)
        second_time = time.time() - start_time
        print(f"Second parse: {len(commands)} commands in {second_time:.4f}s")

        speedup = first_time / second_time if second_time > 0 else float('inf')
        print(f"Speedup: {speedup:.2f}x")

    elif action == "info":
        info = parser.cache.get_cache_info()
        print("Cache Information:")
        for key, value in info.items():
            print(f"  {key}: {value}")

    elif action == "clear":
        removed = parser.cache.clear_cache()
        print(f"Removed {removed} cache files")

    elif action == "cleanup":
        removed = parser.cache.cleanup_invalid_cache()
        print(f"Cleaned up {removed} invalid cache files")

    else:
        print(f"Unknown action: {action}")
        sys.exit(1)


if __name__ == "__main__":
    main()