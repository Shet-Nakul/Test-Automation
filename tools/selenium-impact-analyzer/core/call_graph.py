"""
Call Graph Builder
==================
Builds a complete call graph from parsed Java files and supports
reverse BFS traversal to find impacted @Test methods.

Graph model:
  - Node  : MethodInfo (identified by class_name#method_name)
  - Edge  : A → B means method A calls method B
  - Reverse graph: B → [A, ...] means B is called by A

Impact tracing:
  Starting from a changed node, traverse the REVERSE graph using BFS
  until @Test annotated methods are reached (or no more callers exist).
"""

from collections import defaultdict, deque
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field

from core.java_parser import ParsedFile, MethodInfo


# ──────────────────────────────────────────────
# Data structures
# ──────────────────────────────────────────────

@dataclass
class CallGraph:
    # method_name → MethodInfo (short name for fast lookup)
    method_map_short: Dict[str, List[MethodInfo]] = field(default_factory=lambda: defaultdict(list))
    # class#method → MethodInfo (fully qualified lookup)
    method_map_fq: Dict[str, MethodInfo] = field(default_factory=dict)

    # Forward graph: caller_fq → set of callee method names (short)
    forward: Dict[str, Set[str]] = field(default_factory=lambda: defaultdict(set))
    # Reverse graph: callee_fq → set of caller_fq
    reverse: Dict[str, Set[str]] = field(default_factory=lambda: defaultdict(set))

    # Locator string → set of method fq that use this locator
    locator_to_methods: Dict[str, Set[str]] = field(default_factory=lambda: defaultdict(set))

    # All @Test methods
    test_methods: List[MethodInfo] = field(default_factory=list)


# ──────────────────────────────────────────────
# Builder
# ──────────────────────────────────────────────

class CallGraphBuilder:

    def build(self, parsed_files: List[ParsedFile]) -> CallGraph:
        graph = CallGraph()

        # ── Phase 1: register all methods ──────────────────────
        for pf in parsed_files:
            for method in pf.methods:
                graph.method_map_fq[method.full_qualified] = method
                graph.method_map_short[method.method_name].append(method)
                if method.is_test:
                    graph.test_methods.append(method)

                # Register locators
                for loc in method.locators:
                    graph.locator_to_methods[loc].add(method.full_qualified)

        # ── Phase 2: build forward edges & reverse edges ────────
        for pf in parsed_files:
            for method in pf.methods:
                caller_fq = method.full_qualified
                for called_name in method.calls:
                    # Resolve called_name to full-qualified methods
                    callees = graph.method_map_short.get(called_name, [])
                    for callee in callees:
                        callee_fq = callee.full_qualified
                        graph.forward[caller_fq].add(callee_fq)
                        graph.reverse[callee_fq].add(caller_fq)

        return graph


# ──────────────────────────────────────────────
# Impact Analyzer
# ──────────────────────────────────────────────

@dataclass
class ImpactedTest:
    test_method: MethodInfo
    call_path: List[str]          # chain from changed node → test
    change_root: str              # what change triggered this


@dataclass
class ImpactReport:
    changed_methods: List[str]
    changed_locators: List[str]
    impacted_tests: List[ImpactedTest]
    all_impacted_fq: Set[str]     # all nodes in blast radius (not just tests)

    @property
    def unique_test_names(self) -> List[str]:
        seen = set()
        result = []
        for it in self.impacted_tests:
            key = it.test_method.full_qualified
            if key not in seen:
                seen.add(key)
                result.append(key)
        return result


class ImpactAnalyzer:

    def __init__(self, call_graph: CallGraph):
        self.graph = call_graph

    def analyze(
        self,
        changed_methods: List[str],          # list of method names or class#method
        changed_locators: List[str],          # list of xpath/css strings that changed
    ) -> ImpactReport:
        """
        Entry point: given changed methods and locators,
        return all impacted @Test cases with their call paths.
        """
        # Resolve changed method names → fq names
        starting_fq: Dict[str, str] = {}  # fq → change_root label

        for cm in changed_methods:
            resolved = self._resolve_method(cm)
            for fq in resolved:
                starting_fq[fq] = cm

        # Resolve changed locators → methods that use them
        for loc in changed_locators:
            # exact match
            if loc in self.graph.locator_to_methods:
                for fq in self.graph.locator_to_methods[loc]:
                    starting_fq[fq] = f"LOCATOR:{loc}"
            else:
                # partial match (locator might be substring)
                for stored_loc, methods in self.graph.locator_to_methods.items():
                    if loc in stored_loc or stored_loc in loc:
                        for fq in methods:
                            starting_fq[fq] = f"LOCATOR:{loc}"

        # BFS upward from each starting node
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

            # Also mark all nodes traversed
            all_impacted.update(self._get_all_ancestors(start_fq))
            all_impacted.add(start_fq)

        return ImpactReport(
            changed_methods=changed_methods,
            changed_locators=changed_locators,
            impacted_tests=impacted_tests,
            all_impacted_fq=all_impacted
        )

    def _bfs_reverse(self, start_fq: str, change_root: str) -> List[ImpactedTest]:
        """
        BFS on the REVERSE call graph.
        Returns ImpactedTest for every @Test reached.
        Tracks path for each route.
        """
        results = []
        # Queue items: (current_fq, path_so_far)
        queue = deque([(start_fq, [start_fq])])
        visited = {start_fq}

        while queue:
            current_fq, path = queue.popleft()

            current_method = self.graph.method_map_fq.get(current_fq)

            # Check if this node is a @Test
            if current_method and current_method.is_test:
                results.append(ImpactedTest(
                    test_method=current_method,
                    call_path=list(reversed(path)),  # root of change → test
                    change_root=change_root
                ))
                # Don't stop: there might be other @Test further up (rare but possible)

            # Traverse callers
            callers = self.graph.reverse.get(current_fq, set())
            for caller_fq in callers:
                if caller_fq not in visited:
                    visited.add(caller_fq)
                    queue.append((caller_fq, path + [caller_fq]))

        return results

    def _get_all_ancestors(self, start_fq: str) -> Set[str]:
        """Get all nodes that can reach start_fq going upward (callers)."""
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
        """
        Resolve a method reference to full-qualified names.
        Accepts:
          - 'methodName'            → looks up short name
          - 'ClassName#methodName'  → direct lookup
          - 'ClassName.methodName'  → normalized to #
        """
        # Normalize separator
        method_ref = method_ref.replace('.', '#', 1) if '#' not in method_ref and '.' in method_ref else method_ref

        if '#' in method_ref:
            if method_ref in self.graph.method_map_fq:
                return [method_ref]
            # partial class match
            results = []
            parts = method_ref.split('#')
            class_hint = parts[0]
            method_hint = parts[1]
            for fq, m in self.graph.method_map_fq.items():
                if m.method_name == method_hint and class_hint.lower() in m.class_name.lower():
                    results.append(fq)
            return results
        else:
            # short name lookup
            matches = self.graph.method_map_short.get(method_ref, [])
            return [m.full_qualified for m in matches]
