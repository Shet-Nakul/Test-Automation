"""
Git Diff Analyzer
=================
Parses git diff output to detect:
  1. Changed method implementations
  2. Changed XPath / CSS / locator strings

Supports two modes:
  - Live repo: runs `git diff` between two refs / branches
  - Diff file: parses a pre-generated .diff / .patch file
"""

import re
import os
import subprocess
from dataclasses import dataclass, field
from typing import List, Tuple, Optional

# ──────────────────────────────────────────────
# Patterns
# ──────────────────────────────────────────────

# Matches diff file header: +++ b/src/main/.../LoginPage.java
DIFF_FILE_RE     = re.compile(r'^\+{3}\s+b/(.+\.java)', re.MULTILINE)

# Added lines start with +, removed with -
ADDED_LINE_RE    = re.compile(r'^\+(?!\+\+)(.*)$', re.MULTILINE)
REMOVED_LINE_RE  = re.compile(r'^-(?!--)(.*)$',  re.MULTILINE)

# Method signature in a diff line
METHOD_SIG_RE    = re.compile(
    r'(?:public|protected|private|static|final|synchronized|\s)+'
    r'(?:<[^>]+>\s+)?'
    r'(?:[\w\[\]<>,\s]+?)\s+'
    r'(\w+)'        # method name
    r'\s*\([^)]*\)'
    r'\s*(?:throws[\w,\s]+)?\s*\{'
)

# Locator patterns in diff lines
BY_XPATH_RE   = re.compile(r'By\.xpath\s*\(\s*"([^"]+)"')
BY_CSS_RE     = re.compile(r'By\.cssSelector\s*\(\s*"([^"]+)"')
BY_ID_RE      = re.compile(r'By\.id\s*\(\s*"([^"]+)"')
BY_NAME_RE    = re.compile(r'By\.name\s*\(\s*"([^"]+)"')
BY_CLASS_RE   = re.compile(r'By\.className\s*\(\s*"([^"]+)"')
BY_TAG_RE     = re.compile(r'By\.tagName\s*\(\s*"([^"]+)"')
BY_LINK_RE    = re.compile(r'By\.linkText\s*\(\s*"([^"]+)"')
BY_PARTIAL_RE = re.compile(r'By\.partialLinkText\s*\(\s*"([^"]+)"')
RAW_XPATH_RE  = re.compile(r'"((?:/|\./)[\w@\[\]=\'"./\s*]+)"')
LOCATOR_FIELD_RE = re.compile(
    r'(?:By|String)\s+\w+\s*=\s*By\.(?:xpath|cssSelector|id|name|className|tagName|linkText|partialLinkText)\s*\(\s*"([^"]+)"'
)
# FIX 1: @FindBy annotation changes
FINDBY_RE     = re.compile(
    r'@FindBy\s*\(\s*(?:xpath|css|id|name|className|tagName|linkText|partialLinkText)\s*=\s*"([^"]+)"'
)

# Hunk header: @@ -a,b +c,d @@ optional context
HUNK_RE = re.compile(r'^@@[^@]+@@\s*(.*)', re.MULTILINE)


# ──────────────────────────────────────────────
# Data structures
# ──────────────────────────────────────────────

@dataclass
class FileChange:
    file_path: str                           # relative path inside repo
    added_lines: List[str] = field(default_factory=list)
    removed_lines: List[str] = field(default_factory=list)
    changed_methods: List[str] = field(default_factory=list)   # method names
    changed_locators: List[str] = field(default_factory=list)  # xpath/css values
    hunk_contexts: List[str] = field(default_factory=list)     # method context from @@ headers


@dataclass
class DiffResult:
    file_changes: List[FileChange] = field(default_factory=list)

    @property
    def all_changed_methods(self) -> List[str]:
        methods = []
        for fc in self.file_changes:
            methods.extend(fc.changed_methods)
        return list(set(methods))

    @property
    def all_changed_locators(self) -> List[str]:
        locators = []
        for fc in self.file_changes:
            locators.extend(fc.changed_locators)
        return list(set(locators))


# ──────────────────────────────────────────────
# Core parser
# ──────────────────────────────────────────────

class GitDiffAnalyzer:

    def from_repo(
        self,
        repo_path: str,
        base_ref: str = 'HEAD~1',
        head_ref: str = 'HEAD'
    ) -> DiffResult:
        """Run git diff between two refs and parse the output."""
        try:
            result = subprocess.run(
                ['git', 'diff', f'{base_ref}..{head_ref}', '--unified=5'],
                cwd=repo_path,
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                print(f"[WARN] git diff failed: {result.stderr}")
                return DiffResult()
            return self._parse_diff(result.stdout)
        except FileNotFoundError:
            print("[ERROR] git not found. Make sure git is installed.")
            return DiffResult()

    def from_diff_file(self, diff_file_path: str) -> DiffResult:
        """Parse a .diff / .patch file."""
        with open(diff_file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        return self._parse_diff(content)

    def from_diff_string(self, diff_string: str) -> DiffResult:
        """Parse diff from a string."""
        return self._parse_diff(diff_string)

    def from_changed_files(
        self,
        repo_path: str,
        old_files: dict,  # {relative_path: old_content}
        new_files: dict   # {relative_path: new_content}
    ) -> DiffResult:
        """
        Compare old vs new file contents directly.
        Useful when you have the file contents but not a git repo.
        """
        import difflib
        combined_diff = []
        for path in set(list(old_files.keys()) + list(new_files.keys())):
            old = old_files.get(path, '').splitlines(keepends=True)
            new = new_files.get(path, '').splitlines(keepends=True)
            diff = list(difflib.unified_diff(old, new, fromfile=f'a/{path}', tofile=f'b/{path}', n=5))
            combined_diff.extend(diff)
        return self._parse_diff(''.join(combined_diff))

    # ──────────────────────────────────────────
    # Internal diff parser
    # ──────────────────────────────────────────

    def _parse_diff(self, diff_text: str) -> DiffResult:
        result = DiffResult()

        # Split into per-file sections
        file_sections = self._split_by_file(diff_text)

        for file_path, section in file_sections:
            if not file_path.endswith('.java'):
                continue

            fc = FileChange(file_path=file_path)

            # Extract hunk context headers (method names from @@ lines)
            for m in HUNK_RE.finditer(section):
                ctx = m.group(1).strip()
                if ctx:
                    fc.hunk_contexts.append(ctx)
                    # Try to extract method name from context
                    sig_match = METHOD_SIG_RE.search(ctx)
                    if sig_match:
                        fc.changed_methods.append(sig_match.group(1))

            # Process added lines
            for m in ADDED_LINE_RE.finditer(section):
                line = m.group(1)
                fc.added_lines.append(line)
                self._extract_from_line(line, fc)

            # Process removed lines
            for m in REMOVED_LINE_RE.finditer(section):
                line = m.group(1)
                fc.removed_lines.append(line)
                # If a locator was removed (i.e. changed), track it
                self._extract_locators_from_line(line, fc, changed=True)

            # Deduplicate
            fc.changed_methods = list(set(fc.changed_methods))
            fc.changed_locators = list(set(fc.changed_locators))

            result.file_changes.append(fc)

        return result

    def _split_by_file(self, diff_text: str) -> List[Tuple[str, str]]:
        """Split diff text into (file_path, section) pairs."""
        sections = []
        parts = re.split(r'^diff --git ', diff_text, flags=re.MULTILINE)
        for part in parts:
            if not part.strip():
                continue
            # Find +++ b/path line
            m = re.search(r'^\+{3}\s+b/(.+?)(?:\s|$)', part, re.MULTILINE)
            if m:
                sections.append((m.group(1).strip(), part))
        return sections

    def _extract_from_line(self, line: str, fc: FileChange):
        """Extract method signatures and locators from a changed (+) line."""
        # Method signatures
        sig_match = METHOD_SIG_RE.search(line)
        if sig_match:
            name = sig_match.group(1)
            if name not in ('if', 'while', 'for', 'catch', 'switch'):
                fc.changed_methods.append(name)

        # Locators
        self._extract_locators_from_line(line, fc)

    def _extract_locators_from_line(self, line: str, fc: FileChange, changed: bool = False):
        """Extract locator values from a line."""
        for pattern in [BY_XPATH_RE, BY_CSS_RE, BY_ID_RE, BY_NAME_RE,
                        BY_CLASS_RE, BY_TAG_RE, BY_LINK_RE, BY_PARTIAL_RE,
                        LOCATOR_FIELD_RE, FINDBY_RE]:
            for m in pattern.finditer(line):
                val = m.group(1)
                if val and val not in fc.changed_locators:
                    fc.changed_locators.append(val)

        for m in RAW_XPATH_RE.finditer(line):
            val = m.group(1)
            if val and val not in fc.changed_locators:
                fc.changed_locators.append(val)


# ──────────────────────────────────────────────
# Convenience: detect changed method bodies
# ──────────────────────────────────────────────

class MethodChangeDetector:
    """
    More precise: given two versions of a Java file,
    detect which method BODIES have actually changed.
    """

    def detect_changed_methods(
        self,
        old_source: str,
        new_source: str,
        file_path: str = ""
    ) -> List[str]:
        """Returns list of method names whose bodies changed."""
        from core.java_parser import JavaFileParser
        parser = JavaFileParser()

        # Write to temp files and parse
        import tempfile, os

        changed = []
        with tempfile.NamedTemporaryFile(suffix='.java', mode='w', delete=False) as f1:
            f1.write(old_source)
            old_path = f1.name
        with tempfile.NamedTemporaryFile(suffix='.java', mode='w', delete=False) as f2:
            f2.write(new_source)
            new_path = f2.name

        try:
            old_parsed = parser.parse_file(old_path)
            new_parsed = parser.parse_file(new_path)

            if old_parsed and new_parsed:
                old_map = {m.method_name: m.body for m in old_parsed.methods}
                new_map = {m.method_name: m.body for m in new_parsed.methods}

                for name, new_body in new_map.items():
                    old_body = old_map.get(name)
                    if old_body is None:
                        # New method added
                        changed.append(name)
                    elif self._normalize(old_body) != self._normalize(new_body):
                        changed.append(name)
        finally:
            os.unlink(old_path)
            os.unlink(new_path)

        return changed

    def _normalize(self, body: str) -> str:
        """Normalize whitespace for comparison."""
        return re.sub(r'\s+', ' ', body).strip()
