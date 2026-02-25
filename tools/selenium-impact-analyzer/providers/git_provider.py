import re
import subprocess
import os
from dataclasses import dataclass, field
from typing import List, Tuple, Optional

# Regex patterns (moved from original diff_analyzer.py)
ADDED_LINE_RE    = re.compile(r'^\+(?!\+\+)(.*)$', re.MULTILINE)
REMOVED_LINE_RE  = re.compile(r'^-(?!--)(.*)$',  re.MULTILINE)
METHOD_SIG_RE    = re.compile(
    r'(?:public|protected|private|static|final|synchronized|\s)+'
    r'(?:<[^>]+>\s+)?'
    r'(?:[\w\[\]<>,\s]+?)\s+'
    r'(\w+)'
    r'\s*\([^)]*\)'
    r'\s*(?:throws[\w,\s]+)?\s*\{'
)
BY_XPATH_RE   = re.compile(r'By\.xpath\s*\(\s*"([^"]+)"')
BY_CSS_RE     = re.compile(r'By\.cssSelector\s*\(\s*"([^"]+)"')
BY_ID_RE      = re.compile(r'By\.id\s*\(\s*"([^"]+)"')
BY_NAME_RE    = re.compile(r'By\.name\s*\(\s*"([^"]+)"')
BY_CLASS_RE   = re.compile(r'By\.className\s*\(\s*"([^"]+)"')
BY_TAG_RE     = re.compile(r'By\.tagName\s*\(\s*"([^"]+)"')
BY_LINK_RE    = re.compile(r'By\.linkText\s*\(\s*"([^"]+)"')
BY_PARTIAL_RE = re.compile(r'By\.partialLinkText\s*\(\s*"([^"]+)"')
RAW_XPATH_RE  = re.compile(r'"((?:/|\./)[\w@\[\]=\'"./\s*]+)"')
FINDBY_RE     = re.compile(r'@FindBy\s*\(\s*(?:xpath|css|id|name|className|tagName|linkText|partialLinkText)\s*=\s*"([^"]+)"')
LOCATOR_FIELD_WITH_NAME_RE = re.compile(
    r'(?:private|public|protected)?\s*(?:final\s+)?'
    r'(?:By|String)\s+(\w+)\s*=\s*'
    r'By\.(?:xpath|cssSelector|id|name|className|tagName|linkText|partialLinkText)\s*\(\s*"([^"]+)"'
)
FINDBY_WITH_NAME_RE = re.compile(
    r'@FindBy\s*\(\s*(?:xpath|css|id|name|className|tagName|linkText|partialLinkText)\s*=\s*"([^"]+)"\s*\)\s*'
    r'(?:@\w+\s*)*(?:private|public|protected)?\s*(?:static\s+)?(?:final\s+)?'
    r'(?:WebElement|By|List\s*<\s*WebElement\s*>)\s+(\w+)'
)

@dataclass
class FileChange:
    file_path: str
    added_lines: List[str] = field(default_factory=list)
    removed_lines: List[str] = field(default_factory=list)
    changed_methods: List[str] = field(default_factory=list)
    changed_locators: List[str] = field(default_factory=list)
    scoped_locator_changes: List[tuple] = field(default_factory=list)
    _scoped_builder: dict = field(default_factory=dict, repr=False)

@dataclass
class DiffResult:
    file_changes: List[FileChange] = field(default_factory=list)

    @property
    def all_changed_methods(self) -> List[str]:
        methods = []
        for fc in self.file_changes: methods.extend(fc.changed_methods)
        return list(set(methods))

    @property
    def all_changed_locators(self) -> List[str]:
        locators = []
        for fc in self.file_changes: locators.extend(fc.changed_locators)
        return list(set(locators))

    @property
    def all_scoped_locator_changes(self) -> List[tuple]:
        result, seen = [], set()
        for fc in self.file_changes:
            for item in fc.scoped_locator_changes:
                key = (item[0], item[1])
                if key not in seen:
                    seen.add(key)
                    result.append(item)
        return result

class GitProvider:
    def from_repo(self, repo_path: str, base_ref: str = 'HEAD~1', head_ref: str = 'HEAD') -> DiffResult:
        try:
            result = subprocess.run(['git', 'diff', f'{base_ref}..{head_ref}', '--unified=5'], cwd=repo_path, capture_output=True, text=True)
            if result.returncode != 0: return DiffResult()
            return self._parse_diff(result.stdout)
        except Exception: return DiffResult()

    def from_diff_file(self, diff_file_path: str) -> DiffResult:
        with open(diff_file_path, 'r', encoding='utf-8', errors='replace') as f:
            return self._parse_diff(f.read())

    def _parse_diff(self, diff_text: str) -> DiffResult:
        result = DiffResult()
        sections = self._split_by_file(diff_text)
        for file_path, section in sections:
            if not file_path.endswith('.java'): continue
            fc = FileChange(file_path=file_path)
            current_method, noise = None, frozenset({'if','while','for','switch','catch','try','else','new','class','super','this','return'})
            for raw_line in section.split('\n'):
                if raw_line.startswith('@@'):
                    m = re.search(r'@@[^@]+@@\s*(.*)', raw_line)
                    if m:
                        sig = METHOD_SIG_RE.search(m.group(1).strip())
                        if sig and sig.group(1) not in noise: current_method = sig.group(1)
                elif raw_line.startswith(' '):
                    sig = METHOD_SIG_RE.search(raw_line[1:])
                    if sig and sig.group(1) not in noise: current_method = sig.group(1)
                elif raw_line.startswith('+') or raw_line.startswith('-'):
                    if current_method and current_method not in fc.changed_methods: fc.changed_methods.append(current_method)
                    sig = METHOD_SIG_RE.search(raw_line[1:])
                    if sig and sig.group(1) not in noise:
                        if sig.group(1) not in fc.changed_methods: fc.changed_methods.append(sig.group(1))

            class_name = os.path.splitext(os.path.basename(file_path))[0]
            for m in ADDED_LINE_RE.finditer(section):
                line = m.group(1)
                fc.added_lines.append(line)
                self._extract_from_line(line, fc, class_name)
            for m in REMOVED_LINE_RE.finditer(section):
                line = m.group(1)
                fc.removed_lines.append(line)
                self._extract_locators_from_line(line, fc, class_name, changed=True)

            for key, data in fc._scoped_builder.items():
                fc.scoped_locator_changes.append((data['class'], data['field'], data['old'] or '', data['new'] or ''))
            fc.changed_methods = [n for n in fc.changed_methods if n not in noise]
            fc.changed_locators = list(set(fc.changed_locators))
            result.file_changes.append(fc)
        return result

    def _split_by_file(self, diff_text: str) -> List[Tuple[str, str]]:
        sections = []
        parts = re.split(r'^diff --git ', diff_text, flags=re.MULTILINE)
        for part in parts:
            if not part.strip(): continue
            m = re.search(r'^\+{3}\s+b/(.+?)(?:\s|$)', part, re.MULTILINE)
            if m: sections.append((m.group(1).strip(), part))
        return sections

    def _extract_from_line(self, line: str, fc: FileChange, class_name: str):
        sig = METHOD_SIG_RE.search(line)
        if sig and sig.group(1) not in ('if', 'while', 'for', 'catch', 'switch'):
            fc.changed_methods.append(sig.group(1))
        self._extract_locators_from_line(line, fc, class_name)

    def _extract_locators_from_line(self, line: str, fc: FileChange, class_name: str, changed: bool = False):
        for m in LOCATOR_FIELD_WITH_NAME_RE.finditer(line):
            field_name, xpath_value = m.group(1), m.group(2)
            if class_name:
                key = f"{class_name}#{field_name}"
                entry = fc._scoped_builder.setdefault(key, {'class': class_name, 'field': field_name, 'old': None, 'new': None})
                entry['old' if changed else 'new'] = xpath_value
            if xpath_value not in fc.changed_locators: fc.changed_locators.append(xpath_value)
        for m in FINDBY_WITH_NAME_RE.finditer(line):
            xpath_value, field_name = m.group(1), m.group(2)
            if class_name:
                key = f"{class_name}#{field_name}"
                entry = fc._scoped_builder.setdefault(key, {'class': class_name, 'field': field_name, 'old': None, 'new': None})
                entry['old' if changed else 'new'] = xpath_value
            if xpath_value not in fc.changed_locators: fc.changed_locators.append(xpath_value)
        for p in [BY_XPATH_RE, BY_CSS_RE, BY_ID_RE, BY_NAME_RE, BY_CLASS_RE, BY_TAG_RE, BY_LINK_RE, BY_PARTIAL_RE, FINDBY_RE]:
            for m in p.finditer(line):
                val = m.group(1)
                if val and val not in fc.changed_locators: fc.changed_locators.append(val)
        for m in RAW_XPATH_RE.finditer(line):
            val = m.group(1)
            if val and val not in fc.changed_locators: fc.changed_locators.append(val)
