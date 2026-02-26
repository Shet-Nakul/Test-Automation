import os
from datetime import datetime
from reporters.base import BaseReporter
from core.models import ImpactReport

class C:
    RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, BOLD, RESET, DIM = '\033[91m', '\033[92m', '\033[93m', '\033[94m', '\033[95m', '\033[96m', '\033[97m', '\033[1m', '\033[0m', '\033[2m'

def colored(text: str, *codes: str) -> str:
    return ''.join(codes) + text + C.RESET

class ConsoleReporter(BaseReporter):
    def report(self, report: ImpactReport, verbose: bool = False):
        print(f"\n{colored('=' * 70, C.BOLD, C.CYAN)}\n{colored('  🔍  IMPACT ANALYZER REPORT', C.BOLD, C.CYAN)}\n{colored('=' * 70, C.BOLD, C.CYAN)}")
        print(colored(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", C.DIM), "\n")
        print(colored("  📝  CHANGES DETECTED", C.BOLD, C.YELLOW), "\n  " + "-" * 40)
        if report.changed_methods:
            print(colored("  Changed Methods:", C.BOLD))
            for m in report.changed_methods: print(colored(f"    ✏  {m}", C.MAGENTA))
        if report.changed_locators:
            print(colored("\n  Changed Locators:", C.BOLD))
            for loc in report.changed_locators: print(colored(f"    🔗  {loc[:80]}...", C.BLUE) if len(loc) > 80 else colored(f"    🔗  {loc}", C.BLUE))
        
        test_count = len(report.unique_test_names)
        if test_count == 0:
            print(f"\n{colored('  ✅  NO IMPACTED TEST CASES FOUND', C.BOLD, C.GREEN)}")
        else:
            print(f"\n{colored(f'  🚨  {test_count} IMPACTED TEST CASE(S) FOUND', C.BOLD, C.RED)}\n  " + "-" * 40 + "\n")
            by_root = {}
            for it in report.impacted_tests: by_root.setdefault(it.change_root, []).append(it)
            for root, tests in by_root.items():
                print(colored(f"  Change: {root}", C.BOLD, C.YELLOW))
                seen = set()
                for it in tests:
                    if it.test_method.full_qualified in seen: continue
                    seen.add(it.test_method.full_qualified)
                    print(f"{colored(f'    🧪  {it.test_method.class_name}', C.CYAN)} → {colored(f'{it.test_method.method_name}()', C.BOLD, C.RED)}")
                    if verbose and len(it.call_path) > 1:
                        for i, node in enumerate(it.call_path):
                            print(f"{' ' * 12}{'  ' * i}{'🔴' if i==0 else ('🧪' if i==len(it.call_path)-1 else '├─')} {node}")
                print()
        print(colored("=" * 70, C.BOLD, C.CYAN), "\n")

class CiSummaryReporter(BaseReporter):
    def report(self, report: ImpactReport, **kwargs):
        lines = []
        total = len(report.unique_test_names)

        if total == 0:
            lines.append("> ✅ **No tests impacted — safe to merge.**")
            print("\n".join(lines))
            return

        lines.append(f"> 🚨 **{total} test case(s) impacted — merge is blocked until reviewed.**")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## 🔍 Impact Analysis Report")
        lines.append("")
        lines.append("### 📝 What Changed")
        lines.append("")

        if report.changed_methods:
            lines.append("**Modified Methods:**")
            for m in report.changed_methods:
                lines.append(f"- `{m}()`")
            lines.append("")

        if report.changed_locators:
            lines.append("**Changed Locators:**")
            for loc in report.changed_locators:
                lines.append(f"- `{loc[:100]}...`" if len(loc) > 100 else f"- `{loc}`")
            lines.append("")

        lines.append("### 🧪 Impacted Tests")
        lines.append("")
        lines.append("| Test Class | Test Method | File |")
        lines.append("|-----------|-------------|------|")
        
        seen = set()
        for it in report.impacted_tests:
            key = it.test_method.full_qualified
            if key in seen: continue
            seen.add(key)
            lines.append(f"| `{it.test_method.class_name}` | `{it.test_method.method_name}()` | `{os.path.basename(it.test_method.file_path)}:{it.test_method.line_number}` |")

        mapping = {}
        for it in report.impacted_tests:
            tm = it.test_method
            if not tm.is_test: continue
            if not tm.file_path.endswith('.java'): continue
            pkg = tm.package_name.strip()
            fqcn = f"{pkg}.{tm.class_name}" if pkg else tm.class_name
            s = mapping.setdefault(fqcn, set())
            s.add(tm.method_name)
        if mapping:
            lines.append("")
            lines.append("### ▶ Runnable TestNG XML")
            lines.append("")
            xml_lines = []
            xml_lines.append("<suite name=\"ImpactedSuite\">")
            xml_lines.append("  <test name=\"ImpactedTests\">")
            xml_lines.append("    <classes>")
            for cls, methods in sorted(mapping.items()):
                xml_lines.append(f"      <class name=\"{cls}\">")
                xml_lines.append("        <methods>")
                for m in sorted(methods):
                    xml_lines.append(f"          <include name=\"{m}\"/>")
                xml_lines.append("        </methods>")
                xml_lines.append("      </class>")
            xml_lines.append("    </classes>")
            xml_lines.append("  </test>")
            xml_lines.append("</suite>")
            lines.append("```xml")
            lines.extend(xml_lines)
            lines.append("```")

        print("\n".join(lines))
