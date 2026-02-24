"""
Java source parser using regex-based AST analysis.
Extracts:
  - Class names and their methods
  - Method bodies and their outgoing calls
  - XPath/CSS locator strings and where they're used
  - @Test annotations (TestNG / JUnit)
"""

import re
import os
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple


# ──────────────────────────────────────────────
# Data structures
# ──────────────────────────────────────────────

@dataclass
class MethodInfo:
    class_name: str
    method_name: str
    full_qualified: str          # ClassName#methodName
    file_path: str
    line_number: int
    is_test: bool                # @Test annotation present
    annotations: List[str]
    body: str                    # raw method body text
    calls: Set[str] = field(default_factory=set)      # method names called inside body
    locators: List[str] = field(default_factory=list) # xpath/css inline strings used
    locator_fields_used: Set[str] = field(default_factory=set)  # class-level field names referenced (e.g. 'employeeListHeader')
    # Typed calls: {varName: methodName} extracted from "varName.methodName()" in body
    # e.g. {"adminPage": {"clickAdd", "searchUser"}}
    typed_calls: Dict[str, Set[str]] = field(default_factory=dict)


@dataclass
class ParsedFile:
    file_path: str
    class_name: str
    package: str
    imports: List[str]
    methods: List[MethodInfo]
    raw_source: str
    class_level_locators: Dict[str, str] = field(default_factory=dict)  # fieldName → xpathValue
    class_field_types: Dict[str, str] = field(default_factory=dict)     # varName → TypeName (for typed call resolution)


# ──────────────────────────────────────────────
# Regex patterns
# ──────────────────────────────────────────────

PACKAGE_RE       = re.compile(r'^\s*package\s+([\w.]+)\s*;', re.MULTILINE)
IMPORT_RE        = re.compile(r'^\s*import\s+([\w.*]+)\s*;', re.MULTILINE)
CLASS_RE         = re.compile(r'(?:public\s+)?(?:abstract\s+)?class\s+(\w+)', re.MULTILINE)

# Annotation detection
ANNOTATION_RE    = re.compile(r'@([\w.]+)(?:\([^)]*\))?')

# Method signature: captures annotations block + return type + name + params
METHOD_RE        = re.compile(
    r'((?:\s*@[\w.()\s,"=@\[\]{}]*\s*)*)'   # annotations (group 1)
    r'\s*(?:public|protected|private|static|final|synchronized|default|abstract|\s)+'
    r'(?:<[^>]+>\s+)?'                         # generics
    r'(?:[\w\[\]<>,\s]+?)\s+'                 # return type
    r'(\w+)'                                   # method name (group 2)
    r'\s*\('                                   # opening paren
    r'([^)]*)'                                 # params (group 3)
    r'\)\s*'
    r'(?:throws\s+[\w,\s]+)?\s*'
    r'\{',                                     # opening brace
    re.MULTILINE
)

# XPath / CSS locator patterns
XPATH_RE         = re.compile(r'"([^"]*//[^"]*)"')          # strings starting with //
BY_XPATH_RE      = re.compile(r'By\.xpath\s*\(\s*"([^"]+)"')
BY_CSS_RE        = re.compile(r'By\.cssSelector\s*\(\s*"([^"]+)"')
BY_ID_RE         = re.compile(r'By\.id\s*\(\s*"([^"]+)"')
BY_NAME_RE       = re.compile(r'By\.name\s*\(\s*"([^"]+)"')
BY_CLASS_RE      = re.compile(r'By\.className\s*\(\s*"([^"]+)"')
BY_TAG_RE        = re.compile(r'By\.tagName\s*\(\s*"([^"]+)"')
BY_LINK_RE       = re.compile(r'By\.linkText\s*\(\s*"([^"]+)"')
BY_PARTIAL_RE    = re.compile(r'By\.partialLinkText\s*\(\s*"([^"]+)"')
FIND_ELEMENT_RE  = re.compile(r'findElement\s*\(\s*By\.\w+\s*\(\s*"([^"]+)"')

# FIX 1: @FindBy annotation pattern (PageFactory style)
# e.g. @FindBy(xpath = "//button[@id='submit']")
# e.g. @FindBy(css = ".my-class")
# e.g. @FindBy(id = "submit")
FINDBY_RE        = re.compile(
    r'@FindBy\s*\(\s*(?:xpath|css|id|name|className|tagName|linkText|partialLinkText)\s*=\s*"([^"]+)"'
)

# FIX 2: String constant locators
# e.g. private static final String LOGIN_BTN_XPATH = "//button[@id='login']";
# We track by field name → string value so method bodies referencing field name get linked
STRING_CONST_LOCATOR_RE = re.compile(
    r'(?:private\s+|public\s+|protected\s+)?(?:static\s+)?(?:final\s+)?'
    r'String\s+(\w*(?:XPATH|CSS|LOCATOR|SELECTOR|PATH|xpath|css|locator|selector|path)\w*)\s*=\s*"([^"]+)"'
)

# Method call: someObject.method( or method(
METHOD_CALL_RE   = re.compile(r'(?:[\w]+\.)?(\w+)\s*\(')

# Locator field assignments (e.g. private By loginBtn = By.xpath("..."))
LOCATOR_FIELD_RE = re.compile(
    r'(?:By|String)\s+(\w+)\s*=\s*By\.(?:xpath|cssSelector|id|name|className|tagName|linkText|partialLinkText)\s*\(\s*"([^"]+)"'
)

# Field declaration pattern: captures (TypeName, varName) from class-level field declarations
# e.g. "AdminPage adminPage = new AdminPage(driver);" → ("AdminPage", "adminPage")
FIELD_DECL_RE = re.compile(
    r'(?:private|public|protected)?\s*(?:static\s+)?(?:final\s+)?'
    r'([A-Z]\w+)\s+(\w+)\s*(?:=|;)'
)

# Typed call pattern: captures (objectName, methodName) from "obj.method()" calls
# e.g. "adminPage.clickAdd()" → ("adminPage", "clickAdd")
TYPED_CALL_RE = re.compile(r'\b(\w+)\.(\w+)\s*\(')

# Noise words to filter from method call extraction (Java keywords + common types)
_CALL_NOISE = frozenset({
    'if', 'while', 'for', 'switch', 'catch', 'try', 'else', 'new',
    'return', 'throw', 'assert', 'instanceof',
    'System', 'String', 'Integer', 'Long', 'Double', 'Boolean', 'List',
    'Map', 'Set', 'Array', 'Arrays', 'Collections', 'Optional',
    'int', 'boolean', 'void', 'null', 'true', 'false', 'super', 'this',
    'Object', 'Exception', 'Thread', 'Math', 'Duration', 'WebDriverWait',
    'ExpectedConditions', 'JavascriptExecutor', 'Actions',
})


# ──────────────────────────────────────────────
# Brace-aware body extractor
# ──────────────────────────────────────────────

def extract_body(source: str, open_brace_pos: int) -> str:
    """Given the position of '{', extract the full method body including nested braces."""
    depth = 0
    i = open_brace_pos
    start = open_brace_pos
    in_string = False
    in_char = False
    in_line_comment = False
    in_block_comment = False

    while i < len(source):
        c = source[i]

        # Handle comments
        if in_line_comment:
            if c == '\n':
                in_line_comment = False
            i += 1
            continue
        if in_block_comment:
            if source[i:i+2] == '*/':
                in_block_comment = False
                i += 2
                continue
            i += 1
            continue

        # Handle strings
        if c == '"' and not in_char:
            if i > 0 and source[i-1] == '\\':
                i += 1
                continue
            in_string = not in_string
            i += 1
            continue
        if in_string:
            i += 1
            continue

        # Handle char literals
        if c == "'" and not in_string:
            in_char = not in_char
            i += 1
            continue
        if in_char:
            i += 1
            continue

        # Detect comment starts
        if source[i:i+2] == '//':
            in_line_comment = True
            i += 2
            continue
        if source[i:i+2] == '/*':
            in_block_comment = True
            i += 2
            continue

        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                return source[start:i+1]
        i += 1
    return source[start:]


def line_of(source: str, pos: int) -> int:
    return source[:pos].count('\n') + 1


# ──────────────────────────────────────────────
# Locator extraction helpers
# ──────────────────────────────────────────────

def extract_locators_from_text(text: str) -> List[str]:
    locators = []
    for pattern in [BY_XPATH_RE, BY_CSS_RE, BY_ID_RE, BY_NAME_RE,
                    BY_CLASS_RE, BY_TAG_RE, BY_LINK_RE, BY_PARTIAL_RE,
                    FIND_ELEMENT_RE, FINDBY_RE]:
        locators.extend(pattern.findall(text))
    # Also pick up raw xpath strings (start with // or ./)
    for m in XPATH_RE.finditer(text):
        val = m.group(1)
        if val not in locators:
            locators.append(val)
    return list(set(locators))


# ──────────────────────────────────────────────
# Main parser
# ──────────────────────────────────────────────

class JavaFileParser:

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
        if not class_match:
            return None
        class_name = class_match.group(1)

        # Extract locator fields defined at class level
        # Pattern 1: By field = By.xpath("...")  — standard POM
        class_level_locators: Dict[str, str] = {}
        for m in LOCATOR_FIELD_RE.finditer(source):
            class_level_locators[m.group(1)] = m.group(2)

        # FIX 1: @FindBy(xpath="...") field — PageFactory style
        # @FindBy annotations precede a field declaration, so we capture the
        # WebElement field name on the NEXT line after the annotation.
        for m in re.finditer(
            r'@FindBy\s*\(\s*(?:xpath|css|id|name|className|tagName|linkText|partialLinkText)\s*=\s*"([^"]+)"\s*\)\s*'
            r'(?:@\w+\s*)*'                    # optional other annotations
            r'(?:private|public|protected)?\s*'
            r'(?:static\s+)?(?:final\s+)?'
            r'(?:WebElement|List\s*<\s*WebElement\s*>)\s+(\w+)',
            source
        ):
            locator_value = m.group(1)
            field_name    = m.group(2)
            class_level_locators[field_name] = locator_value

        # FIX 2: String constant locators e.g. XPATH_LOGIN_BTN = "//button[@id='login']"
        for m in STRING_CONST_LOCATOR_RE.finditer(source):
            class_level_locators[m.group(1)] = m.group(2)

        # Extract class-level field type declarations: varName → TypeName
        # e.g. "AdminPage adminPage = new AdminPage(driver);" → adminPage:AdminPage
        _java_builtins = frozenset({
            'String','int','boolean','void','long','double','float','char','byte',
            'Integer','Long','Double','Boolean','List','Map','Set','Object',
            'WebDriver','WebElement','By','WebDriverWait','Duration','Actions',
            'JavascriptExecutor','ExpectedConditions','WebDriverException',
        })
        class_field_types: Dict[str, str] = {}
        for m in FIELD_DECL_RE.finditer(source):
            type_name = m.group(1)
            var_name  = m.group(2)
            if type_name not in _java_builtins and not type_name[0].islower():
                class_field_types[var_name] = type_name

        methods = self._extract_methods(source, class_name, file_path, class_level_locators, class_field_types)

        return ParsedFile(
            file_path=file_path,
            class_name=class_name,
            package=package,
            imports=imports,
            methods=methods,
            raw_source=source,
            class_level_locators=class_level_locators,
            class_field_types=class_field_types
        )

    def _extract_methods(
        self,
        source: str,
        class_name: str,
        file_path: str,
        class_level_locators: Dict[str, str],
        class_field_types: Dict[str, str] = None
    ) -> List[MethodInfo]:
        if class_field_types is None:
            class_field_types = {}

        methods = []
        # Find all method matches
        for match in METHOD_RE.finditer(source):
            annotation_block = match.group(1)
            method_name = match.group(2)

            # Skip constructors that look like class names (heuristic)
            # Skip common non-method keywords
            if method_name in ('if', 'while', 'for', 'switch', 'catch', 'try', 'else',
                                'new', 'return', 'class', 'interface', 'enum'):
                continue

            # Parse annotations
            annotations = ANNOTATION_RE.findall(annotation_block)
            is_test = any(a in ('Test', 'org.testng.annotations.Test',
                                'org.junit.Test', 'org.junit.jupiter.api.Test')
                          for a in annotations)

            # Find the opening brace position
            brace_pos = match.end() - 1  # last char of match is '{'
            body = extract_body(source, brace_pos)

            line_num = line_of(source, match.start())
            fq = f"{class_name}#{method_name}"

            # Extract calls from body
            calls = self._extract_calls(body, method_name)

            # Extract locators from body
            locators = extract_locators_from_text(body)

            # Resolve locator field usages:
            # Track BOTH the resolved xpath value AND the field name used.
            # This lets the impact analyzer do scoped lookups:
            #   "which field of THIS class changed" → which methods use that field
            locator_fields_used: Set[str] = set()
            for field_name, locator_value in class_level_locators.items():
                if re.search(r'\b' + re.escape(field_name) + r'\b', body):
                    locator_fields_used.add(field_name)   # track the field NAME
                    if locator_value not in locators:
                        locators.append(locator_value)    # also keep resolved value

            # Extract typed calls: "varName.methodName()" patterns
            # These allow us to resolve "adminPage.clickAdd()" → AdminPage#clickAdd
            typed_calls: Dict[str, Set[str]] = {}
            cleaned_body = re.sub(r'"[^"]*"', '""', body)
            for tc in TYPED_CALL_RE.finditer(cleaned_body):
                var_name    = tc.group(1)
                method_name_called = tc.group(2)
                if var_name in class_field_types and var_name != 'this':
                    typed_calls.setdefault(var_name, set()).add(method_name_called)

            methods.append(MethodInfo(
                class_name=class_name,
                method_name=method_name,
                full_qualified=fq,
                file_path=file_path,
                line_number=line_num,
                is_test=is_test,
                annotations=annotations,
                body=body,
                calls=calls,
                locators=locators,
                locator_fields_used=locator_fields_used,
                typed_calls=typed_calls
            ))

        return methods

    def _extract_calls(self, body: str, current_method: str) -> Set[str]:
        """Extract all method names called in the body."""
        calls = set()
        # Remove string literals to avoid false positives
        cleaned = re.sub(r'"[^"]*"', '""', body)
        cleaned = re.sub(r'//.*?\n', '\n', cleaned)
        cleaned = re.sub(r'/\*.*?\*/', '', cleaned, flags=re.DOTALL)

        noise = _CALL_NOISE | {current_method}
        for m in METHOD_CALL_RE.finditer(cleaned):
            name = m.group(1)
            if name and name not in noise:
                calls.add(name)
        return calls


# ──────────────────────────────────────────────
# Repository scanner
# ──────────────────────────────────────────────

class RepositoryScanner:

    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.parser = JavaFileParser()

    def scan(self) -> List[ParsedFile]:
        parsed_files = []
        for root, dirs, files in os.walk(self.repo_path):
            # Skip hidden / build directories
            dirs[:] = [d for d in dirs if d not in (
                '.git', 'target', 'build', 'out', '.idea', 'node_modules', '.gradle'
            )]
            for fname in files:
                if fname.endswith('.java'):
                    fpath = os.path.join(root, fname)
                    result = self.parser.parse_file(fpath)
                    if result:
                        parsed_files.append(result)
        return parsed_files
