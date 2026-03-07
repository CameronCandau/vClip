"""
Variable detection and substitution for vclip commands.
"""

import re
import json
import os
from pathlib import Path
from typing import Dict, Optional, Set


class VariableDetector:
    """Detects $UPPERCASE_VAR patterns in command strings."""

    # Matches $WORD where WORD starts with uppercase letter (not shell vars like $ip)
    PATTERN = re.compile(r'\$([A-Z][A-Z0-9_]*)')

    @classmethod
    def detect(cls, text: str) -> Set[str]:
        """Return set of variable names (without $) found in text."""
        return set(cls.PATTERN.findall(text))

    @classmethod
    def has_variables(cls, text: str) -> bool:
        """Return True if text contains any $UPPERCASE_VAR."""
        return bool(cls.PATTERN.search(text))

    @classmethod
    def substitute(cls, text: str, values: Dict[str, str]) -> str:
        """Replace all $VAR occurrences in text with corresponding values."""
        result = text
        for var, val in values.items():
            result = result.replace(f'${var}', val)
        return result


class VariableSubstitutor:
    """Resolves variable values from config, session cache, and user prompts."""

    def __init__(self, config_variables: Dict[str, str] = None):
        """
        Args:
            config_variables: Pre-defined variables from config.yaml (never prompted).
        """
        self.config_variables = config_variables or {}
        self.session_cache = self._load_cache()

    def _cache_path(self) -> Path:
        xdg = os.environ.get('XDG_CACHE_HOME')
        base = Path(xdg) if xdg else Path.home() / '.cache'
        return base / 'vclip' / 'vars.json'

    def _load_cache(self) -> Dict[str, str]:
        try:
            p = self._cache_path()
            if p.exists():
                with open(p) as f:
                    return json.load(f)
        except Exception:
            pass
        return {}

    def _save_cache(self) -> None:
        try:
            p = self._cache_path()
            p.parent.mkdir(parents=True, exist_ok=True)
            with open(p, 'w') as f:
                json.dump(self.session_cache, f, indent=2)
        except Exception:
            pass

    def resolve(self, variables: Set[str], rofi=None, no_prompt: bool = False) -> Optional[Dict[str, str]]:
        """
        Resolve variable values for the given set of variable names.

        Priority order:
            1. config.yaml definitions (auto-substitute, never prompt)
            2. Session cache (pre-fill prompts)
            3. User prompt via rofi (unless no_prompt)

        Returns:
            Dict of {VAR: value} for all resolved variables, or None if user cancelled.
            Variables that couldn't be resolved are omitted (left literal in command).
        """
        values = {}

        # Config-defined vars: always apply, never prompt
        for var in variables:
            if var in self.config_variables:
                values[var] = self.config_variables[var]

        remaining = variables - set(values.keys())
        if not remaining:
            return values

        if no_prompt:
            # Use session cache only, no interactive prompts
            for var in remaining:
                if var in self.session_cache:
                    values[var] = self.session_cache[var]
            return values

        # Prompt for each remaining variable
        prompted = {}
        for var in sorted(remaining):
            default = self.session_cache.get(var, '')
            if rofi is None:
                # No UI available; leave this var unresolved
                continue
            val = rofi.prompt_input(f"Enter {var}", default)
            if val is None:
                # User pressed ESC — cancel the entire substitution
                return None
            final = val if val else default
            if final:
                prompted[var] = final

        if prompted:
            self.session_cache.update(prompted)
            self._save_cache()

        values.update(prompted)
        return values
