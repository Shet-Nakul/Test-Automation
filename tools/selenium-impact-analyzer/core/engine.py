from collections import defaultdict, deque
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field
from core.models import ParsedFile, MethodInfo, ImpactedTest, ImpactReport

@dataclass
class CallGraph:
    method_map_short: Dict[str, List[MethodInfo]] = field(default_factory=lambda: defaultdict(list))
    method_map_fq: Dict[str, MethodInfo] = field(default_factory=dict)
    forward: Dict[str, Set[str]] = field(default_factory=lambda: defaultdict(set))
    reverse: Dict[str, Set[str]] = field(default_factory=lambda: defaultdict(set))
    locator_to_methods: Dict[str, Set[str]] = field(default_factory=lambda: defaultdict(set))
    scoped_field_to_methods: Dict[str, Set[str]] = field(default_factory=lambda: defaultdict(set))
    class_field_map: Dict[str, Dict[str, str]] = field(default_factory=lambda: defaultdict(dict))
    test_methods: List[MethodInfo] = field(default_factory=list)

class CallGraphBuilder:
    def build(self, parsed_files: List[ParsedFile]) -> CallGraph:
        graph = CallGraph()
        for pf in parsed_files:
            if hasattr(pf, 'class_level_locators'):
                graph.class_field_map[pf.class_name] = pf.class_level_locators
            if hasattr(pf, 'class_field_types'):
                graph.class_field_map[f"__types__{pf.class_name}"] = pf.class_field_types

        for pf in parsed_files:
            for method in pf.methods:
                graph.method_map_fq[method.full_qualified] = method
                graph.method_map_short[method.method_name].append(method)
                if method.is_test:
                    graph.test_methods.append(method)
                for loc in method.locators:
                    graph.locator_to_methods[loc].add(method.full_qualified)
                for field_name in method.locator_fields_used:
                    scoped_key = f"{method.class_name}#{field_name}"
                    graph.scoped_field_to_methods[scoped_key].add(method.full_qualified)

        for pf in parsed_files:
            field_types = graph.class_field_map.get(f"__types__{pf.class_name}", {})
            for method in pf.methods:
                caller_fq = method.full_qualified
                resolved_callees: Set[str] = set()
                for var_name, method_names in method.typed_calls.items():
                    target_class = field_types.get(var_name)
                    if target_class:
                        for mn in method_names:
                            candidate_fq = f"{target_class}#{mn}"
                            if candidate_fq in graph.method_map_fq:
                                resolved_callees.add(candidate_fq)
                for called_name in method.calls:
                    already_resolved = any(fq.endswith(f"#{called_name}") for fq in resolved_callees)
                    if already_resolved:
                        continue
                    same_class_fq = f"{pf.class_name}#{called_name}"
                    if same_class_fq in graph.method_map_fq:
                        resolved_callees.add(same_class_fq)
                    else:
                        for callee in graph.method_map_short.get(called_name, []):
                            resolved_callees.add(callee.full_qualified)
                for callee_fq in resolved_callees:
                    graph.forward[caller_fq].add(callee_fq)
                    graph.reverse[callee_fq].add(caller_fq)
        return graph

class ImpactAnalyzer:
    def __init__(self, call_graph: CallGraph):
        self.graph = call_graph

    def analyze(self, changed_methods: List[str], changed_locators: List[str], changed_scoped_locators: Optional[List[tuple]] = None) -> ImpactReport:
        starting_fq: Dict[str, str] = {}
        for cm in changed_methods:
            resolved = self._resolve_method(cm)
            for fq in resolved:
                starting_fq[fq] = cm

        for scoped_item in (changed_scoped_locators or []):
            class_name, field_name = scoped_item[0], scoped_item[1]
            xpath_value = scoped_item[3] if len(scoped_item) == 4 else scoped_item[2]
            scoped_key = f"{class_name}#{field_name}"
            label = f"LOCATOR:{field_name} ({class_name})"
            if scoped_key in self.graph.scoped_field_to_methods:
                for fq in self.graph.scoped_field_to_methods[scoped_key]:
                    starting_fq[fq] = label
            else:
                for fq, method in self.graph.method_map_fq.items():
                    if method.class_name == class_name and xpath_value in method.locators:
                        starting_fq[fq] = label

        if not changed_scoped_locators:
            for loc in changed_locators:
                if loc in self.graph.locator_to_methods:
                    for fq in self.graph.locator_to_methods[loc]:
                        if fq not in starting_fq:
                            starting_fq[fq] = f"LOCATOR:{loc}"
                else:
                    for stored_loc, methods in self.graph.locator_to_methods.items():
                        if loc in stored_loc or stored_loc in loc:
                            for fq in methods:
                                if fq not in starting_fq:
                                    starting_fq[fq] = f"LOCATOR:{loc}"

        impacted_tests: List[ImpactedTest] = []
        all_impacted: Set[str] = set()
        seen_test_paths: Set[Tuple] = set()

        for start_fq, change_root in starting_fq.items():
            tests_found = self._bfs_reverse(start_fq, change_root)
            for it in tests_found:
                path_key = (it.test_method.full_qualified, it.change_root)
                if path_key not in seen_test_paths:
                    seen_test_paths.add(path_key)
                    impacted_tests.append(it)
                all_impacted.update(it.call_path)
            all_impacted.update(self._get_all_ancestors(start_fq))
            all_impacted.add(start_fq)

        return ImpactReport(changed_methods=changed_methods, changed_locators=changed_locators, impacted_tests=impacted_tests, all_impacted_fq=all_impacted, scoped_locator_changes=list(changed_scoped_locators or []))

    def _bfs_reverse(self, start_fq: str, change_root: str) -> List[ImpactedTest]:
        results = []
        queue = deque([(start_fq, [start_fq])])
        visited = {start_fq}
        while queue:
            current_fq, path = queue.popleft()
            current_method = self.graph.method_map_fq.get(current_fq)
            if current_method and current_method.is_test:
                results.append(ImpactedTest(test_method=current_method, call_path=list(reversed(path)), change_root=change_root))
            callers = self.graph.reverse.get(current_fq, set())
            for caller_fq in callers:
                if caller_fq not in visited:
                    visited.add(caller_fq)
                    queue.append((caller_fq, path + [caller_fq]))
        return results

    def _get_all_ancestors(self, start_fq: str) -> Set[str]:
        visited = set()
        queue = deque([start_fq])
        while queue:
            curr = queue.popleft()
            for caller in self.graph.reverse.get(curr, set()):
                if caller not in visited:
                    visited.add(caller)
                    queue.append(caller)
        return visited

    def _resolve_method(self, method_ref: str) -> List[str]:
        method_ref = method_ref.replace('.', '#', 1) if '#' not in method_ref and '.' in method_ref else method_ref
        if '#' in method_ref:
            if method_ref in self.graph.method_map_fq:
                return [method_ref]
            results = []
            parts = method_ref.split('#')
            class_hint, method_hint = parts[0], parts[1]
            for fq, m in self.graph.method_map_fq.items():
                if m.method_name == method_hint and class_hint.lower() in m.class_name.lower():
                    results.append(fq)
            return results
        else:
            matches = self.graph.method_map_short.get(method_ref, [])
            return [m.full_qualified for m in matches]
