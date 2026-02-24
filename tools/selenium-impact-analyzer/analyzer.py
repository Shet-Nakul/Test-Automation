"""
Selenium Impact Analyzer - Main Entry Point
===========================================
Orchestrates:
  1. Scan repo → build call graph
  2. Detect changes from git diff / diff file / direct input
  3. Trace blast radius via reverse BFS
  4. Report impacted @Test cases

Usage:
  python analyzer.py --repo /path/to/repo --base HEAD~1 --head HEAD [--verbose] [--html report.html] [--json report.json]
  python analyzer.py --repo /path/to/repo --diff changes.diff
  python analyzer.py --repo /path/to/repo --methods "clickLoginButton,enterCredentials" --locators "//button[@id='login']"
"""

import argparse
import os
import sys
import time

# Make sure local imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.java_parser import RepositoryScanner
from core.call_graph import CallGraphBuilder, ImpactAnalyzer
from git.diff_analyzer import GitDiffAnalyzer
from output.reporter import ConsoleReporter, JsonReporter, HtmlReporter, CiSummaryReporter


# ──────────────────────────────────────────────
# Main API class
# ──────────────────────────────────────────────

class SeleniumImpactAnalyzer:

    def __init__(self, repo_path: str, verbose: bool = False):
        self.repo_path = os.path.abspath(repo_path)
        self.verbose = verbose
        self._call_graph = None
        self._scan_time = 0

    def build_call_graph(self):
        """Scan the repository and build the complete call graph."""
        print(f"\n[1/3] Scanning repository: {self.repo_path}")
        start = time.time()
        scanner = RepositoryScanner(self.repo_path)
        parsed_files = scanner.scan()
        self._scan_time = time.time() - start

        print(f"      Found {len(parsed_files)} Java files")
        total_methods = sum(len(pf.methods) for pf in parsed_files)
        total_tests = sum(1 for pf in parsed_files for m in pf.methods if m.is_test)
        print(f"      Parsed {total_methods} methods ({total_tests} @Test methods)")

        print(f"[2/3] Building call graph...")
        builder = CallGraphBuilder()
        self._call_graph = builder.build(parsed_files)

        total_edges = sum(len(v) for v in self._call_graph.forward.values())
        print(f"      Call graph: {len(self._call_graph.method_map_fq)} nodes, {total_edges} edges")
        print(f"      Locators tracked: {len(self._call_graph.locator_to_methods)}")
        print(f"      Scan completed in {self._scan_time:.2f}s")

    def analyze_from_git(
        self,
        base_ref: str = 'HEAD~1',
        head_ref: str = 'HEAD'
    ):
        """Detect changes from git diff and analyze impact."""
        self._ensure_graph()
        print(f"[3/3] Detecting changes: {base_ref}..{head_ref}")
        diff_analyzer = GitDiffAnalyzer()
        diff_result = diff_analyzer.from_repo(self.repo_path, base_ref, head_ref)
        return self._run_analysis(
            diff_result.all_changed_methods,
            diff_result.all_changed_locators,
            diff_result.all_scoped_locator_changes   # ← precise scoped input
        )

    def analyze_from_diff_file(self, diff_file: str):
        """Detect changes from a .diff file and analyze impact."""
        self._ensure_graph()
        print(f"[3/3] Parsing diff file: {diff_file}")
        diff_analyzer = GitDiffAnalyzer()
        diff_result = diff_analyzer.from_diff_file(diff_file)
        return self._run_analysis(
            diff_result.all_changed_methods,
            diff_result.all_changed_locators,
            diff_result.all_scoped_locator_changes
        )

    def analyze_direct(
        self,
        changed_methods: list = None,
        changed_locators: list = None
    ):
        """Directly specify changed methods/locators and analyze impact."""
        self._ensure_graph()
        print(f"[3/3] Analyzing direct input...")
        return self._run_analysis(changed_methods or [], changed_locators or [])

    def _run_analysis(self, changed_methods: list, changed_locators: list, changed_scoped_locators: list = None):
        print(f"      Changed methods:         {changed_methods}")
        print(f"      Changed locators (raw):  {len(changed_locators)} locator(s)")
        if changed_scoped_locators:
            print(f"      Changed locators (scoped): {len(changed_scoped_locators)} field(s)")
            for cls, field, val in changed_scoped_locators:
                print(f"        → {cls}#{field} = '{val[:60]}'")

        analyzer = ImpactAnalyzer(self._call_graph)
        report = analyzer.analyze(changed_methods, changed_locators, changed_scoped_locators)
        return report

    def _ensure_graph(self):
        if self._call_graph is None:
            self.build_call_graph()


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='Selenium Impact Analyzer - Find impacted @Test cases from code changes',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze last commit
  python analyzer.py --repo ./my-test-repo

  # Analyze specific git refs
  python analyzer.py --repo ./my-test-repo --base origin/main --head feature/login-fix

  # Analyze from a diff file (e.g. from GitHub PR)
  python analyzer.py --repo ./my-test-repo --diff pr_changes.diff

  # Directly specify changed items
  python analyzer.py --repo ./my-test-repo --methods "clickLoginButton" --locators "//button[@id='login']"

  # Full output with HTML report
  python analyzer.py --repo ./my-test-repo --html report.html --json report.json --verbose
        """
    )

    parser.add_argument('--repo',     required=True, help='Path to the test automation repository')
    parser.add_argument('--base',     default='HEAD~1', help='Base git ref (default: HEAD~1)')
    parser.add_argument('--head',     default='HEAD',   help='Head git ref (default: HEAD)')
    parser.add_argument('--diff',     help='Path to a .diff / .patch file instead of git diff')
    parser.add_argument('--methods',  help='Comma-separated list of changed method names')
    parser.add_argument('--locators', help='Comma-separated list of changed XPath/CSS locators')
    parser.add_argument('--html',     help='Save HTML report to this path')
    parser.add_argument('--json',     help='Save JSON report to this path')
    parser.add_argument('--ci',       action='store_true', help='Print CI-friendly markdown summary')
    parser.add_argument('--verbose',  action='store_true', help='Show call chains and blast radius')

    args = parser.parse_args()

    # Validate repo
    if not os.path.isdir(args.repo):
        print(f"[ERROR] Repo path not found: {args.repo}")
        sys.exit(1)

    # Initialize
    analyzer = SeleniumImpactAnalyzer(args.repo, verbose=args.verbose)
    analyzer.build_call_graph()

    # Detect changes
    if args.methods or args.locators:
        changed_methods = [m.strip() for m in args.methods.split(',')] if args.methods else []
        changed_locators = [l.strip() for l in args.locators.split(',')] if args.locators else []
        report = analyzer.analyze_direct(changed_methods, changed_locators)
    elif args.diff:
        report = analyzer.analyze_from_diff_file(args.diff)
    else:
        report = analyzer.analyze_from_git(args.base, args.head)

    # Console output
    ConsoleReporter().print_report(report, verbose=args.verbose)

    # Optional outputs
    if args.html:
        HtmlReporter().save(report, args.html)

    if args.json:
        JsonReporter().save(report, args.json)

    if args.ci:
        print(CiSummaryReporter().generate(report))

    # Exit code: 0 = no impact, 1 = tests impacted (useful for CI gates)
    sys.exit(1 if report.unique_test_names else 0)


if __name__ == '__main__':
    main()
