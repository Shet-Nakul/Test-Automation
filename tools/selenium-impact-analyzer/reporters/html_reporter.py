from datetime import datetime
from reporters.base import BaseReporter
from core.models import ImpactReport

class HtmlReporter(BaseReporter):
    def report(self, report: ImpactReport, output_path: str = "report.html"):
        unique_tests = report.unique_test_names
        test_count = len(unique_tests)
        status_color = "#e74c3c" if test_count > 0 else "#27ae60"
        status_text = f"⚠ {test_count} Test(s) Impacted" if test_count > 0 else "✅ No Tests Impacted"

        test_cards_html, seen = "", set()
        for it in report.impacted_tests:
            if it.test_method.full_qualified in seen: continue
            seen.add(it.test_method.full_qualified)
            path_items = []
            for i, node in enumerate(it.call_path):
                node_class = 'path-changed' if i == 0 else ('path-test' if i == len(it.call_path) - 1 else 'path-helper')
                if i == 0:
                    badge_html = "<span class='badge badge-changed'>CHANGED</span>"
                elif i == len(it.call_path) - 1:
                    badge_html = "<span class='badge badge-test'>@Test</span>"
                else:
                    badge_html = "<span class='badge badge-middle'>helper</span>"
                arrow_html = "<div class='path-arrow'>▼ calls</div>" if i == 0 else ""
                path_items.append(f"{arrow_html}<div class='path-node {node_class}'>{badge_html} {node}</div>")
            path_html = "".join(path_items)
            test_cards_html += f"<div class='test-card'><div class='test-header'><span class='test-icon'>🧪</span><span class='test-class'>{it.test_method.class_name}</span><span class='test-sep'>→</span><span class='test-method'>{it.test_method.method_name}()</span></div><div class='test-meta'><span>📁 {it.test_method.file_path}</span><span>📍 Line {it.test_method.line_number}</span><span>🔗 Triggered by: <code>{it.change_root}</code></span></div><details class='call-chain'><summary>📞 Call Chain ({len(it.call_path)} hops)</summary><div class='path-container'>{path_html}</div></details></div>"

        method_items = ''.join(f'<li><code>{m}</code></li>' for m in report.changed_methods) or '<li class="none">None detected</li>'
        locator_items = ''.join(f'<li><code>{l[:100]}</code></li>' for l in report.changed_locators) or '<li class="none">None detected</li>'

        html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>Impact Report</title><style>body {{ font-family: sans-serif; background: #0f1117; color: #e0e0e0; padding: 20px; }} .container {{ max-width: 1100px; margin: 0 auto; }} .header {{ background: #1a1a2e; padding: 20px; border-radius: 12px; }} .status-banner {{ background: {status_color}22; border: 1px solid {status_color}; border-radius: 10px; padding: 20px; margin: 20px 0; font-size: 22px; font-weight: bold; color: {status_color}; text-align: center; }} .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }} .card {{ background: #1a1a2e; border: 1px solid #2a2a4a; border-radius: 10px; padding: 20px; }} .test-card {{ background: #1a1a2e; border-left: 4px solid #e74c3c; padding: 20px; margin-bottom: 14px; border-radius: 10px; }} .path-container {{ background: #0d1117; padding: 14px; border-radius: 8px; }} .badge {{ font-size: 10px; padding: 2px 7px; border-radius: 4px; color: white; margin-right: 6px; }} .badge-changed {{ background: #e74c3c; }} .badge-test {{ background: #27ae60; }} .badge-middle {{ background: #3498db; }}</style></head><body><div class="container"><div class="header"><h1>🔍 Impact Analyzer Report</h1><p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p></div><div class="status-banner">{status_text}</div><div class="grid"><div class="card"><h3>✏ Changed Methods</h3><ul>{method_items}</ul></div><div class="card"><h3>🔗 Changed Locators</h3><ul>{locator_items}</ul></div></div><h3 style='margin-top:20px'>🧪 Impacted Tests</h3>{test_cards_html}</div></body></html>"""
        with open(output_path, 'w', encoding='utf-8') as f: f.write(html)
        print(f"[HTML] Report saved to: {output_path}")
