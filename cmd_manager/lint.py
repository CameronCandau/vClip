"""
Linting utilities for OpIndex-compatible markdown files.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


SUPPORTED_LANGUAGES = {"", "bash", "sh", "shell", "powershell", "ps1", "cmd", "bat", "batch"}
EXECUTABLE_LANGUAGES = SUPPORTED_LANGUAGES - {""}


@dataclass
class LintIssue:
    """A single lint issue for a markdown file."""

    severity: str
    file_path: str
    line_number: int
    code: str
    message: str


@dataclass
class LintResult:
    """Lint result for one file."""

    file_path: str
    issues: List[LintIssue]

    @property
    def error_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "warning")

    @property
    def ok(self) -> bool:
        return self.error_count == 0


class MarkdownLinter:
    """Linter for the OpIndex markdown authoring standard."""

    def lint_file(self, file_path: str) -> LintResult:
        """Lint a single markdown file from disk."""
        path = Path(file_path)
        if not path.exists():
            return LintResult(
                file_path=file_path,
                issues=[
                    LintIssue(
                        severity="error",
                        file_path=file_path,
                        line_number=1,
                        code="missing-file",
                        message="File does not exist."
                    )
                ]
            )

        content = path.read_text(encoding="utf-8")
        return self.lint_content(content, str(path))

    def lint_content(self, content: str, file_path: str = "<memory>") -> LintResult:
        """Lint markdown content in memory."""
        issues: List[LintIssue] = []
        lines = content.splitlines()

        current_category: Optional[str] = None
        current_description: Optional[str] = None
        current_description_line: Optional[int] = None

        seen_category = False
        saw_parseable_block = False
        in_code_block = False
        code_block_lang = ""
        code_block_start = 0
        code_block_lines: List[str] = []
        code_block_has_content = False
        description_has_parseable_block = False

        for line_number, raw_line in enumerate(lines, 1):
            line = raw_line.rstrip()

            if line.startswith("```") and not in_code_block:
                in_code_block = True
                code_block_lang = line[3:].strip().lower()
                code_block_start = line_number
                code_block_lines = []
                code_block_has_content = False

                if current_category is None:
                    issues.append(
                        self._issue(
                            "error",
                            file_path,
                            line_number,
                            "missing-category",
                            "Code block appears before any '# ' category heading."
                        )
                    )

                if current_description is None:
                    issues.append(
                        self._issue(
                            "error",
                            file_path,
                            line_number,
                            "missing-description",
                            "Code block appears before any '## ' task heading."
                        )
                    )

                if code_block_lang not in SUPPORTED_LANGUAGES:
                    issues.append(
                        self._issue(
                            "warning",
                            file_path,
                            line_number,
                            "unsupported-language",
                            f"Code block language '{code_block_lang}' will not be parsed by OpIndex."
                        )
                    )
                continue

            if line.startswith("```") and in_code_block:
                in_code_block = False
                is_parseable = code_block_lang in SUPPORTED_LANGUAGES

                if is_parseable:
                    saw_parseable_block = True
                    description_has_parseable_block = True

                if is_parseable and not code_block_has_content:
                    issues.append(
                        self._issue(
                            "error",
                            file_path,
                            code_block_start,
                            "empty-command",
                            "Supported code block is empty or contains comments only."
                        )
                    )

                code_block_lang = ""
                code_block_start = 0
                code_block_lines = []
                code_block_has_content = False
                continue

            if in_code_block:
                code_block_lines.append(line)
                stripped = line.strip()
                if stripped and not stripped.startswith("#"):
                    code_block_has_content = True
                continue

            if line.startswith("# "):
                if current_description and not description_has_parseable_block:
                    issues.append(
                        self._issue(
                            "warning",
                            file_path,
                            current_description_line or line_number,
                            "heading-without-command",
                            f"Task heading '{current_description}' has no parseable command block under it."
                        )
                    )

                current_category = line[2:].strip()
                seen_category = True
                current_description = None
                current_description_line = None
                description_has_parseable_block = False

                if not current_category:
                    issues.append(
                        self._issue(
                            "error",
                            file_path,
                            line_number,
                            "empty-category",
                            "Category heading must not be empty."
                        )
                    )
                continue

            if line.startswith("## "):
                if current_description and not description_has_parseable_block:
                    issues.append(
                        self._issue(
                            "warning",
                            file_path,
                            current_description_line or line_number,
                            "heading-without-command",
                            f"Task heading '{current_description}' has no parseable command block under it."
                        )
                    )

                current_description = line[3:].strip()
                current_description_line = line_number
                description_has_parseable_block = False

                if current_category is None:
                    issues.append(
                        self._issue(
                            "error",
                            file_path,
                            line_number,
                            "description-before-category",
                            "Task heading appears before any '# ' category heading."
                        )
                    )

                if not current_description:
                    issues.append(
                        self._issue(
                            "error",
                            file_path,
                            line_number,
                            "empty-description",
                            "Task heading must not be empty."
                        )
                    )
                elif not self._looks_like_action(current_description):
                    issues.append(
                        self._issue(
                            "warning",
                            file_path,
                            line_number,
                            "weak-description",
                            "Task heading should usually start with an action verb for better lookup."
                        )
                    )
                continue

        if in_code_block:
            issues.append(
                self._issue(
                    "error",
                    file_path,
                    code_block_start,
                    "unclosed-code-block",
                    "Code block is not closed."
                )
            )

        if current_description and not description_has_parseable_block:
            issues.append(
                self._issue(
                    "warning",
                    file_path,
                    current_description_line or 1,
                    "heading-without-command",
                    f"Task heading '{current_description}' has no parseable command block under it."
                )
            )

        if not seen_category:
            issues.append(
                self._issue(
                    "error",
                    file_path,
                    1,
                    "missing-category",
                    "File must contain at least one '# ' category heading."
                )
            )

        if not saw_parseable_block:
            issues.append(
                self._issue(
                    "error",
                    file_path,
                    1,
                    "no-commands",
                    "File does not contain any parseable command blocks."
                )
            )

        return LintResult(file_path=file_path, issues=issues)

    def _looks_like_action(self, description: str) -> bool:
        """Heuristic check for action-oriented task headings."""
        first_word = description.split()[0].lower().strip("()[]{}:,.")
        weak_starts = {
            "notes",
            "misc",
            "example",
            "examples",
            "reference",
            "overview",
            "info",
            "information",
            "stuff",
        }
        return first_word not in weak_starts

    def _issue(
        self,
        severity: str,
        file_path: str,
        line_number: int,
        code: str,
        message: str
    ) -> LintIssue:
        """Create a lint issue."""
        return LintIssue(
            severity=severity,
            file_path=file_path,
            line_number=line_number,
            code=code,
            message=message
        )
