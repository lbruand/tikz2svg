"""Mathematical expression evaluator for TikZ."""

import math
import re
from typing import Any, Optional

from .context import EvaluationContext


class MathEvaluator:
    """Evaluates mathematical expressions in TikZ code."""

    # Map LaTeX math functions to Python math functions
    FUNCTION_MAP = {
        "sqrt": "math.sqrt",
        "sin": "math.sin",
        "cos": "math.cos",
        "tan": "math.tan",
        "abs": "abs",
        "exp": "math.exp",
        "ln": "math.log",
        "log": "math.log10",
        "floor": "math.floor",
        "ceil": "math.ceil",
        "round": "round",
    }

    def __init__(self, context: Optional[EvaluationContext] = None):
        """
        Initialize math evaluator.

        Args:
            context: Evaluation context for variables
        """
        self.context = context or EvaluationContext()

    def evaluate(self, expr: str) -> float:
        """
        Evaluate a mathematical expression.

        Args:
            expr: Expression string

        Returns:
            Evaluated result as float

        Raises:
            ValueError: If expression cannot be evaluated
        """
        if not expr:
            return 0.0

        # Convert to string if not already
        expr = str(expr).strip()

        # If it's already a number, return it
        try:
            return float(expr)
        except ValueError:
            pass

        # Process the expression
        processed = self._process_expression(expr)

        # Evaluate safely
        try:
            result = self._safe_eval(processed)
            return float(result)
        except Exception as e:
            raise ValueError(f"Failed to evaluate expression '{expr}': {e}") from e

    def _process_expression(self, expr: str) -> str:
        """
        Process expression by replacing variables and functions.

        Args:
            expr: Raw expression

        Returns:
            Processed expression ready for eval
        """
        # Replace variables with their values
        expr = self._replace_variables(expr)

        # Replace LaTeX functions with Python equivalents
        expr = self._replace_functions(expr)

        # Convert degrees to radians for trig functions
        expr = self._handle_trig_degrees(expr)

        return expr

    def _replace_variables(self, expr: str) -> str:
        """
        Replace LaTeX variables (\var) with their values.

        Args:
            expr: Expression with variables

        Returns:
            Expression with variables replaced
        """
        # Find all variable references (\varname)
        var_pattern = r"\\([a-zA-Z_][a-zA-Z0-9_]*)"

        def replace_var(match):
            var_name = match.group(1)
            value = self.context.get_variable(var_name)

            if value is None:
                # Variable not found, keep as is (might be undefined)
                return match.group(0)

            # Convert value to string for substitution
            return str(value)

        return re.sub(var_pattern, replace_var, expr)

    def _replace_functions(self, expr: str) -> str:
        """
        Replace LaTeX function names with Python equivalents.

        Args:
            expr: Expression with LaTeX functions

        Returns:
            Expression with Python functions
        """
        for latex_func, python_func in self.FUNCTION_MAP.items():
            # Replace function calls: func(x) -> math.func(x)
            expr = re.sub(
                rf"\b{latex_func}\b",
                python_func,
                expr,
            )

        return expr

    def _handle_trig_degrees(self, expr: str) -> str:
        """
        Convert degree arguments to radians for trig functions.

        TikZ uses degrees by default for trig functions.

        Args:
            expr: Expression with trig functions

        Returns:
            Expression with degree-to-radian conversions
        """
        # Pattern to match trig functions with their arguments
        trig_pattern = r"math\.(sin|cos|tan)\s*\(([^)]+)\)"

        def convert_to_radians(match):
            func = match.group(1)
            arg = match.group(2)
            # Convert degrees to radians: radians = degrees * pi / 180
            return f"math.{func}(math.radians({arg}))"

        return re.sub(trig_pattern, convert_to_radians, expr)

    def _safe_eval(self, expr: str) -> Any:
        """
        Safely evaluate an expression.

        Args:
            expr: Processed expression

        Returns:
            Evaluation result

        Raises:
            ValueError: If evaluation fails
        """
        # Create a restricted namespace
        safe_namespace = {
            "__builtins__": {},
            "math": math,
            "abs": abs,
            "round": round,
            "min": min,
            "max": max,
        }

        # Add all variables from context
        safe_namespace.update(self.context.get_all_variables())

        try:
            result = eval(expr, safe_namespace)
            return result
        except Exception as e:
            raise ValueError(f"Evaluation error: {e}") from e

    def evaluate_coordinate_value(self, value: Any) -> float:
        """
        Evaluate a coordinate value (may be number or expression).

        Args:
            value: Coordinate value

        Returns:
            Evaluated float value
        """
        if isinstance(value, (int, float)):
            return float(value)

        if isinstance(value, str):
            return self.evaluate(value)

        return 0.0
