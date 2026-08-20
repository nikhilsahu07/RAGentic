from __future__ import annotations

import ast
import operator
from datetime import datetime, timezone


# Safe arithmetic operator map — no eval(), no exec()
_SAFE_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
    ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv,
}


def _safe_eval(node: ast.AST) -> float:
    """Recursively evaluate an AST node with a restricted operator set."""
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return float(node.value)
        raise ValueError(f"Unsupported constant type: {type(node.value)}")
    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in _SAFE_OPS:
            raise ValueError(f"Unsupported operator: {op_type.__name__}")
        left = _safe_eval(node.left)
        right = _safe_eval(node.right)
        return _SAFE_OPS[op_type](left, right)
    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in _SAFE_OPS:
            raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
        return _SAFE_OPS[op_type](_safe_eval(node.operand))
    raise ValueError(f"Unsupported node type: {type(node).__name__}")


def calculator(expression: str) -> str:
    """Safely evaluate an arithmetic expression.

    Uses AST parsing — no eval(), no exec(). Supports +, -, *, /, **, %, //.
    """
    try:
        tree = ast.parse(expression.strip(), mode="eval")
        result = _safe_eval(tree.body)
        # Format cleanly: strip trailing .0 for integer results
        if result == int(result):
            return str(int(result))
        return f"{result:.6g}"
    except ZeroDivisionError:
        return "Error: division by zero"
    except Exception as exc:
        return f"Error: {exc}"


def current_date() -> str:
    """Return the current UTC date and time as a human-readable string."""
    now = datetime.now(tz=timezone.utc)
    return f"Today is {now.strftime('%A, %B %d, %Y')} (UTC {now.strftime('%H:%M')})."


TOOL_REGISTRY: dict[str, callable] = {
    "calculator": calculator,
    "date": current_date,
}


def dispatch_tool(tool_name: str, query: str) -> str:
    """Dispatch to the named tool, extracting arguments from the query if needed."""
    if tool_name == "calculator":
        # Extract the math expression from the query (best-effort)
        # Try to find content after common phrases
        for prefix in ["calculate", "compute", "what is", "eval", "="]:
            lower = query.lower()
            if prefix in lower:
                expression = query[lower.index(prefix) + len(prefix):].strip(" ?:")
                return calculator(expression)
        # Fallback: treat whole query as expression
        return calculator(query)
    if tool_name == "date":
        return current_date()
    return f"Unknown tool: {tool_name}"
