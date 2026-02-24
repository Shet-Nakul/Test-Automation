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

    # Raw xpath/css string → methods that use it inline (in method body directly)
    locator_to_methods: Dict[str, Set[str]] = field(default_factory=lambda: defaultdict(set))
    # ClassName#fieldName → methods that reference that field
    # Key: "AdminPage#addBtn"  Value: {"AdminPage#clickAddBtn", ...}
    # This is used for SCOPED locator lookup - avoids cross-class false positives
    scoped_field_to_methods: Dict[str, Set[str]] = field(default_factory=lambda: defaultdict(set))
    # ClassName → {fieldName → xpathValue}  (for reverse lookup)
    class_field_map: Dict[str, Dict[str, str]] = field(default_factory=lambda: defaultdict(dict))

    # All @Test methods
    test_methods: List[MethodInfo] = field(default_factory=list)


# ──────────────────────────────────────────────
# Builder
# ──────────────────────────────────────────────

class CallGraphBuilder:

    def build(self, parsed_files: List[ParsedFile]) -> CallGraph:
        graph = CallGraph()

        # ── Phase 0: build class-level field maps ───────────────────────────
        for pf in parsed_files:
            if hasattr(pf, 'class_level_locators'):
                graph.class_field_map[pf.class_name] = pf.class_level_locators
            if hasattr(pf, 'class_field_types'):
                # Store varName → ClassName for this class
                # e.g. AdminTests: {"adminPage": "AdminPage", "pimPage": "PIMPage"}
                graph.class_field_map[f"__types__{pf.class_name}"] = pf.class_field_types

        # ── Phase 1: register all methods ──────────────────────
        for pf in parsed_files:
            for method in pf.methods:
                graph.method_map_fq[method.full_qualified] = method
                graph.method_map_short[method.method_name].append(method)
                if method.is_test:
                    graph.test_methods.append(method)

                # Register inline locators (xpath strings directly in method body)
                for loc in method.locators:
                    graph.locator_to_methods[loc].add(method.full_qualified)

                # Register SCOPED field-name → method mapping
                # Key: "ClassName#fieldName" so we know WHICH class's field was changed
                for field_name in method.locator_fields_used:
                    scoped_key = f"{method.class_name}#{field_name}"
                    graph.scoped_field_to_methods[scoped_key].add(method.full_qualified)

        # ── Phase 2: build forward edges & reverse edges ────────────────────
        for pf in parsed_files:
            # Get the field type map for THIS class: varName → TypeName
            field_types = graph.class_field_map.get(f"__types__{pf.class_name}", {})

            for method in pf.methods:
                caller_fq = method.full_qualified
                resolved_callees: Set[str] = set()

                # ── Typed call resolution (precise): "varName.methodName()" ──
                # Resolves to the specific class of the variable, not all classes.
                # e.g. "adminPage.clickAdd()" → AdminPage#clickAdd only (not PIMPage#clickAdd)
                for var_name, method_names in method.typed_calls.items():
                    target_class = field_types.get(var_name)
                    if target_class:
                        for mn in method_names:
                            candidate_fq = f"{target_class}#{mn}"
                            if candidate_fq in graph.method_map_fq:
                                resolved_callees.add(candidate_fq)

                # ── Untyped call resolution (fallback): plain "methodName()" ──
                # For calls without an object prefix, or where the type isn't known.
                # Prefer same-class methods to reduce cross-class noise.
                for called_name in method.calls:
                    # Skip if already resolved via typed path
                    already_resolved = any(fq.endswith(f"#{called_name}") for fq in resolved_callees)
                    if already_resolved:
                        continue

                    # First try: same class (self-calls like helper methods)
                    same_class_fq = f"{pf.class_name}#{called_name}"
                    if same_class_fq in graph.method_map_fq:
                        resolved_callees.add(same_class_fq)
                    else:
                        # Fallback: any class that has this method name
                        for callee in graph.method_map_short.get(called_name, []):
                            resolved_callees.add(callee.full_qualified)

                # Build edges
                for callee_fq in resolved_callees:
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
        changed_methods: List[str],
        changed_locators: List[str],
        changed_scoped_locators: Optional[List[tuple]] = None,
    ) -> ImpactReport:
        """
        Entry point: given changed methods and/or locators,
        return all impacted @Test cases with their call paths.

        changed_scoped_locators = list of (class_name, field_name, xpath_value)
        This is the precise input from git diff — it knows WHICH class's field changed.
        Using this avoids false positives from other classes that share the same xpath.
        """
        starting_fq: Dict[str, str] = {}

        # ── Resolve changed method names ────────────────────────────────────
        for cm in changed_methods:
            resolved = self._resolve_method(cm)
            for fq in resolved:
                starting_fq[fq] = cm

        # ── Resolve SCOPED locator changes (precise - no cross-class pollution) ──
        # Input: (class_name, field_name, xpath_value) tuples from git diff
        # Lookup: "ClassName#fieldName" → only methods in THAT class using THAT field
        for class_name, field_name, xpath_value in (changed_scoped_locators or []):
            scoped_key = f"{class_name}#{field_name}"
            label = f"LOCATOR:{field_name} ({class_name})"

            if scoped_key in self.graph.scoped_field_to_methods:
                for fq in self.graph.scoped_field_to_methods[scoped_key]:
                    starting_fq[fq] = label
            else:
                # Fallback: restrict xpath match to same class only
                for fq, method in self.graph.method_map_fq.items():
                    if method.class_name == class_name and xpath_value in method.locators:
                        starting_fq[fq] = label

        # ── Resolve raw xpath/css strings (CLI --locators flag only) ─────────
        # IMPORTANT: If scoped locator changes were provided, the raw locator list
        # will contain both old AND new xpath values from the diff (from - and + lines).
        # These raw values must NOT be used when scoped info already covers that class —
        # otherwise they match identically-named xpaths in OTHER classes (false positives).
        #
        # Rule: skip raw lookup entirely if scoped changes were provided.
        # Raw lookup is only the fallback for CLI --locators flag usage.
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
