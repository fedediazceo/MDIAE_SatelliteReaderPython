"""
Safe math expression parser and evaluator for calibration expressions.
- Supports basic arithmetic, math functions and the actual value 'raw'.
- Uses Python's ast module to parse and validate expressions before evaluation.

Note: It's a bit overkill for the current sat work requested, but I kinda got carried away and kept adding features...
"""

import ast
import math

_ALLOWED_NODES = (
    ast.Expression, ast.BinOp, ast.UnaryOp, ast.Compare, ast.Constant,
    ast.Name, ast.Load, ast.operator, ast.unaryop, ast.boolop, ast.BoolOp,
    ast.IfExp, ast.Call, ast.Attribute
)
_ALLOWED_BINOPS = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow)
_ALLOWED_UNARYOPS = (ast.UAdd, ast.USub)
_ALLOWED_CMPOPS = (ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE)
_ALLOWED_NAMES = {"raw"}  
_ALLOWED_FUNCS = {
    # Somewhat extensive set of math functions, simplified to bare names, for simpler usage in the XML
    "sin": math.sin, "cos": math.cos, "tan": math.tan, "asin": math.asin, "acos": math.acos, "atan": math.atan,
    "sqrt": math.sqrt, "log": math.log, "log10": math.log10, "exp": math.exp, "fabs": math.fabs, "floor": math.floor,
    "ceil": math.ceil, "round": round, "min": min, "max": max, "pow": pow, "abs": abs
}

def _ensure_safe_expr(node: ast.AST) -> None:
    """
    Recursively ensure that the AST node only contains allowed elements.
    Raises ValueError if a disallowed element is found.
    """
    if not isinstance(node, _ALLOWED_NODES):
        raise ValueError(f"[EXPR PARSE ERROR] Disallowed expression element: {type(node).__name__}")
    for child in ast.iter_child_nodes(node):
        _ensure_safe_expr(child)

    # Additional checks for specific node types
    if isinstance(node, ast.BinOp) and not isinstance(node.op, _ALLOWED_BINOPS):
        raise ValueError(f"[EXPR PARSE ERROR] Disallowed binary operator: {type(node.op).__name__}")
    if isinstance(node, ast.UnaryOp) and not isinstance(node.op, _ALLOWED_UNARYOPS):
        raise ValueError(f"[EXPR PARSE ERROR] Disallowed unary operator: {type(node.op).__name__}")
    if isinstance(node, ast.Compare):
        for op in node.ops:
            if not isinstance(op, _ALLOWED_CMPOPS):
                raise ValueError(f"[EXPR PARSE ERROR] Disallowed comparison operator: {type(op).__name__}")
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name):
            if node.func.id not in _ALLOWED_FUNCS:
                raise ValueError(f"[EXPR PARSE ERROR] Function '{node.func.id}' not allowed.")
        elif isinstance(node.func, ast.Attribute):
            if not (isinstance(node.func.value, ast.Name) and node.func.value.id == "math" and node.func.attr in dir(math)):
                raise ValueError("[EXPR PARSE ERROR] Only math.<func> calls are allowed.")
        else:
            raise ValueError("[EXPR PARSE ERROR] Only simple function calls are allowed.")

    if isinstance(node, ast.Name) and node.id not in _ALLOWED_NAMES and node.id != "math":
        raise ValueError(f"[EXPR PARSE ERROR] Unknown variable '{node.id}'. Allowed: {sorted(_ALLOWED_NAMES)}")

def eval_expr(expr: str, *, raw: float) -> float:
    """
    Evaluate a safe math expression using the variable 'raw'
    Returns a float result.
    """
    try:
        parsed = ast.parse(expr, mode="eval")
        _ensure_safe_expr(parsed)
        compiled = compile(parsed, "<calibration>", "eval")
        env = {"__builtins__": {},
               "raw": raw,
               "math": math,
               **_ALLOWED_FUNCS}
        return float(eval(compiled, env, {}))
    except Exception as e:
        raise ValueError(f"[EXPR PARSE ERROR] Error evaluating expr '{expr}': {e}") from e