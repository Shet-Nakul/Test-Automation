import json
from datetime import datetime
from reporters.base import BaseReporter
from core.models import ImpactReport

class JsonReporter(BaseReporter):
    def report(self, report: ImpactReport, output_path: str = "report.json"):
        data = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "changed_methods": report.changed_methods,
                "changed_locators": report.changed_locators,
                "impacted_test_count": len(report.unique_test_names),
            },
            "impacted_tests": [{
                "class": it.test_method.class_name,
                "method": it.test_method.method_name,
                "full_qualified": it.test_method.full_qualified,
                "file": it.test_method.file_path,
                "line": it.test_method.line_number,
                "change_root": it.change_root,
                "call_path": it.call_path
            } for it in report.impacted_tests],
            "blast_radius": sorted(report.all_impacted_fq)
        }
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"[JSON] Report saved to: {output_path}")
