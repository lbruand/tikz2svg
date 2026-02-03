"""String variable evaluation for TikZ to SVG conversion."""

import re

from ..evaluator.context import EvaluationContext


class StringEvaluator:
    """Evaluates variable references within strings.

    Replaces variable references like \\i, \\x with their current values
    from the evaluation context.
    """

    def __init__(self, context: EvaluationContext):
        """Initialize string evaluator.

        Args:
            context: Evaluation context containing variable values
        """
        self.context = context

    def evaluate(self, text: str) -> str:
        """Evaluate variable references in a string.

        Replaces variable references like \\i, \\x with their current values
        from the evaluation context.

        Args:
            text: String that may contain variable references

        Returns:
            String with variables replaced by their values

        Examples:
            >>> context = EvaluationContext()
            >>> context.set_variable("i", 5)
            >>> evaluator = StringEvaluator(context)
            >>> evaluator.evaluate("P\\i")
            'P5'
        """
        if not text or "\\" not in text:
            return text

        # Find all variable references (e.g., \i, \x, \myvar)
        pattern = r"\\([a-zA-Z][a-zA-Z0-9]*)"

        def replace_var(match):
            var_name = match.group(1)
            try:
                value = self.context.get_variable(var_name)
                # If variable is not found, get_variable returns None
                if value is None:
                    return match.group(0)
                return str(value)
            except (KeyError, AttributeError):
                # Variable not found, keep original
                return match.group(0)

        result = re.sub(pattern, replace_var, text)
        return result
