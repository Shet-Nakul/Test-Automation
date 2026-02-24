"""
Report Generator
================
Formats the ImpactReport into human-readable output:
  - Console (colored text)
  - JSON
  - HTML report
  - CI-friendly summary (plain text)
"""

import json
import os
from datetime import datetime
from typing import List
from core.call_graph import ImpactReport, ImpactedTest


# ──────────────────────────────────────────────
# ANSI Colors (console)
# ──────────────────────────────────────────────

class C:
    RED     = '\033[91m'
    GREEN   = '\033[92m'
    YELLOW  = '\033[93m'
    BLUE    = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN    = '\033[96m'
    WHITE   = '\033[97m'
    BOLD    = '\033[1m'
    RESET   = '\033[0m'
    DIM     = '\033[2m'


def colored(text: str, *codes: str) -> str:
    return ''.join(codes) + text + C.RESET


# ──────────────────────────────────────────────
# Console Reporter
# ──────────────────────────────────────────────

class ConsoleReporter:

    def print_report(self, report: ImpactReport, verbose: bool = False):
        print()
        print(colored("=" * 70, C.BOLD, C.CYAN))
        print(colored("  🔍  SELENIUM IMPACT ANALYZER - REPORT", C.BOLD, C.CYAN))
        print(colored("=" * 70, C.BOLD, C.CYAN))
        print(colored(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", C.DIM))
        print()

        # ── Changes detected ──────────────────────────
        print(colored("  📝  CHANGES DETECTED", C.BOLD, C.YELLOW))
        print(colored("  " + "-" * 40, C.YELLOW))

        if report.changed_methods:
            print(colored("  Changed Methods:", C.BOLD))
            for m in report.changed_methods:
                print(colored(f"    ✏  {m}", C.MAGENTA))
        else:
            print(colored("  No changed methods detected", C.DIM))

        if report.changed_locators:
            print(colored("\n  Changed Locators (XPath/CSS):", C.BOLD))
            for loc in report.changed_locators:
                display = loc[:80] + '...' if len(loc) > 80 else loc
                print(colored(f"    🔗  {display}", C.BLUE))
        else:
            print(colored("  No changed locators detected", C.DIM))

        print()

        # ── Impact summary ─────────────────────────────
        unique_tests = report.unique_test_names
        test_count = len(unique_tests)

        if test_count == 0:
            print(colored("  ✅  NO IMPACTED TEST CASES FOUND", C.BOLD, C.GREEN))
            print(colored("  Changes appear to be isolated or no test coverage found.", C.DIM))
        else:
            print(colored(f"  🚨  {test_count} IMPACTED TEST CASE(S) FOUND", C.BOLD, C.RED))
            print(colored("  " + "-" * 40, C.RED))
            print()

            # Group by change root
            by_root: dict = {}
            for it in report.impacted_tests:
                by_root.setdefault(it.change_root, []).append(it)

            for change_root, impacted_list in by_root.items():
                print(colored(f"  Change: {change_root}", C.BOLD, C.YELLOW))

                # Deduplicate tests for this root
                seen = set()
                for it in impacted_list:
                    test_fq = it.test_method.full_qualified
                    if test_fq in seen:
                        continue
                    seen.add(test_fq)

                    # Test header
                    print(colored(f"    🧪  {it.test_method.class_name}", C.CYAN) +
                          colored(f" → ", C.DIM) +
                          colored(f"{it.test_method.method_name}()", C.BOLD, C.RED))
                    print(colored(f"         📁 {it.test_method.file_path}", C.DIM))
                    print(colored(f"         📍 Line {it.test_method.line_number}", C.DIM))

                    if verbose and len(it.call_path) > 1:
                        print(colored("         📞 Call Chain:", C.DIM))
                        for i, node in enumerate(it.call_path):
                            indent = "            " + ("  " * i)
                            arrow = "└─" if i == len(it.call_path) - 1 else "├─"
                            if i == 0:
                                print(colored(f"            🔴 {node}  ← CHANGED", C.RED))
                            elif i == len(it.call_path) - 1:
                                print(colored(f"            🧪 {node}  ← @Test", C.GREEN))
                            else:
                                print(colored(f"            {arrow} {node}", C.DIM))
                    print()
                print()

        # ── Full blast radius ──────────────────────────
        if verbose and report.all_impacted_fq:
            print(colored("  🌊  FULL BLAST RADIUS (All Impacted Nodes)", C.BOLD, C.BLUE))
            print(colored("  " + "-" * 40, C.BLUE))
            for fq in sorted(report.all_impacted_fq):
                print(colored(f"    · {fq}", C.DIM))
            print()

        print(colored("=" * 70, C.BOLD, C.CYAN))
        print()


# ──────────────────────────────────────────────
# JSON Reporter
# ──────────────────────────────────────────────

class JsonReporter:

    def to_dict(self, report: ImpactReport) -> dict:
        tests = []
        seen = set()
        for it in report.impacted_tests:
            test_fq = it.test_method.full_qualified
            if test_fq in seen:
                continue
            seen.add(test_fq)
            tests.append({
                "class": it.test_method.class_name,
                "method": it.test_method.method_name,
                "full_qualified": test_fq,
                "file": it.test_method.file_path,
                "line": it.test_method.line_number,
                "change_root": it.change_root,
                "call_path": it.call_path
            })

        return {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "changed_methods": report.changed_methods,
                "changed_locators": report.changed_locators,
                "impacted_test_count": len(report.unique_test_names),
            },
            "impacted_tests": tests,
            "blast_radius": sorted(report.all_impacted_fq)
        }

    def to_json(self, report: ImpactReport, indent: int = 2) -> str:
        return json.dumps(self.to_dict(report), indent=indent)

    def save(self, report: ImpactReport, output_path: str):
        with open(output_path, 'w') as f:
            json.dump(self.to_dict(report), f, indent=2)
        print(f"[JSON] Report saved to: {output_path}")


# ──────────────────────────────────────────────
# HTML Reporter
# ──────────────────────────────────────────────

class HtmlReporter:

    def generate(self, report: ImpactReport) -> str:
        unique_tests = report.unique_test_names
        test_count = len(unique_tests)
        status_color = "#e74c3c" if test_count > 0 else "#27ae60"
        status_text = f"⚠ {test_count} Test(s) Impacted" if test_count > 0 else "✅ No Tests Impacted"

        # Build test cards
        test_cards_html = ""
        seen = set()
        for it in report.impacted_tests:
            test_fq = it.test_method.full_qualified
            if test_fq in seen:
                continue
            seen.add(test_fq)

            # Build call path visualization
            path_html = ""
            for i, node in enumerate(it.call_path):
                is_first = i == 0
                is_last = i == len(it.call_path) - 1
                if is_first:
                    badge = '<span class="badge badge-changed">CHANGED</span>'
                elif is_last:
                    badge = '<span class="badge badge-test">@Test</span>'
                else:
                    badge = '<span class="badge badge-middle">helper</span>'

                arrow = "" if i == 0 else '<div class="path-arrow">▼ calls</div>'
                path_html += f"""
                    {arrow}
                    <div class="path-node {'path-changed' if is_first else ('path-test' if is_last else 'path-helper')}">
                        {badge} {node}
                    </div>"""

            test_cards_html += f"""
            <div class="test-card">
                <div class="test-header">
                    <span class="test-icon">🧪</span>
                    <span class="test-class">{it.test_method.class_name}</span>
                    <span class="test-sep">→</span>
                    <span class="test-method">{it.test_method.method_name}()</span>
                </div>
                <div class="test-meta">
                    <span>📁 {it.test_method.file_path}</span>
                    <span>📍 Line {it.test_method.line_number}</span>
                    <span>🔗 Triggered by: <code>{it.change_root}</code></span>
                </div>
                <details class="call-chain">
                    <summary>📞 Call Chain ({len(it.call_path)} hops)</summary>
                    <div class="path-container">{path_html}</div>
                </details>
            </div>"""

        # Changed items
        method_items = ''.join(f'<li><code>{m}</code></li>' for m in report.changed_methods) or '<li class="none">None detected</li>'
        locator_items = ''.join(f'<li><code>{l[:100]}</code></li>' for l in report.changed_locators) or '<li class="none">None detected</li>'

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Selenium Impact Analysis Report</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0f1117; color: #e0e0e0; padding: 20px; }}
  .container {{ max-width: 1100px; margin: 0 auto; }}
  .header {{ background: linear-gradient(135deg, #1a1a2e, #16213e); border: 1px solid #0f3460; border-radius: 12px; padding: 30px; margin-bottom: 20px; }}
  .header h1 {{ font-size: 28px; color: #00d4ff; margin-bottom: 8px; }}
  .header .meta {{ color: #888; font-size: 13px; }}
  .status-banner {{ background: {status_color}22; border: 1px solid {status_color}; border-radius: 10px; padding: 20px; margin-bottom: 20px; font-size: 22px; font-weight: bold; color: {status_color}; text-align: center; }}
  .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 20px; }}
  .card {{ background: #1a1a2e; border: 1px solid #2a2a4a; border-radius: 10px; padding: 20px; }}
  .card h3 {{ color: #00d4ff; margin-bottom: 14px; font-size: 15px; text-transform: uppercase; letter-spacing: 1px; }}
  .card ul {{ list-style: none; }}
  .card ul li {{ padding: 6px 0; border-bottom: 1px solid #2a2a4a; font-size: 13px; }}
  .card ul li:last-child {{ border-bottom: none; }}
  .card ul li code {{ background: #0d1b2a; padding: 2px 6px; border-radius: 4px; color: #e2a96c; font-size: 12px; word-break: break-all; }}
  .none {{ color: #555; font-style: italic; }}
  .section-title {{ font-size: 18px; font-weight: bold; color: #e74c3c; margin-bottom: 14px; padding-left: 4px; }}
  .test-card {{ background: #1a1a2e; border: 1px solid #3a2a4a; border-left: 4px solid #e74c3c; border-radius: 10px; padding: 20px; margin-bottom: 14px; }}
  .test-header {{ display: flex; align-items: center; gap: 10px; margin-bottom: 10px; flex-wrap: wrap; }}
  .test-icon {{ font-size: 20px; }}
  .test-class {{ color: #00d4ff; font-weight: bold; font-size: 15px; }}
  .test-sep {{ color: #555; }}
  .test-method {{ color: #e74c3c; font-weight: bold; font-size: 15px; }}
  .test-meta {{ display: flex; gap: 20px; font-size: 12px; color: #888; margin-bottom: 12px; flex-wrap: wrap; }}
  .test-meta code {{ color: #e2a96c; background: #0d1b2a; padding: 2px 6px; border-radius: 4px; }}
  .call-chain summary {{ cursor: pointer; color: #00d4ff; font-size: 13px; padding: 8px 0; }}
  .path-container {{ padding: 14px; background: #0d1117; border-radius: 8px; margin-top: 10px; }}
  .path-node {{ padding: 8px 14px; border-radius: 6px; font-size: 13px; font-family: monospace; margin: 2px 0; }}
  .path-changed {{ background: #3a1010; border: 1px solid #e74c3c; }}
  .path-helper  {{ background: #1a1a2e; border: 1px solid #333; }}
  .path-test    {{ background: #0e2a0e; border: 1px solid #27ae60; }}
  .path-arrow   {{ color: #555; font-size: 12px; padding: 2px 14px; }}
  .badge {{ font-size: 10px; padding: 2px 7px; border-radius: 4px; font-weight: bold; margin-right: 6px; }}
  .badge-changed {{ background: #e74c3c; color: white; }}
  .badge-test    {{ background: #27ae60; color: white; }}
  .badge-middle  {{ background: #3498db; color: white; }}
  .footer {{ text-align: center; color: #555; font-size: 12px; margin-top: 30px; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>🔍 Selenium Impact Analyzer</h1>
    <div class="meta">Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
  </div>

  <div class="status-banner">{status_text}</div>

  <div class="grid">
    <div class="card">
      <h3>✏ Changed Methods</h3>
      <ul>{method_items}</ul>
    </div>
    <div class="card">
      <h3>🔗 Changed Locators</h3>
      <ul>{locator_items}</ul>
    </div>
  </div>

  {"<div class='section-title'>🧪 Impacted Test Cases</div>" + test_cards_html if test_count > 0 else "<div class='card'><h3>✅ No Impacted Tests</h3><p style='color:#888;margin-top:10px;'>The changes do not appear to affect any test cases.</p></div>"}

  <div class="footer">Selenium Impact Analyzer · Auto-generated</div>
</div>
</body>
</html>"""
        return html

    def save(self, report: ImpactReport, output_path: str):
        html = self.generate(report)
        with open(output_path, 'w') as f:
            f.write(html)
        print(f"[HTML] Report saved to: {output_path}")


# ──────────────────────────────────────────────
# CI Summary (plain text, good for PR comments)
# ──────────────────────────────────────────────

class CiSummaryReporter:

    def generate(self, report: ImpactReport) -> str:
        lines = []
        lines.append("## 🔍 Selenium Impact Analysis")
        lines.append("")

        if report.changed_methods:
            lines.append("**Changed Methods:**")
            for m in report.changed_methods:
                lines.append(f"- `{m}`")
            lines.append("")

        if report.changed_locators:
            lines.append("**Changed Locators:**")
            for loc in report.changed_locators[:10]:  # limit for PR comment
                lines.append(f"- `{loc[:80]}`")
            lines.append("")

        unique_tests = report.unique_test_names
        if not unique_tests:
            lines.append("✅ **No impacted test cases found.**")
        else:
            lines.append(f"🚨 **{len(unique_tests)} test case(s) impacted:**")
            lines.append("")
            lines.append("| Test Class | Test Method | File |")
            lines.append("|-----------|-------------|------|")
            seen = set()
            for it in report.impacted_tests:
                if it.test_method.full_qualified in seen:
                    continue
                seen.add(it.test_method.full_qualified)
                fname = os.path.basename(it.test_method.file_path)
                lines.append(f"| `{it.test_method.class_name}` | `{it.test_method.method_name}()` | {fname}:{it.test_method.line_number} |")

        return "\n".join(lines)
