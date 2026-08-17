"""Target-time formulas for pool exercises.

A tiny, safe arithmetic mini-language over one test variable:

- `pb` — the athlete's latest lactic-acid-test personal best, in seconds
- `st` — the athlete's latest speed-test result, in seconds

Only numbers, exactly ONE of those variables, `+ - * /`, unary `+`/`-` and parentheses
are allowed (e.g. "pb + 2", "st * 2 + 1"). A formula references `pb` OR `st`, never both
and never neither. Formulas are parsed with the `ast` module and validated by walking the
tree; they are never `eval`-ed. Evaluation is normally done client-side for display, but
`evaluate_formula` mirrors the same grammar for tests / any server-side use.
"""

import ast
from typing import Literal

Variable = Literal["pb", "st"]
_VARIABLES: frozenset[str] = frozenset({"pb", "st"})

# Node types the grammar permits. Anything else (calls, attributes, comparisons,
# power `**`, etc.) makes the formula invalid.
_ALLOWED_NODES: tuple[type[ast.AST], ...] = (
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.USub,
    ast.UAdd,
    ast.Constant,
    ast.Name,
    ast.Load,
)


def _check(tree: ast.AST) -> None:
    """Raise ValueError if the tree contains anything outside the allowed grammar
    (node types, known variable names, numeric literals)."""
    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED_NODES):
            raise ValueError(f"disallowed expression: {type(node).__name__}")
        if isinstance(node, ast.Name) and node.id not in _VARIABLES:
            raise ValueError(f"unknown name: {node.id!r}")
        if isinstance(node, ast.Constant) and (
            isinstance(node.value, bool) or not isinstance(node.value, int | float)
        ):
            raise ValueError("only numeric literals are allowed")


def formula_variable(formula: str) -> Variable | None:
    """The single test variable a valid formula references (`pb` or `st`), or None if
    the formula is malformed or doesn't reference exactly one of them (e.g. references
    both, or none)."""
    try:
        tree = ast.parse(formula, mode="eval")
        _check(tree)
    except (SyntaxError, ValueError):
        return None
    names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    if len(names) != 1:
        return None
    (name,) = names
    return name  # type: ignore[return-value]  # _check guarantees name ∈ _VARIABLES


def is_valid_formula(formula: str) -> bool:
    """Whether `formula` is well-formed arithmetic referencing exactly one of pb/st."""
    return formula_variable(formula) is not None


def evaluate_formula(formula: str, value: float) -> float:
    """Evaluate a validated formula with its variable bound to `value`."""
    tree = ast.parse(formula, mode="eval")
    _check(tree)
    return _eval_node(tree.body, value)


def _eval_node(node: ast.AST, value: float) -> float:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, int | float) and not isinstance(node.value, bool):
            return float(node.value)
        raise ValueError("non-numeric constant")  # pragma: no cover — _check rejects these
    if isinstance(node, ast.Name):  # the single pb/st variable survives _check
        return value
    if isinstance(node, ast.UnaryOp):
        operand = _eval_node(node.operand, value)
        return +operand if isinstance(node.op, ast.UAdd) else -operand
    if isinstance(node, ast.BinOp):
        left = _eval_node(node.left, value)
        right = _eval_node(node.right, value)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            return left / right
    raise ValueError(f"unexpected node: {type(node).__name__}")  # pragma: no cover
