import re
import os
from typing import List, Dict, Set, Optional
from core.models import MethodInfo, ParsedFile
from core.base_parser import BaseParser

# Regex patterns (moved from original java_parser.py)
PACKAGE_RE       = re.compile(r'^\s*package\s+([\w.]+)\s*;', re.MULTILINE)
IMPORT_RE        = re.compile(r'^\s*import\s+([\w.*]+)\s*;', re.MULTILINE)
CLASS_RE         = re.compile(r'(?:public\s+)?(?:abstract\s+)?class\s+(\w+)', re.MULTILINE)
ANNOTATION_RE    = re.compile(r'@([\w.]+)(?:\([^)]*\))?')
METHOD_RE        = re.compile(
    r'((?:\s*@[\w.()\s,"=@\[\]{}]*\s*)*)'
    r'\s*(?:public|protected|private|static|final|synchronized|default|abstract|\s)+'
    r'(?:<[^>]+>\s+)?'
    r'(?:[\w\[\]<>,\s]+?)\s+'
    r'(\w+)'
    r'\s*\('
    r'([^)]*)'
    r'\)\s*'
    r'(?:throws\s+[\w,\s]+)?\s*'
    r'\{',
    re.MULTILINE
)
XPATH_RE         = re.compile(r'"([^"]*//[^"]*)"')
BY_XPATH_RE      = re.compile(r'By\.xpath\s*\(\s*"([^"]+)"')
BY_CSS_RE        = re.compile(r'By\.cssSelector\s*\(\s*"([^"]+)"')
BY_ID_RE         = re.compile(r'By\.id\s*\(\s*"([^"]+)"')
BY_NAME_RE       = re.compile(r'By\.name\s*\(\s*"([^"]+)"')
BY_CLASS_RE      = re.compile(r'By\.className\s*\(\s*"([^"]+)"')
BY_TAG_RE        = re.compile(r'By\.tagName\s*\(\s*"([^"]+)"')
BY_LINK_RE       = re.compile(r'By\.linkText\s*\(\s*"([^"]+)"')
BY_PARTIAL_RE    = re.compile(r'By\.partialLinkText\s*\(\s*"([^"]+)"')
FIND_ELEMENT_RE  = re.compile(r'findElement\s*\(\s*By\.\w+\s*\(\s*"([^"]+)"')
FINDBY_RE        = re.compile(r'@FindBy\s*\(\s*(?:xpath|css|id|name|className|tagName|linkText|partialLinkText)\s*=\s*"([^"]+)"')
STRING_CONST_LOCATOR_RE = re.compile(
    r'(?:private\s+|public\s+|protected\s+)?(?:static\s+)?(?:final\s+)?'
    r'String\s+(\w*(?:XPATH|CSS|LOCATOR|SELECTOR|PATH|xpath|css|locator|selector|path)\w*)\s*=\s*"([^"]+)"'
)
METHOD_CALL_RE   = re.compile(r'(?:[\w]+\.)?(\w+)\s*\(')
LOCATOR_FIELD_RE = re.compile(
    r'(?:By|String)\s+(\w+)\s*=\s*By\.(?:xpath|cssSelector|id|name|className|tagName|linkText|partialLinkText)\s*\(\s*"([^"]+)"'
)
FIELD_DECL_RE = re.compile(r'(?:private|public|protected)?\s*(?:static\s+)?(?:final\s+)?([A-Z]\w+)\s+(\w+)\s*(?:=|;)')
TYPED_CALL_RE = re.compile(r'\b(\w+)\.(\w+)\s*\(')

_CALL_NOISE = frozenset({
    'if', 'while', 'for', 'switch', 'catch', 'try', 'else', 'new',
    'return', 'throw', 'assert', 'instanceof',
    'System', 'String', 'Integer', 'Long', 'Double', 'Boolean', 'List',
    'Map', 'Set', 'Array', 'Arrays', 'Collections', 'Optional',
    'int', 'boolean', 'void', 'null', 'true', 'false', 'super', 'this',
    'Object', 'Exception', 'Thread', 'Math', 'Duration', 'WebDriverWait',
    'ExpectedConditions', 'JavascriptExecutor', 'Actions',
})

def extract_body(source: str, open_brace_pos: int) -> str:
    depth, i = 0, open_brace_pos
    start = open_brace_pos
    in_string = in_char = in_line_comment = in_block_comment = False
    while i < len(source):
        c = source[i]
        if in_line_comment:
            if c == '\n': in_line_comment = False
            i += 1; continue
        if in_block_comment:
            if source[i:i+2] == '*/': in_block_comment = False; i += 2; continue
            i += 1; continue
        if c == '"' and not in_char:
            if i > 0 and source[i-1] == '\\': i += 1; continue
            in_string = not in_string; i += 1; continue
        if in_string: i += 1; continue
        if c == "'" and not in_string: in_char = not in_char; i += 1; continue
        if in_char: i += 1; continue
        if source[i:i+2] == '//': in_line_comment = True; i += 2; continue
        if source[i:i+2] == '/*': in_block_comment = True; i += 2; continue
        if c == '{': depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0: return source[start:i+1]
        i += 1
    return source[start:]

def line_of(source: str, pos: int) -> int:
    return source[:pos].count('\n') + 1

def extract_locators_from_text(text: str) -> List[str]:
    locators = []
    for pattern in [BY_XPATH_RE, BY_CSS_RE, BY_ID_RE, BY_NAME_RE, BY_CLASS_RE, BY_TAG_RE, BY_LINK_RE, BY_PARTIAL_RE, FIND_ELEMENT_RE, FINDBY_RE]:
        locators.extend(pattern.findall(text))
    for m in XPATH_RE.finditer(text):
        val = m.group(1)
        if val not in locators: locators.append(val)
    return list(set(locators))

class JavaParser(BaseParser):
    def parse_file(self, file_path: str) -> Optional[ParsedFile]:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                source = f.read()
        except Exception as e:
            print(f"[WARN] Cannot read {file_path}: {e}")
            return None

        package_match = PACKAGE_RE.search(source)
        package = package_match.group(1) if package_match else ""
        imports = IMPORT_RE.findall(source)
        class_match = CLASS_RE.search(source)
        if not class_match: return None
        class_name = class_match.group(1)

        class_level_locators: Dict[str, str] = {}
        for m in LOCATOR_FIELD_RE.finditer(source):
            class_level_locators[m.group(1)] = m.group(2)

        for m in re.finditer(
            r'@FindBy\s*\(\s*(?:xpath|css|id|name|className|tagName|linkText|partialLinkText)\s*=\s*"([^"]+)"\s*\)\s*'
            r'(?:@\w+\s*)*'
            r'(?:private|public|protected)?\s*'
            r'(?:static\s+)?(?:final\s+)?'
            r'(?:WebElement|List\s*<\s*WebElement\s*>)\s+(\w+)',
            source
        ):
            class_level_locators[m.group(2)] = m.group(1)

        for m in STRING_CONST_LOCATOR_RE.finditer(source):
            class_level_locators[m.group(1)] = m.group(2)

        class_field_types: Dict[str, str] = {}
        for m in FIELD_DECL_RE.finditer(source):
            type_name, var_name = m.group(1), m.group(2)
            if not type_name[0].islower():
                class_field_types[var_name] = type_name

        methods = self._extract_methods(source, class_name, file_path, class_level_locators, class_field_types)

        return ParsedFile(
            file_path=file_path, class_name=class_name, package=package, imports=imports,
            methods=methods, raw_source=source, class_level_locators=class_level_locators,
            class_field_types=class_field_types
        )

    def _extract_methods(self, source: str, class_name: str, file_path: str, class_level_locators: Dict[str, str], class_field_types: Dict[str, str]) -> List[MethodInfo]:
        methods = []
        for match in METHOD_RE.finditer(source):
            annotation_block, method_name = match.group(1), match.group(2)
            if method_name in ('if', 'while', 'for', 'switch', 'catch', 'try', 'else', 'new', 'return', 'class', 'interface', 'enum'):
                continue
            annotations = ANNOTATION_RE.findall(annotation_block)
            is_test = any(a in ('Test', 'org.testng.annotations.Test', 'org.junit.Test', 'org.junit.jupiter.api.Test') for a in annotations)
            body = extract_body(source, match.end() - 1)
            line_num = line_of(source, match.start())
            fq = f"{class_name}#{method_name}"
            calls = self._extract_calls(body, method_name)
            locators = extract_locators_from_text(body)
            locator_fields_used: Set[str] = set()
            for field_name, locator_value in class_level_locators.items():
                if re.search(r'\b' + re.escape(field_name) + r'\b', body):
                    locator_fields_used.add(field_name)
                    if locator_value not in locators: locators.append(locator_value)
            typed_calls: Dict[str, Set[str]] = {}
            cleaned_body = re.sub(r'"[^"]*"', '""', body)
            for tc in TYPED_CALL_RE.finditer(cleaned_body):
                var_name, method_called = tc.group(1), tc.group(2)
                if var_name in class_field_types and var_name != 'this':
                    typed_calls.setdefault(var_name, set()).add(method_called)

            methods.append(MethodInfo(
                class_name=class_name, method_name=method_name, full_qualified=fq,
                file_path=file_path, line_number=line_num, is_test=is_test,
                annotations=annotations, body=body, calls=calls, locators=locators,
                locator_fields_used=locator_fields_used, typed_calls=typed_calls
            ))
        return methods

    def _extract_calls(self, body: str, current_method: str) -> Set[str]:
        calls = set()
        cleaned = re.sub(r'"[^"]*"', '""', body)
        cleaned = re.sub(r'//.*?\n', '\n', cleaned)
        cleaned = re.sub(r'/\*.*?\*/', '', cleaned, flags=re.DOTALL)
        noise = _CALL_NOISE | {current_method}
        for m in METHOD_CALL_RE.finditer(cleaned):
            name = m.group(1)
            if name and name not in noise: calls.add(name)
        return calls

    def scan_repository(self, repo_path: str) -> List[ParsedFile]:
        parsed_files = []
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in ('.git', 'target', 'build', 'out', '.idea', 'node_modules', '.gradle')]
            for fname in files:
                if fname.endswith('.java'):
                    res = self.parse_file(os.path.join(root, fname))
                    if res: parsed_files.append(res)
        return parsed_files
