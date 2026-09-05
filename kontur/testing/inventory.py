"""Static inventory of the test suite.

The meta-tests need to answer questions *about the tests themselves*: does every
critical rule have a negative test, does every test actually assert something,
is any test skipped without a reason. Answering those by importing the suite
would be circular, so the inventory reads the test files with :mod:`ast`.

Markers are the contract between a test and the governance layer:

    @pytest.mark.rule("FACET-004")   links a test to a rule in the registry
    @pytest.mark.positive            the rule must fire on this input
    @pytest.mark.negative            the rule must NOT fire / must raise
    @pytest.mark.regression          locks in behaviour that must not drift
    @pytest.mark.boundary            exercises a scoring function's edges
    @pytest.mark.scoring("name")     links a test to a scoring function
    @pytest.mark.endpoint("/path")   links a test to an API route
"""

from __future__ import annotations

import ast
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

#: Fixtures pytest provides out of the box.
BUILTIN_FIXTURES: frozenset[str] = frozenset(
    {
        "request", "tmp_path", "tmp_path_factory", "tmpdir", "tmpdir_factory", "monkeypatch",
        "capsys", "capsysbinary", "capfd", "capfdbinary", "caplog", "recwarn", "pytestconfig",
        "record_property", "record_testsuite_property", "cache", "doctest_namespace", "testdir",
        "pytester", "subtests", "event_loop", "anyio_backend",
    }
)

_ASSERT_HELPER_PREFIXES = ("assert_", "verify_", "expect_")
_RAISES_CALLS = {"raises", "warns", "deprecated_call", "fail", "xfail"}


def _decorator_parts(node: ast.expr) -> tuple[str, list[Any], dict[str, Any]]:
    """Return (dotted name, positional args, keyword args) for a decorator."""
    args: list[Any] = []
    kwargs: dict[str, Any] = {}
    target = node
    if isinstance(node, ast.Call):
        target = node.func
        for argument in node.args:
            args.append(_literal(argument))
        for keyword in node.keywords:
            if keyword.arg:
                kwargs[keyword.arg] = _literal(keyword.value)
    parts: list[str] = []
    while isinstance(target, ast.Attribute):
        parts.append(target.attr)
        target = target.value
    if isinstance(target, ast.Name):
        parts.append(target.id)
    return ".".join(reversed(parts)), args, kwargs


def _literal(node: ast.expr) -> Any:
    try:
        return ast.literal_eval(node)
    except (ValueError, SyntaxError):
        return ast.dump(node)


def _is_tautology(node: ast.Assert) -> bool:
    """Detect asserts that can never fail (`assert True`, `assert 1 == 1`, ...)."""
    test = node.test
    if isinstance(test, ast.Constant):
        return bool(test.value)
    if isinstance(test, ast.Compare) and len(test.ops) == 1:
        left, right = test.left, test.comparators[0]
        if isinstance(left, ast.Constant) and isinstance(right, ast.Constant):
            return True
        if ast.dump(left) == ast.dump(right) and isinstance(test.ops[0], (ast.Eq, ast.Is)):
            return True
    return False


@dataclass(frozen=True, slots=True)
class TestCase:
    """One test function, as seen statically."""

    #: These are inventory records, not pytest test classes.
    __test__ = False

    name: str
    path: str
    line: int
    markers: tuple[str, ...] = ()
    rule_ids: tuple[str, ...] = ()
    scoring: tuple[str, ...] = ()
    endpoints: tuple[str, ...] = ()
    fixtures: tuple[str, ...] = ()
    assertions: int = 0
    tautological_assertions: int = 0
    skip_markers: tuple[tuple[str, str], ...] = ()
    body_skip_calls: int = 0

    @property
    def has_assertion(self) -> bool:
        return self.assertions > 0

    @property
    def is_positive(self) -> bool:
        return "positive" in self.markers

    @property
    def is_negative(self) -> bool:
        return "negative" in self.markers

    @property
    def is_regression(self) -> bool:
        return "regression" in self.markers

    @property
    def is_boundary(self) -> bool:
        return "boundary" in self.markers

    @property
    def is_skipped(self) -> bool:
        return bool(self.skip_markers)

    @property
    def unexplained_skips(self) -> tuple[str, ...]:
        return tuple(marker for marker, reason in self.skip_markers if not reason.strip())

    @property
    def node_id(self) -> str:
        return f"{self.path}::{self.name}"


@dataclass(frozen=True, slots=True)
class TestModule:
    """One parsed test module."""

    __test__ = False

    path: str
    tests: tuple[TestCase, ...]
    fixtures: frozenset[str] = frozenset()
    imports_pytest: bool = True


@dataclass(frozen=True, slots=True)
class TestInventory:
    """Everything the meta-tests need to know about the suite."""

    __test__ = False

    root: str
    modules: tuple[TestModule, ...] = ()
    conftest_fixtures: frozenset[str] = frozenset()
    collection_errors: tuple[str, ...] = field(default_factory=tuple)

    # ------------------------------------------------------------------ views
    @property
    def tests(self) -> tuple[TestCase, ...]:
        return tuple(test for module in self.modules for test in module.tests)

    def __len__(self) -> int:
        return len(self.tests)

    def with_marker(self, marker: str) -> tuple[TestCase, ...]:
        return tuple(t for t in self.tests if marker in t.markers)

    def for_rule(self, rule_id: str) -> tuple[TestCase, ...]:
        return tuple(t for t in self.tests if rule_id in t.rule_ids)

    def positive_tests_for(self, rule_id: str) -> tuple[TestCase, ...]:
        return tuple(t for t in self.for_rule(rule_id) if t.is_positive)

    def negative_tests_for(self, rule_id: str) -> tuple[TestCase, ...]:
        return tuple(t for t in self.for_rule(rule_id) if t.is_negative)

    def regression_tests_for(self, rule_id: str) -> tuple[TestCase, ...]:
        return tuple(t for t in self.for_rule(rule_id) if t.is_regression)

    def boundary_tests_for(self, scoring_name: str) -> tuple[TestCase, ...]:
        return tuple(t for t in self.tests if scoring_name in t.scoring and t.is_boundary)

    def tests_for_endpoint(self, path: str) -> tuple[TestCase, ...]:
        return tuple(t for t in self.tests if path in t.endpoints)

    def covered_rules(self) -> frozenset[str]:
        return frozenset(rule for test in self.tests for rule in test.rule_ids)

    def without_assertions(self) -> tuple[TestCase, ...]:
        return tuple(t for t in self.tests if not t.has_assertion and not t.is_skipped)

    def tautological(self) -> tuple[TestCase, ...]:
        return tuple(
            t for t in self.tests if t.tautological_assertions > 0 and t.assertions == t.tautological_assertions
        )

    def unexplained_skips(self) -> tuple[TestCase, ...]:
        return tuple(t for t in self.tests if t.unexplained_skips)

    def known_fixtures(self) -> frozenset[str]:
        module_fixtures = frozenset(f for m in self.modules for f in m.fixtures)
        return BUILTIN_FIXTURES | self.conftest_fixtures | module_fixtures

    def missing_fixtures(self) -> dict[str, tuple[str, ...]]:
        """Fixtures a test asks for that nothing defines."""
        known = self.known_fixtures()
        missing: dict[str, tuple[str, ...]] = {}
        for test in self.tests:
            unknown = tuple(f for f in test.fixtures if f not in known)
            if unknown:
                missing[test.node_id] = unknown
        return missing

    def summary(self) -> dict[str, int]:
        return {
            "tests": len(self.tests),
            "modules": len(self.modules),
            "positive": len(self.with_marker("positive")),
            "negative": len(self.with_marker("negative")),
            "regression": len(self.with_marker("regression")),
            "boundary": len(self.with_marker("boundary")),
            "meta": len(self.with_marker("meta")),
            "security": len(self.with_marker("security")),
            "rules_covered": len(self.covered_rules()),
        }


class _ModuleVisitor:
    """Extracts tests and fixtures from a single parsed module."""

    def __init__(self, path: Path, root: Path) -> None:
        self.path = path
        self.relative = str(path.relative_to(root.parent)) if root.parent in path.parents else str(path)
        self.tests: list[TestCase] = []
        self.fixtures: set[str] = set()
        self.module_markers: tuple[str, ...] = ()

    def visit(self, tree: ast.Module) -> None:
        self.module_markers = _module_markers(tree)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._visit_function(node)

    def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        markers: list[str] = list(self.module_markers)
        rule_ids: list[str] = []
        scoring: list[str] = []
        endpoints: list[str] = []
        skip_markers: list[tuple[str, str]] = []
        parametrized: set[str] = set()
        is_fixture = False

        for decorator in node.decorator_list:
            name, args, kwargs = _decorator_parts(decorator)
            if name.endswith("fixture") and ("pytest" in name or name == "fixture"):
                is_fixture = True
            if ".mark." not in f".{name}.":
                continue
            marker = name.split("mark.", 1)[1] if "mark." in name else name
            markers.append(marker)
            if marker == "rule":
                rule_ids.extend(str(a) for a in args)
            elif marker == "scoring":
                scoring.extend(str(a) for a in args)
            elif marker == "endpoint":
                endpoints.extend(str(a) for a in args)
            elif marker in ("skip", "skipif", "xfail"):
                skip_markers.append((marker, str(kwargs.get("reason", ""))))
            elif marker == "parametrize" and args:
                names = args[0]
                if isinstance(names, str):
                    parametrized.update(n.strip() for n in names.split(","))
                elif isinstance(names, (tuple, list)):
                    parametrized.update(str(n).strip() for n in names)

        if is_fixture:
            self.fixtures.add(node.name)
            return
        if not node.name.startswith("test_"):
            return

        assertions = 0
        tautologies = 0
        body_skips = 0
        for child in ast.walk(node):
            if isinstance(child, ast.Assert):
                assertions += 1
                if _is_tautology(child):
                    tautologies += 1
            elif isinstance(child, ast.Call):
                call_name, _, _ = _decorator_parts(child)
                tail = call_name.rsplit(".", 1)[-1]
                if tail in _RAISES_CALLS:
                    assertions += 1
                elif tail.startswith(_ASSERT_HELPER_PREFIXES):
                    assertions += 1
                if tail == "skip":
                    body_skips += 1

        fixtures = tuple(
            arg.arg
            for arg in node.args.args
            if arg.arg not in ("self", "cls") and arg.arg not in parametrized
        )

        self.tests.append(
            TestCase(
                name=node.name,
                path=self.relative,
                line=node.lineno,
                markers=tuple(markers),
                rule_ids=tuple(rule_ids),
                scoring=tuple(scoring),
                endpoints=tuple(endpoints),
                fixtures=fixtures,
                assertions=assertions,
                tautological_assertions=tautologies,
                skip_markers=tuple(skip_markers),
                body_skip_calls=body_skips,
            )
        )


def _marker_name(node: ast.expr) -> str | None:
    """Extract ``x`` from ``pytest.mark.x`` / ``pytest.mark.x(...)``."""
    name, _, _ = _decorator_parts(node)
    return name.split("mark.", 1)[1] if "mark." in name else None


def _module_markers(tree: ast.Module) -> tuple[str, ...]:
    """Markers applied to a whole module via ``pytestmark = ...``."""
    found: list[str] = []
    for node in tree.body:
        targets: list[ast.expr] = []
        value: ast.expr | None = None
        if isinstance(node, ast.Assign):
            targets = list(node.targets)
            value = node.value
        elif isinstance(node, ast.AnnAssign) and node.target is not None:
            targets = [node.target]
            value = node.value
        if value is None:
            continue
        if not any(isinstance(t, ast.Name) and t.id == "pytestmark" for t in targets):
            continue
        candidates = value.elts if isinstance(value, (ast.List, ast.Tuple)) else [value]
        for candidate in candidates:
            marker = _marker_name(candidate)
            if marker and marker not in found:
                found.append(marker)
    return tuple(found)


def _iter_test_files(root: Path) -> Iterator[Path]:
    for path in sorted(root.rglob("*.py")):
        if any(part in {"__pycache__", ".pytest_cache"} for part in path.parts):
            continue
        yield path


def build_inventory(root: str | Path = "tests") -> TestInventory:
    """Parse every test module under ``root``."""
    root_path = Path(root).resolve()
    if not root_path.exists():
        return TestInventory(root=str(root_path), collection_errors=(f"missing test root: {root_path}",))

    modules: list[TestModule] = []
    conftest_fixtures: set[str] = set()
    errors: list[str] = []

    for path in _iter_test_files(root_path):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            errors.append(f"{path}: {exc}")
            continue

        visitor = _ModuleVisitor(path, root_path)
        visitor.visit(tree)

        if path.name == "conftest.py":
            conftest_fixtures.update(visitor.fixtures)
            continue
        if not path.name.startswith("test_"):
            # Support modules (helpers, sabotage fixtures) contribute fixtures only.
            conftest_fixtures.update(visitor.fixtures)
            continue

        modules.append(
            TestModule(
                path=visitor.relative,
                tests=tuple(visitor.tests),
                fixtures=frozenset(visitor.fixtures),
            )
        )

    return TestInventory(
        root=str(root_path),
        modules=tuple(modules),
        conftest_fixtures=frozenset(conftest_fixtures),
        collection_errors=tuple(errors),
    )


@lru_cache(maxsize=4)
def cached_inventory(root: str = "tests") -> TestInventory:
    return build_inventory(root)


def describe(inventory: TestInventory) -> str:
    lines = [f"{inventory.root}: {len(inventory)} tests in {len(inventory.modules)} modules"]
    for key, value in inventory.summary().items():
        lines.append(f"  {key:16s} {value}")
    return "\n".join(lines)


def find_repo_root(start: Path | None = None) -> Path:
    """Walk up until a directory containing pyproject.toml is found."""
    current = (start or Path(__file__)).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "pyproject.toml").exists():
            return candidate
    return Path.cwd()


def iter_source_files(package_root: Path) -> Iterable[Path]:
    for path in sorted(package_root.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        yield path
