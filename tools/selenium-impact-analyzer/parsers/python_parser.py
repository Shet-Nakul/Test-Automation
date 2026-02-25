import re
import os
import ast
from typing import List, Dict, Set, Optional
from core.models import MethodInfo, ParsedFile
from core.base_parser import BaseParser

class PythonPytestParser(BaseParser):
    """
    Python parser using the 'ast' module for more reliable analysis than regex.
    """
    def parse_file(self, file_path: str) -> Optional[ParsedFile]:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                source = f.read()
            tree = ast.parse(source)
        except Exception as e:
            print(f"[WARN] Cannot parse {file_path}: {e}")
            return None

        methods: List[MethodInfo] = []
        imports: List[str] = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    for n in node.names: imports.append(n.name)
                else:
                    imports.append(node.module or "")

            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                # Detect if it's a test (starts with test_ or has pytest marks)
                is_test = node.name.startswith('test_')
                annotations = []
                for deco in node.decorator_list:
                    if isinstance(deco, ast.Call) and isinstance(deco.func, ast.Attribute):
                        annotations.append(f"{deco.func.value.id if hasattr(deco.func.value, 'id') else ''}.{deco.func.attr}")
                    elif isinstance(deco, ast.Attribute):
                        annotations.append(f"{deco.value.id if hasattr(deco.value, 'id') else ''}.{deco.attr}")
                    elif isinstance(deco, ast.Name):
                        annotations.append(deco.id)
                
                if any('pytest.mark.test' in a or 'pytest.fixture' in a for a in annotations):
                    is_test = True

                # Extract calls and locators from the function body
                calls, locators = self._analyze_body(node)
                
                # Get class name if nested
                class_name = "Global"
                # Simple check for parent class
                for parent in ast.walk(tree):
                    if isinstance(parent, ast.ClassDef):
                        if node in parent.body:
                            class_name = parent.name
                            if class_name.startswith('Test'): is_test = True
                            break

                methods.append(MethodInfo(
                    class_name=class_name,
                    method_name=node.name,
                    full_qualified=f"{class_name}#{node.name}",
                    file_path=file_path,
                    line_number=node.lineno,
                    is_test=is_test,
                    annotations=annotations,
                    body=ast.get_source_segment(source, node) or "",
                    calls=calls,
                    locators=locators,
                    locator_fields_used=set(),
                    typed_calls={}
                ))

        return ParsedFile(
            file_path=file_path,
            class_name="PythonFile",
            package="",
            imports=imports,
            methods=methods,
            raw_source=source
        )

    def _analyze_body(self, node: ast.AST) -> tuple[Set[str], List[str]]:
        calls = set()
        locators = []
        
        for subnode in ast.walk(node):
            # Extract calls
            if isinstance(subnode, ast.Call):
                if isinstance(subnode.func, ast.Name):
                    calls.add(subnode.func.id)
                elif isinstance(subnode.func, ast.Attribute):
                    calls.add(subnode.func.attr)
                
                # Extract potential Playwright locators: page.locator("...")
                if isinstance(subnode.func, ast.Attribute) and subnode.func.attr == 'locator':
                    if subnode.args and isinstance(subnode.args[0], ast.Constant):
                        locators.append(str(subnode.args[0].value))
            
            # Extract potential CSS/XPath strings
            if isinstance(subnode, ast.Constant) and isinstance(subnode.value, str):
                val = subnode.value
                if val.startswith('//') or val.startswith('.') or val.startswith('#') or '[' in val:
                    if len(val) < 200: # Avoid long strings
                        locators.append(val)
                        
        return calls, list(set(locators))

    def scan_repository(self, repo_path: str) -> List[ParsedFile]:
        parsed_files = []
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in ('.git', '__pycache__', 'venv', '.pytest_cache')]
            for fname in files:
                if fname.endswith('.py'):
                    res = self.parse_file(os.path.join(root, fname))
                    if res: parsed_files.append(res)
        return parsed_files
