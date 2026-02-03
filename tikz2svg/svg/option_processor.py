"""Option processing for TikZ to SVG conversion."""

from typing import Any, Dict, Optional


class OptionProcessor:
    """Processes TikZ options, evaluating expressions and variables.

    Handles:
    - Expression evaluation in option values
    - Variable substitution
    - Safe fallback to original values
    """

    def __init__(self, evaluator):
        """Initialize option processor.

        Args:
            evaluator: MathEvaluator for expression evaluation
        """
        self.evaluator = evaluator

    def process(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate expressions in options dictionary.

        Args:
            options: Raw options dictionary

        Returns:
            Options with evaluated expressions
        """
        from lark import Token

        evaluated = {}
        for key, value in options.items():
            # If value is a Token, convert to string first
            if isinstance(value, Token):
                value = str(value.value)

            eval_succeeded = False

            # Try to evaluate if it looks like an expression
            if isinstance(value, str):
                # Check if it's a variable reference (single word that might be a variable)
                if value.isalpha() and value not in ["true", "false", "none"]:
                    # Try as variable first
                    try:
                        evaluated[key] = self.evaluator.evaluate(f"\\{value}")
                        eval_succeeded = True
                    except Exception:
                        pass

                # Try to evaluate if it has operators or backslash (only if not already evaluated)
                if not eval_succeeded and (
                    "\\" in value or any(op in value for op in ["+", "-", "*", "/", "("])
                ):
                    try:
                        evaluated[key] = self.evaluator.evaluate(value)
                        eval_succeeded = True
                    except Exception:
                        pass

            # Keep as-is if no evaluation succeeded
            if not eval_succeeded:
                evaluated[key] = value

        return evaluated

    def safe_evaluate(self, value, evaluator: Optional[Any] = None):
        """Safely evaluate a value with fallback.

        Args:
            value: Value to evaluate (string expression or literal)
            evaluator: MathEvaluator to use (defaults to self.evaluator)

        Returns:
            Evaluated result, or original value if evaluation fails
        """
        if not isinstance(value, str):
            return value

        eval_instance = evaluator or self.evaluator
        try:
            return eval_instance.evaluate(value)
        except Exception:
            return value
