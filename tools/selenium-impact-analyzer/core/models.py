from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple

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
    locator_fields_used: Set[str] = field(default_factory=set)  # class-level field names referenced
    typed_calls: Dict[str, Set[str]] = field(default_factory=dict)

@dataclass
class ParsedFile:
    file_path: str
    class_name: str
    package: str
    imports: List[str]
    methods: List[MethodInfo]
    raw_source: str
    class_level_locators: Dict[str, str] = field(default_factory=dict)
    class_field_types: Dict[str, str] = field(default_factory=dict)

@dataclass
class ImpactedTest:
    test_method: MethodInfo
    call_path: List[str]
    change_root: str

@dataclass
class ImpactReport:
    changed_methods: List[str]
    changed_locators: List[str]
    impacted_tests: List[ImpactedTest]
    all_impacted_fq: Set[str]
    scoped_locator_changes: List[tuple] = field(default_factory=list)

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
