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
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            xdg_cache = os.environ.get('XDG_CACHE_HOME')
            self.cache_dir = Path(xdg_cache) / 'opindex' if xdg_cache else Path.home() / '.cache' / 'opindex'

        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_file_hash(self, file_path: str) -> str:
        path = Path(file_path)
        if not path.exists():
            return ""

        with open(path, 'rb') as f:
            content_hash = hashlib.md5(f.read()).hexdigest()

        return hashlib.md5(f"{content_hash}:{path.stat().st_mtime}".encode()).hexdigest()

    def _get_cache_file_path(self, source_files: List[str]) -> Path:
        files_hash = hashlib.md5(":".join(sorted(source_files)).encode()).hexdigest()
        return self.cache_dir / f"commands_{files_hash}.json"

    def _create_cache_entry(self, commands: List[Command], source_files: List[str]) -> Dict[str, Any]:
        return {
            'version': '1.0',
            'created_at': datetime.now().isoformat(),
            'source_files': source_files,
            'file_hashes': {file_path: self._get_file_hash(file_path) for file_path in source_files},
            'commands': [cmd.to_dict() for cmd in commands]
        }

    def _is_cache_valid(self, cache_entry: Dict[str, Any]) -> bool:
        try:
            for file_path, cached_hash in cache_entry['file_hashes'].items():
                if not Path(file_path).exists():
                    return False
                if self._get_file_hash(file_path) != cached_hash:
                    return False
            return True
        except (KeyError, TypeError):
            return False

    def get_cached_commands(self, source_files: List[str]) -> Optional[List[Command]]:
        cache_file = self._get_cache_file_path(source_files)
        if not cache_file.exists():
            return None

        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_entry = json.load(f)
            if not self._is_cache_valid(cache_entry):
                cache_file.unlink(missing_ok=True)
                return None
            return [Command.from_dict(cmd_data) for cmd_data in cache_entry['commands']]
        except (json.JSONDecodeError, KeyError, TypeError):
            cache_file.unlink(missing_ok=True)
            return None

    def cache_commands(self, commands: List[Command], source_files: List[str]) -> bool:
        try:
            cache_file = self._get_cache_file_path(source_files)
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(self._create_cache_entry(commands, source_files), f, indent=2)
            return True
        except OSError:
            return False

    def clear_cache(self, source_files: Optional[List[str]] = None) -> int:
        removed_count = 0

        if source_files:
            cache_file = self._get_cache_file_path(source_files)
            if cache_file.exists():
                cache_file.unlink()
                return 1
            return 0

        for cache_file in self.cache_dir.glob("commands_*.json"):
            try:
                cache_file.unlink()
                removed_count += 1
            except OSError:
                pass

        return removed_count


class CachedMarkdownParser(MarkdownParser):
    """MarkdownParser with caching support."""

    def __init__(self, cache_dir: Optional[str] = None):
        self.cache = CommandCache(cache_dir)

    def parse_files_cached(self, file_paths: List[str]) -> List[Command]:
        cached_commands = self.cache.get_cached_commands(file_paths)
        if cached_commands is not None:
            return cached_commands

        commands = self.parse_files(file_paths)
        self.cache.cache_commands(commands, file_paths)
        return commands
