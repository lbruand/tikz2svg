"""Unit tests for OptionProcessor."""

import pytest
from lark import Token
from tikz2svg.svg.option_processor import OptionProcessor
from tikz2svg.evaluator.math_eval import MathEvaluator


@pytest.fixture
def setup_processor():
    """Create OptionProcessor with evaluator."""
    evaluator = MathEvaluator()
    processor = OptionProcessor(evaluator)
    return processor, evaluator


def test_process_simple_values(setup_processor):
    """Test processing options with simple values."""
    processor, _ = setup_processor

    options = {"color": "red", "thickness": "2"}
    result = processor.process(options)

    assert result["color"] == "red"
    assert result["thickness"] == "2"


def test_process_token_values(setup_processor):
    """Test processing options with Token values."""
    processor, _ = setup_processor

    options = {"color": Token("NAME", "blue")}
    result = processor.process(options)

    assert result["color"] == "blue"


def test_process_variable_reference(setup_processor):
    """Test processing variable references."""
    processor, evaluator = setup_processor

    # Set a variable in the evaluator context
    evaluator.context.set_variable("myvar", 42)

    options = {"value": "myvar"}
    result = processor.process(options)

    # Should evaluate \\myvar
    assert result["value"] == 42


def test_process_expression_with_operators(setup_processor):
    """Test processing expressions with operators."""
    processor, _ = setup_processor

    options = {"width": "2*3", "height": "10+5"}
    result = processor.process(options)

    assert result["width"] == 6
    assert result["height"] == 15


def test_process_expression_with_backslash(setup_processor):
    """Test processing expressions with backslash (LaTeX commands)."""
    processor, evaluator = setup_processor

    # Set a variable
    evaluator.context.set_variable("r", 5)

    options = {"radius": "\\r*2"}
    result = processor.process(options)

    assert result["radius"] == 10


def test_process_expression_with_parentheses(setup_processor):
    """Test processing expressions with parentheses."""
    processor, _ = setup_processor

    options = {"value": "(2+3)*4"}
    result = processor.process(options)

    assert result["value"] == 20


def test_process_reserved_words(setup_processor):
    """Test that reserved words (true, false, none) are not evaluated as variables."""
    processor, _ = setup_processor

    options = {"flag1": "true", "flag2": "false", "flag3": "none"}
    result = processor.process(options)

    # Should keep as strings, not try to evaluate
    assert result["flag1"] == "true"
    assert result["flag2"] == "false"
    assert result["flag3"] == "none"


def test_process_invalid_expression(setup_processor):
    """Test that invalid expressions fall back to original value."""
    processor, _ = setup_processor

    options = {"value": "2 + + invalid"}
    result = processor.process(options)

    # Should keep original value on evaluation failure
    assert result["value"] == "2 + + invalid"


def test_process_non_string_values(setup_processor):
    """Test processing non-string values (should pass through)."""
    processor, _ = setup_processor

    options = {"num": 42, "flag": True, "nested": {"key": "value"}}
    result = processor.process(options)

    assert result["num"] == 42
    assert result["flag"] is True
    assert result["nested"] == {"key": "value"}


def test_process_mixed_options(setup_processor):
    """Test processing mixed option types."""
    processor, evaluator = setup_processor

    evaluator.context.set_variable("x", 10)

    options = {
        "color": "red",
        "width": "2*3",
        "variable": "x",
        "number": 5,
        "expression": "\\x+5"
    }
    result = processor.process(options)

    assert result["color"] == "red"
    assert result["width"] == 6
    assert result["variable"] == 10
    assert result["number"] == 5
    assert result["expression"] == 15


def test_safe_evaluate_with_evaluator(setup_processor):
    """Test safe_evaluate with explicit evaluator."""
    processor, evaluator = setup_processor

    result = processor.safe_evaluate("2+3", evaluator)
    assert result == 5


def test_safe_evaluate_default_evaluator(setup_processor):
    """Test safe_evaluate using default evaluator."""
    processor, _ = setup_processor

    result = processor.safe_evaluate("10*2")
    assert result == 20


def test_safe_evaluate_non_string(setup_processor):
    """Test safe_evaluate with non-string value returns it unchanged."""
    processor, _ = setup_processor

    assert processor.safe_evaluate(42) == 42
    assert processor.safe_evaluate(3.14) == 3.14
    assert processor.safe_evaluate(None) is None


def test_safe_evaluate_invalid_expression(setup_processor):
    """Test safe_evaluate with invalid expression returns original."""
    processor, _ = setup_processor

    result = processor.safe_evaluate("invalid!!!")
    assert result == "invalid!!!"


def test_safe_evaluate_empty_string(setup_processor):
    """Test safe_evaluate with empty string."""
    processor, _ = setup_processor

    result = processor.safe_evaluate("")
    # Empty string evaluates to 0.0 via the evaluator
    assert result == 0.0


def test_process_alpha_string_not_in_reserved(setup_processor):
    """Test that alphabetic strings not in reserved list are tried as variables."""
    processor, evaluator = setup_processor

    # Variable doesn't exist, should fall back to original
    options = {"value": "unknownvar"}
    result = processor.process(options)

    # Should keep original since variable not found
    assert result["value"] == "unknownvar"


def test_process_variable_evaluation_failure(setup_processor):
    """Test variable evaluation that fails falls back to expression evaluation."""
    processor, _ = setup_processor

    # Single word that's not a variable and not reserved
    options = {"value": "notavar"}
    result = processor.process(options)

    # Should try as variable (fail), then keep original
    assert result["value"] == "notavar"


def test_process_expression_evaluation_with_division(setup_processor):
    """Test expression with division operator."""
    processor, _ = setup_processor

    options = {"value": "10/2"}
    result = processor.process(options)

    assert result["value"] == 5


def test_process_expression_evaluation_with_subtraction(setup_processor):
    """Test expression with subtraction operator."""
    processor, _ = setup_processor

    options = {"value": "10-3"}
    result = processor.process(options)

    assert result["value"] == 7
