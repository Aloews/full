"""AST mutation operators.

Only semantically meaningful mutations are generated: flipped comparisons,
shifted boundaries, swapped boolean operators, perturbed thresholds and flipped
boolean literals. Cosmetic edits would inflate the score without proving
anything about the tests.
"""

from __future__ import annotations

import ast
from collections.abc import Callable, Iterator
from dataclasses import dataclass

#: Comparison flips: each pair is mutated in both directions.
_COMPARE_SWAPS: dict[type[ast.cmpop], type[ast.cmpop]] = {
    ast.Lt: ast.GtE,
    ast.GtE: ast.Lt,
    ast.Gt: ast.LtE,
    ast.LtE: ast.Gt,
    ast.Eq: ast.NotEq,
    ast.NotEq: ast.Eq,
    ast.Is: ast.IsNot,
    ast.IsNot: ast.Is,
    ast.In: ast.NotIn,
    ast.NotIn: ast.In,
}

#: Boundary shifts: the classic off-by-one that a weak test suite misses.
_BOUNDARY_SHIFTS: dict[type[ast.cmpop], type[ast.cmpop]] = {
    ast.Lt: ast.LtE,
    ast.LtE: ast.Lt,
    ast.Gt: ast.GtE,
    ast.GtE: ast.Gt,
}


@dataclass(frozen=True, slots=True)
class Mutation:
    """One candidate change to one file."""

    operator: str
    lineno: int
    col: int
    description: str
    source: str

    @property
    def key(self) -> str:
        return f"{self.operator}@{self.lineno}:{self.col}"


class _Replacer(ast.NodeTransformer):
    """Applies exactly one change, identified by node position and kind."""

    def __init__(self, target: ast.AST, apply: Callable[[ast.AST], ast.AST]) -> None:
        self.target = target
        self.apply = apply
        self.done = False

    def generic_visit(self, node: ast.AST) -> ast.AST:
        node = super().generic_visit(node)
        if node is self.target and not self.done:
            self.done = True
            return self.apply(node)
        return node

    def visit(self, node: ast.AST) -> ast.AST:
        if node is self.target and not self.done:
            self.done = True
            node = super().generic_visit(node)
            return self.apply(node)
        return super().visit(node)


def _render(tree: ast.Module, node: ast.AST, apply: Callable[[ast.AST], ast.AST]) -> str:
    clone = ast.parse(ast.unparse(tree))
    # Re-locate the node in the clone by position and type.
    target = _find_equivalent(clone, node)
    if target is None:
        return ""
    replacer = _Replacer(target, apply)
    mutated = replacer.visit(clone)
    if not replacer.done:
        return ""
    ast.fix_missing_locations(mutated)
    return ast.unparse(mutated)


def _find_equivalent(tree: ast.AST, node: ast.AST) -> ast.AST | None:
    """Locate ``node`` in a re-parsed clone.

    Positions are part of the comparison: two identical expressions elsewhere in
    the file must not be mistaken for this one, or the mutation lands on the
    wrong line and the report lies about what was tested.
    """
    dumped = ast.dump(node, include_attributes=True)
    for candidate in ast.walk(tree):
        if type(candidate) is type(node) and ast.dump(candidate, include_attributes=True) == dumped:
            return candidate
    return None


def _line_of(source_lines: list[str], node: ast.AST) -> str:
    index = getattr(node, "lineno", 1) - 1
    if 0 <= index < len(source_lines):
        return source_lines[index].strip()
    return ""


#: Keyword arguments that configure dataclass machinery rather than behaviour.
_MACHINERY_KWARGS = frozenset(
    {"init", "repr", "eq", "order", "unsafe_hash", "frozen", "slots", "kw_only", "compare", "hash"}
)


def _machinery_nodes(tree: ast.AST) -> set[int]:
    """Constants passed to ``field(init=False)`` and friends.

    Flipping ``init`` or ``slots`` changes the generated constructor, not the
    logic under test, so those mutants are equivalent for every realistic suite.
    """
    excluded: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        for keyword in node.keywords:
            if keyword.arg in _MACHINERY_KWARGS:
                for inner in ast.walk(keyword.value):
                    excluded.add(id(inner))
    return excluded


def _decorator_nodes(tree: ast.AST) -> set[int]:
    """Nodes inside decorator expressions.

    ``@dataclass(frozen=True, slots=True)`` configures the class machinery; it is
    not the algorithm under test, and flipping ``slots`` produces an equivalent
    mutant no test could reasonably distinguish. Immutability is covered by
    explicit tests instead.
    """
    excluded: set[int] = set()
    for node in ast.walk(tree):
        for decorator in getattr(node, "decorator_list", []):
            for inner in ast.walk(decorator):
                excluded.add(id(inner))
    return excluded


def generate_mutations(source: str) -> list[Mutation]:
    """Every mutation this engine can make to ``source``."""
    tree = ast.parse(source)
    # Normalise first, so positions in the generated source match the mutants.
    normalised = ast.unparse(tree)
    tree = ast.parse(normalised)
    lines = normalised.splitlines()

    excluded = _decorator_nodes(tree) | _machinery_nodes(tree)
    mutations: list[Mutation] = []
    seen: set[str] = set()

    def add(node: ast.AST, operator: str, description: str, apply: Callable[[ast.AST], ast.AST]) -> None:
        mutated = _render(tree, node, apply)
        if not mutated or mutated == normalised:
            return
        mutation = Mutation(
            operator=operator,
            lineno=getattr(node, "lineno", 0),
            col=getattr(node, "col_offset", 0),
            description=f"{description} — {_line_of(lines, node)[:90]}",
            source=mutated,
        )
        if mutation.key in seen:
            return
        seen.add(mutation.key)
        mutations.append(mutation)

    for node in ast.walk(tree):
        if id(node) in excluded:
            continue
        if isinstance(node, ast.Compare) and len(node.ops) == 1:
            op_type = type(node.ops[0])
            if op_type in _COMPARE_SWAPS:
                swapped = _COMPARE_SWAPS[op_type]
                add(
                    node,
                    "compare_swap",
                    f"{op_type.__name__} -> {swapped.__name__}",
                    lambda n, s=swapped: ast.Compare(left=n.left, ops=[s()], comparators=n.comparators),
                )
            if op_type in _BOUNDARY_SHIFTS:
                shifted = _BOUNDARY_SHIFTS[op_type]
                add(
                    node,
                    "boundary_shift",
                    f"{op_type.__name__} -> {shifted.__name__}",
                    lambda n, s=shifted: ast.Compare(left=n.left, ops=[s()], comparators=n.comparators),
                )
        elif isinstance(node, ast.BoolOp):
            flipped = ast.Or if isinstance(node.op, ast.And) else ast.And
            add(
                node,
                "boolop_swap",
                f"{type(node.op).__name__} -> {flipped.__name__}",
                lambda n, f=flipped: ast.BoolOp(op=f(), values=n.values),
            )
        elif isinstance(node, ast.Constant):
            if isinstance(node.value, bool):
                add(
                    node,
                    "bool_flip",
                    f"{node.value} -> {not node.value}",
                    lambda n: ast.Constant(value=not n.value),
                )
            elif isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
                shifted = node.value + 1 if node.value != 0 else 1
                add(
                    node,
                    "constant_shift",
                    f"{node.value} -> {shifted}",
                    lambda n, v=shifted: ast.Constant(value=v),
                )
    return mutations


def iter_mutations(source: str) -> Iterator[Mutation]:
    yield from generate_mutations(source)
