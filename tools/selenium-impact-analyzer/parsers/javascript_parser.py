import re
import os
from typing import List, Dict, Set, Optional
from core.models import MethodInfo, ParsedFile
from core.base_parser import BaseParser

# Regex patterns for JavaScript/TypeScript
IMPORT_RE = re.compile(r'(?:import\s+.*?\s+from\s+[\'"](.*?)[\'"]|require\s*\(\s*[\'"](.*?)[\'"]\s*\))', re.MULTILINE)

# Playwright Test pattern: test('name', async ({ page }) => { ... })
PLAYWRIGHT_TEST_RE = re.compile(
    r'(?:test|test\.only|test\.skip|test\.fixme)\s*\(\s*[\'"](.*?)[\'"]\s*,\s*(?:async\s*)?\s*\((.*?)\)\s*=>\s*\{',
    re.MULTILINE
)

# Function patterns: function name() { ... } or const name = () => { ... }
FUNCTION_RE = re.compile(
    r'(?:async\s+)?function\s+(\w+)\s*\(.*?\)\s*\{|'
    r'(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\(.*?\)\s*=>\s*\{',
    re.MULTILINE
)

# Locator patterns
PLAYWRIGHT_LOCATOR_RE = re.compile(r'(?:page|locator|frame)\.(?:locator|getByRole|getByText|getByLabel|getByPlaceholder|getByAltText|getByTitle|getByTestId)\s*\(\s*[\'"](.*?)[\'"]', re.MULTILINE)
CSS_XPATH_STRING_RE = re.compile(r'[\'"]((?://|\.|#|\[)[^"\'\s]*)[\'"]', re.MULTILINE)

# Method call pattern
METHOD_CALL_RE = re.compile(r'(?:[\w]+\.)?(\w+)\s*\(')

_JS_NOISE = frozenset({
    'if', 'while', 'for', 'switch', 'catch', 'try', 'else', 'new',
    'return', 'throw', 'await', 'async', 'const', 'let', 'var', 'export', 'import',
    'console', 'Array', 'Object', 'String', 'Number', 'Boolean', 'Promise',
    'null', 'undefined', 'true', 'false', 'this', 'super',
})

def extract_js_body(source: str, open_brace_pos: int) -> str:
    depth, i = 0, open_brace_pos
    start = open_brace_pos
    in_string = False
    string_char = None
    in_line_comment = in_block_comment = False
    
    while i < len(source):
        c = source[i]
        if in_line_comment:
            if c == '\n': in_line_comment = False
            i += 1; continue
        if in_block_comment:
            if source[i:i+2] == '*/': in_block_comment = False; i += 2; continue
            i += 1; continue
        
        # Handle template literals and strings
        if not in_string and not in_line_comment and not in_block_comment:
            if c in ('"', "'", '`'):
                in_string = True
                string_char = c
                i += 1; continue
        elif in_string:
            if c == string_char and source[i-1] != '\\':
                in_string = False
                string_char = None
            i += 1; continue

        if source[i:i+2] == '//': in_line_comment = True; i += 2; continue
        if source[i:i+2] == '/*': in_block_comment = True; i += 2; continue
        
        if c == '{': depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0: return source[start:i+1]
        i += 1
    return source[start:]

class JavascriptPlaywrightParser(BaseParser):
    def parse_file(self, file_path: str) -> Optional[ParsedFile]:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                source = f.read()
        except Exception as e:
            print(f"[WARN] Cannot read {file_path}: {e}")
            return None

        imports = [m[0] or m[1] for m in IMPORT_RE.findall(source)]
        
        methods: List[MethodInfo] = []
        
        # 1. Extract Playwright Tests
        for match in PLAYWRIGHT_TEST_RE.finditer(source):
            test_name = match.group(1)
            brace_pos = match.end() - 1
            body = extract_js_body(source, brace_pos)
            line_num = source[:match.start()].count('\n') + 1
            
            methods.append(MethodInfo(
                class_name="PlaywrightTests",
                method_name=test_name,
                full_qualified=f"{os.path.basename(file_path)}#{test_name}",
                file_path=file_path,
                line_number=line_num,
                is_test=True,
                annotations=["playwright-test"],
                body=body,
                calls=self._extract_calls(body, test_name),
                locators=self._extract_locators(body),
                locator_fields_used=set(),
                typed_calls={}
            ))

        # 2. Extract Regular Functions/Methods
        for match in FUNCTION_RE.finditer(source):
            func_name = match.group(1) or match.group(2)
            if not func_name: continue
            
            brace_pos = match.end() - 1
            body = extract_js_body(source, brace_pos)
            line_num = source[:match.start()].count('\n') + 1
            
            methods.append(MethodInfo(
                class_name="Global",
                method_name=func_name,
                full_qualified=f"{os.path.basename(file_path)}#{func_name}",
                file_path=file_path,
                line_number=line_num,
                is_test=False,
                annotations=[],
                body=body,
                calls=self._extract_calls(body, func_name),
                locators=self._extract_locators(body),
                locator_fields_used=set(),
                typed_calls={}
            ))

        return ParsedFile(
            file_path=file_path,
            class_name="JavascriptFile",
            package="",
            imports=imports,
            methods=methods,
            raw_source=source
        )

    def _extract_calls(self, body: str, current_name: str) -> Set[str]:
        calls = set()
        # Simple extraction for JS
        for m in METHOD_CALL_RE.finditer(body):
            name = m.group(1)
            if name and name not in _JS_NOISE and name != current_name:
                calls.add(name)
        return calls

    def _extract_locators(self, body: str) -> List[str]:
        locators = set()
        for m in PLAYWRIGHT_LOCATOR_RE.finditer(body):
            locators.add(m.group(1))
        # Fallback for strings that look like selectors
        for m in CSS_XPATH_STRING_RE.finditer(body):
            locators.add(m.group(1))
        return list(locators)

    def scan_repository(self, repo_path: str) -> List[ParsedFile]:
        parsed_files = []
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in ('.git', 'node_modules', 'dist', 'build')]
            for fname in files:
                if fname.endswith(('.js', '.ts')):
                    res = self.parse_file(os.path.join(root, fname))
                    if res: parsed_files.append(res)
        return parsed_files
