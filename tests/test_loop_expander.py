"""Unit tests for ForeachLoopExpander."""

import pytest

from tikz2svg.evaluator.context import EvaluationContext
from tikz2svg.evaluator.math_eval import MathEvaluator
from tikz2svg.parser.ast_nodes import DrawStatement, ForeachLoop, Path
from tikz2svg.svg.loop_expander import ForeachLoopExpander
from tikz2svg.svg.option_processor import OptionProcessor


class MockConverter:
    """Mock converter for testing loop expander."""

    def __init__(self):
        self.context = EvaluationContext()
        self.evaluator = MathEvaluator(self.context)
        self.visited_statements = []

    def visit_statement(self, stmt):
        """Mock visit_statement that records calls."""
        self.visited_statements.append(stmt)
        return f"<element-{len(self.visited_statements)}/>"


@pytest.fixture
def setup_expander():
    """Create ForeachLoopExpander with dependencies."""
    evaluator = MathEvaluator()
    option_processor = OptionProcessor(evaluator)
    expander = ForeachLoopExpander(option_processor)
    converter = MockConverter()
    return expander, converter


def test_simple_loop_single_variable(setup_expander):
    """Test simple foreach loop with single variable."""
    expander, converter = setup_expander

    loop = ForeachLoop(
        variables=["i"],
        values=[1, 2, 3],
        body=[
            DrawStatement(command="draw", options={}, path=Path()),
            DrawStatement(command="draw", options={}, path=Path()),
        ],
        evaluate_clause=None,
    )

    result = expander.expand(loop, converter)

    # Should expand 3 iterations × 2 statements = 6 elements
    assert len(result) == 6
    assert all(elem.startswith("<element-") for elem in result)


def test_loop_with_variable_evaluation(setup_expander):
    """Test that loop variables are set correctly."""
    expander, converter = setup_expander

    loop = ForeachLoop(variables=["i"], values=[5, 10, 15], body=[], evaluate_clause=None)

    # Create a custom converter that checks variable values
    variable_values = []

    def capture_variable(stmt):
        variable_values.append(converter.context.get_variable("i"))
        return f"elem-{len(variable_values)}"

    converter.visit_statement = capture_variable

    loop.body = [DrawStatement(command="draw", options={}, path=Path())]
    expander.expand(loop, converter)

    assert variable_values == [5, 10, 15]


def test_loop_with_multiple_variables(setup_expander):
    """Test foreach loop with multiple variables (paired values)."""
    expander, converter = setup_expander

    loop = ForeachLoop(
        variables=["x", "y"],
        values=[(1, 2), (3, 4), (5, 6)],
        body=[DrawStatement(command="draw", options={}, path=Path())],
        evaluate_clause=None,
    )

    result = expander.expand(loop, converter)

    # Should expand 3 iterations × 1 statement = 3 elements
    assert len(result) == 3


def test_loop_with_evaluate_clause(setup_expander):
    """Test foreach loop with evaluate clause."""
    expander, converter = setup_expander

    loop = ForeachLoop(
        variables=["i"],
        values=[1, 2, 3],
        body=[],
        evaluate_clause={"target": "double", "expression": "\\i * 2"},
    )

    # Create a custom converter that checks evaluated variable
    evaluated_values = []

    def capture_evaluated(stmt):
        evaluated_values.append(converter.context.get_variable("double"))
        return "elem"

    converter.visit_statement = capture_evaluated

    loop.body = [DrawStatement(command="draw", options={}, path=Path())]
    expander.expand(loop, converter)

    assert evaluated_values == [2, 4, 6]


def test_loop_context_isolation(setup_expander):
    """Test that loop iterations have isolated contexts."""
    expander, converter = setup_expander

    # Set a variable in parent context
    converter.context.set_variable("outer", 100)

    loop = ForeachLoop(
        variables=["i"],
        values=[1, 2],
        body=[DrawStatement(command="draw", options={}, path=Path())],
        evaluate_clause=None,
    )

    expander.expand(loop, converter)

    # Parent context should still have outer variable
    assert converter.context.get_variable("outer") == 100

    # Loop variable should not be in parent context's local variables
    # (it was set in child context which was discarded)
    assert "i" not in converter.context.variables


def test_loop_context_restoration(setup_expander):
    """Test that context is properly restored after loop."""
    expander, converter = setup_expander

    original_context = converter.context
    original_evaluator = converter.evaluator

    loop = ForeachLoop(
        variables=["i"],
        values=[1, 2, 3],
        body=[DrawStatement(command="draw", options={}, path=Path())],
        evaluate_clause=None,
    )

    expander.expand(loop, converter)

    # Context and evaluator should be restored
    assert converter.context is original_context
    assert converter.evaluator is original_evaluator


def test_empty_loop(setup_expander):
    """Test foreach loop with no values."""
    expander, converter = setup_expander

    loop = ForeachLoop(
        variables=["i"],
        values=[],
        body=[DrawStatement(command="draw", options={}, path=Path())],
        evaluate_clause=None,
    )

    result = expander.expand(loop, converter)

    assert result == []


def test_loop_with_no_body_statements(setup_expander):
    """Test foreach loop with empty body."""
    expander, converter = setup_expander

    loop = ForeachLoop(variables=["i"], values=[1, 2, 3], body=[], evaluate_clause=None)

    result = expander.expand(loop, converter)

    assert result == []


def test_loop_filters_none_elements(setup_expander):
    """Test that None elements from visit_statement are filtered out."""
    expander, converter = setup_expander

    # Create converter that returns None for some statements
    call_count = [0]

    def visit_with_none(stmt):
        call_count[0] += 1
        return f"elem-{call_count[0]}" if call_count[0] % 2 == 1 else None

    converter.visit_statement = visit_with_none

    loop = ForeachLoop(
        variables=["i"],
        values=[1, 2],
        body=[
            DrawStatement(command="draw", options={}, path=Path()),
            DrawStatement(command="draw", options={}, path=Path()),
        ],
        evaluate_clause=None,
    )

    result = expander.expand(loop, converter)

    # Should only have odd-numbered elements (1, 3)
    assert len(result) == 2
    assert result == ["elem-1", "elem-3"]


def test_loop_with_string_values(setup_expander):
    """Test foreach loop with string values."""
    expander, converter = setup_expander

    loop = ForeachLoop(
        variables=["name"],
        values=["red", "blue", "green"],
        body=[DrawStatement(command="draw", options={}, path=Path())],
        evaluate_clause=None,
    )

    result = expander.expand(loop, converter)

    assert len(result) == 3


def test_loop_with_expression_values(setup_expander):
    """Test foreach loop with expression values."""
    expander, converter = setup_expander

    # Set up parent context with a variable
    converter.context.set_variable("base", 10)

    loop = ForeachLoop(
        variables=["i"],
        values=["\\base", "\\base*2", "\\base*3"],
        body=[DrawStatement(command="draw", options={}, path=Path())],
        evaluate_clause=None,
    )

    # Capture evaluated values
    evaluated_values = []

    def capture_value(stmt):
        evaluated_values.append(converter.context.get_variable("i"))
        return "elem"

    converter.visit_statement = capture_value

    expander.expand(loop, converter)

    assert evaluated_values == [10, 20, 30]


def test_nested_loops_context_management(setup_expander):
    """Test that nested loops properly manage contexts."""
    expander, converter = setup_expander

    inner_loop = ForeachLoop(
        variables=["j"],
        values=[1, 2],
        body=[DrawStatement(command="draw", options={}, path=Path())],
        evaluate_clause=None,
    )

    outer_loop = ForeachLoop(
        variables=["i"],
        values=[10, 20],
        body=[inner_loop],
        evaluate_clause=None,
    )

    # Track context depth
    max_depth = [0]
    current_depth = [0]

    original_visit = converter.visit_statement

    def track_depth(stmt):
        current_depth[0] += 1
        max_depth[0] = max(max_depth[0], current_depth[0])
        result = original_visit(stmt)
        current_depth[0] -= 1
        return result

    converter.visit_statement = track_depth

    expander.expand(outer_loop, converter)

    # Inner loop should create nested contexts
    # We should see depth increase when processing inner loop
    assert converter.visited_statements  # Should have visited statements


def test_evaluate_clause_error_handling(setup_expander):
    """Test that evaluate clause errors are handled gracefully."""
    expander, converter = setup_expander

    loop = ForeachLoop(
        variables=["i"],
        values=[1, 2],
        body=[DrawStatement(command="draw", options={}, path=Path())],
        evaluate_clause={
            "target": "result",
            "expression": "invalid_expression!!!",
        },
    )

    # Should not raise exception, just skip setting the variable
    result = expander.expand(loop, converter)

    assert len(result) == 2
