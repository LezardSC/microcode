import ast
import operator

def evaluate_ast(node):
    allowed_operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.Mod: operator.mod,
        ast.FloorDiv: operator.floordiv,
    }

    # Check if number
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    
    # check if negative number
    elif isinstance(node, ast.UnaryOp):
        if type(node.op) in allowed_operators:
            return allowed_operators[type(node.op)](evaluate_ast(node.operand))
    
    # check if operation
    elif isinstance(node, ast.BinOp):
        if type(node.op) in allowed_operators:
            left = evaluate_ast(node.left)
            right = evaluate_ast(node.right)

            if isinstance(node.op, ast.Pow) and right > 1000:
                raise ValueError("exponant too large.")
            
            return allowed_operators[type(node.op)](left, right)
    
    raise ValueError(f"Unauthorized element: {type(node).__name__}")
