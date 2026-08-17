"""Target-time formulas for pool exercises.

A tiny, safe arithmetic mini-language over `pb` — the athlete's latest lactic-acid-test
personal best, in seconds. Only numbers, the single name `pb`, `+ - * /`, unary `+`/`-`
and parentheses are allowed (e.g. "pb + 2", "pb * 2 + 1"). Formulas are parsed with the
`ast` module and validated by walking the tree; they are never `eval`-ed. Evaluation is
normally done client-side for display, but `evaluate_formula` mirrors the same grammar
for tests / any server-side use.
"""

import ast

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
    """Raise ValueError if the tree contains anything outside the allowed grammar."""
    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED_NODES):
            raise ValueError(f"disallowed expression: {type(node).__name__}")
        if isinstance(node, ast.Name) and node.id != "pb":
            raise ValueError(f"unknown name: {node.id!r}")
        if isinstance(node, ast.Constant) and (
            isinstance(node.value, bool) or not isinstance(node.value, int | float)
        ):
            raise ValueError("only numeric literals are allowed")


def is_valid_formula(formula: str) -> bool:
    """Whether `formula` is a well-formed arithmetic expression over `pb`."""
    try:
        _check(ast.parse(formula, mode="eval"))
    except (SyntaxError, ValueError):
        return False
    return True


def evaluate_formula(formula: str, pb: float) -> float:
    """Evaluate a validated formula with `pb` bound to the given value."""
    tree = ast.parse(formula, mode="eval")
    _check(tree)
    return _eval_node(tree.body, pb)


def _eval_node(node: ast.AST, pb: float) -> float:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, int | float) and not isinstance(node.value, bool):
            return float(node.value)
        raise ValueError("non-numeric constant")  # pragma: no cover — _check rejects these
    if isinstance(node, ast.Name):  # only `pb` survives _check
        return pb
    if isinstance(node, ast.UnaryOp):
        value = _eval_node(node.operand, pb)
        return +value if isinstance(node.op, ast.UAdd) else -value
    if isinstance(node, ast.BinOp):
        left = _eval_node(node.left, pb)
        right = _eval_node(node.right, pb)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            return left / right
    raise ValueError(f"unexpected node: {type(node).__name__}")  # pragma: no cover
