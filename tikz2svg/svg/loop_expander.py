"""Foreach loop expansion for TikZ to SVG conversion."""

from typing import List

from ..evaluator.math_eval import MathEvaluator
from ..parser.ast_nodes import ForeachLoop


class ForeachLoopExpander:
    """Expands TikZ foreach loops by iterating and processing body statements.

    Handles:
    - Simple iteration over values
    - Multiple variables (paired values)
    - Evaluate clause for computed variables
    - Nested loops with proper scoping
    """

    def __init__(self, option_processor):
        """Initialize foreach loop expander.

        Args:
            option_processor: OptionProcessor for value evaluation
        """
        self.option_processor = option_processor

    def expand(self, loop: ForeachLoop, converter) -> List[str]:
        """Expand foreach loop into list of SVG elements.

        Args:
            loop: ForeachLoop AST node
            converter: SVGConverter instance for context and statement visiting

        Returns:
            List of SVG element strings from expanded loop
        """
        elements = []
        num_vars = len(loop.variables)

        for value in loop.values:
            # Create child context for this iteration
            parent_context = converter.context
            parent_evaluator = converter.evaluator

            converter.context = converter.context.create_child_context()
            converter.evaluator = MathEvaluator(converter.context)

            try:
                # Set loop variable(s)
                self._set_loop_variables(
                    loop.variables, value, num_vars, parent_evaluator, converter.context
                )

                # Handle evaluate clause
                if loop.evaluate_clause:
                    self._handle_evaluate_clause(
                        loop.evaluate_clause, converter.evaluator, converter.context
                    )

                # Visit body statements
                elements.extend(
                    element for stmt in loop.body if (element := converter.visit_statement(stmt))
                )

            finally:
                # Restore parent context
                converter.context = parent_context
                converter.evaluator = parent_evaluator

        return elements

    def _set_loop_variables(
        self, variables: List[str], value, num_vars: int, parent_evaluator, context
    ):
        """Set loop variable(s) in current context.

        Args:
            variables: List of variable names
            value: Value(s) to assign
            num_vars: Number of variables
            parent_evaluator: Parent evaluator for safe evaluation
            context: Current evaluation context
        """
        if num_vars == 1:
            # Single variable
            var_name = variables[0]
            value_eval = self.option_processor.safe_evaluate(value, parent_evaluator)
            context.set_variable(var_name, value_eval)
        elif num_vars > 1 and isinstance(value, (tuple, list)):
            # Multiple variables with paired values
            for i, var_name in enumerate(variables):
                if i < len(value):
                    val = self.option_processor.safe_evaluate(value[i], parent_evaluator)
                    context.set_variable(var_name, val)

    def _handle_evaluate_clause(self, evaluate_clause: dict, evaluator, context):
        """Process evaluate clause to compute derived variables.

        Args:
            evaluate_clause: Dictionary with 'target' and 'expression' keys
            evaluator: Math evaluator
            context: Current evaluation context
        """
        target_var = evaluate_clause["target"]
        expression = evaluate_clause["expression"]

        # Evaluate the expression with current loop variable value
        try:
            result = evaluator.evaluate(expression)
            context.set_variable(target_var, result)
        except Exception:
            pass
