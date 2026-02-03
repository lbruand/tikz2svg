"""Unit tests for StringEvaluator."""

import pytest

from tikz2svg.evaluator.context import EvaluationContext
from tikz2svg.svg.string_evaluator import StringEvaluator


@pytest.fixture
def context():
    """Create evaluation context."""
    return EvaluationContext()


@pytest.fixture
def evaluator(context):
    """Create string evaluator."""
    return StringEvaluator(context)


class TestBasicEvaluation:
    """Test basic string variable evaluation."""

    def test_empty_string(self, evaluator):
        """Test empty string returns empty string."""
        assert evaluator.evaluate("") == ""

    def test_none_string(self, evaluator):
        """Test None returns None."""
        result = evaluator.evaluate(None)
        assert result is None

    def test_string_without_variables(self, evaluator):
        """Test string without variables is returned unchanged."""
        text = "Hello World"
        assert evaluator.evaluate(text) == text

    def test_string_with_backslash_no_variable(self, evaluator):
        """Test string with backslash but no variable pattern."""
        text = "Path\\to\\file"
        assert evaluator.evaluate(text) == text


class TestSingleVariable:
    """Test evaluation of single variables."""

    def test_single_variable_integer(self, evaluator, context):
        """Test evaluating single integer variable."""
        context.set_variable("i", 5)
        result = evaluator.evaluate("P\\i")
        assert result == "P5"

    def test_single_variable_float(self, evaluator, context):
        """Test evaluating single float variable."""
        context.set_variable("x", 3.14)
        result = evaluator.evaluate("Point\\x")
        assert result == "Point3.14"

    def test_single_variable_string(self, evaluator, context):
        """Test evaluating single string variable."""
        context.set_variable("name", "foo")
        result = evaluator.evaluate("Node\\name")
        assert result == "Nodefoo"

    def test_single_variable_at_start(self, evaluator, context):
        """Test variable at start of string."""
        context.set_variable("i", 1)
        result = evaluator.evaluate("\\i-suffix")
        assert result == "1-suffix"

    def test_single_variable_at_end(self, evaluator, context):
        """Test variable at end of string."""
        context.set_variable("i", 2)
        result = evaluator.evaluate("prefix-\\i")
        assert result == "prefix-2"

    def test_single_variable_alone(self, evaluator, context):
        """Test variable as entire string."""
        context.set_variable("value", 42)
        result = evaluator.evaluate("\\value")
        assert result == "42"


class TestMultipleVariables:
    """Test evaluation of multiple variables in same string."""

    def test_two_variables(self, evaluator, context):
        """Test evaluating two variables."""
        context.set_variable("x", 1)
        context.set_variable("y", 2)
        result = evaluator.evaluate("Point\\x-\\y")
        assert result == "Point1-2"

    def test_three_variables(self, evaluator, context):
        """Test evaluating three variables."""
        context.set_variable("a", 1)
        context.set_variable("b", 2)
        context.set_variable("c", 3)
        result = evaluator.evaluate("\\a:\\b:\\c")
        assert result == "1:2:3"

    def test_repeated_variable(self, evaluator, context):
        """Test same variable used multiple times."""
        context.set_variable("i", 5)
        result = evaluator.evaluate("\\i-\\i-\\i")
        assert result == "5-5-5"

    def test_mixed_variables_and_text(self, evaluator, context):
        """Test complex mix of variables and text."""
        context.set_variable("row", 2)
        context.set_variable("col", 3)
        result = evaluator.evaluate("cell[\\row,\\col]")
        assert result == "cell[2,3]"


class TestVariableNames:
    """Test different variable name patterns."""

    def test_single_letter_variable(self, evaluator, context):
        """Test single letter variable name."""
        context.set_variable("x", 10)
        result = evaluator.evaluate("\\x")
        assert result == "10"

    def test_multi_letter_variable(self, evaluator, context):
        """Test multi-letter variable name."""
        context.set_variable("index", 99)
        result = evaluator.evaluate("\\index")
        assert result == "99"

    def test_variable_with_numbers(self, evaluator, context):
        """Test variable name with numbers."""
        context.set_variable("var1", "a")
        context.set_variable("var2", "b")
        result = evaluator.evaluate("\\var1-\\var2")
        assert result == "a-b"

    def test_uppercase_variable(self, evaluator, context):
        """Test uppercase variable names."""
        context.set_variable("CONSTANT", 100)
        result = evaluator.evaluate("\\CONSTANT")
        assert result == "100"

    def test_mixed_case_variable(self, evaluator, context):
        """Test mixed case variable names."""
        context.set_variable("MyVar", 42)
        result = evaluator.evaluate("\\MyVar")
        assert result == "42"


class TestUndefinedVariables:
    """Test handling of undefined variables."""

    def test_undefined_variable_preserved(self, evaluator):
        """Test undefined variable is kept as-is."""
        result = evaluator.evaluate("P\\undefined")
        assert result == "P\\undefined"

    def test_undefined_variable_with_defined(self, evaluator, context):
        """Test mix of defined and undefined variables."""
        context.set_variable("i", 1)
        result = evaluator.evaluate("\\i-\\undefined-\\i")
        assert result == "1-\\undefined-1"

    def test_multiple_undefined_variables(self, evaluator):
        """Test multiple undefined variables preserved."""
        result = evaluator.evaluate("\\a-\\b-\\c")
        assert result == "\\a-\\b-\\c"


class TestVariableTypes:
    """Test different variable value types."""

    def test_integer_value(self, evaluator, context):
        """Test integer variable value."""
        context.set_variable("count", 10)
        result = evaluator.evaluate("N\\count")
        assert result == "N10"

    def test_float_value(self, evaluator, context):
        """Test float variable value."""
        context.set_variable("pi", 3.14159)
        result = evaluator.evaluate("\\pi")
        assert result == "3.14159"

    def test_zero_value(self, evaluator, context):
        """Test zero value."""
        context.set_variable("zero", 0)
        result = evaluator.evaluate("\\zero")
        assert result == "0"

    def test_negative_value(self, evaluator, context):
        """Test negative value."""
        context.set_variable("neg", -5)
        result = evaluator.evaluate("\\neg")
        assert result == "-5"

    def test_boolean_value(self, evaluator, context):
        """Test boolean value converted to string."""
        context.set_variable("flag", True)
        result = evaluator.evaluate("\\flag")
        assert result == "True"


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_backslash_not_followed_by_letter(self, evaluator):
        """Test backslash not followed by letter is preserved."""
        result = evaluator.evaluate("\\123")
        assert result == "\\123"

    def test_backslash_followed_by_special_char(self, evaluator):
        """Test backslash followed by special character."""
        result = evaluator.evaluate("\\@test")
        assert result == "\\@test"

    def test_consecutive_backslashes(self, evaluator):
        """Test consecutive backslashes."""
        result = evaluator.evaluate("\\\\text")
        assert result == "\\\\text"

    def test_backslash_at_end(self, evaluator):
        """Test string ending with backslash."""
        result = evaluator.evaluate("text\\")
        assert result == "text\\"

    def test_variable_adjacent_to_text_no_separator(self, evaluator, context):
        """Test variable immediately followed by text."""
        context.set_variable("var", 5)
        result = evaluator.evaluate("prefix\\varSuffix")
        # Note: This will try to find variable "varSuffix", not "var"
        assert result == "prefix\\varSuffix"


class TestRealWorldScenarios:
    """Test real-world usage scenarios."""

    def test_coordinate_name_in_loop(self, evaluator, context):
        """Test coordinate name with loop variable."""
        context.set_variable("i", 0)
        assert evaluator.evaluate("P\\i") == "P0"

        context.set_variable("i", 1)
        assert evaluator.evaluate("P\\i") == "P1"

        context.set_variable("i", 2)
        assert evaluator.evaluate("P\\i") == "P2"

    def test_node_name_with_two_indices(self, evaluator, context):
        """Test node name with row and column indices."""
        context.set_variable("row", 2)
        context.set_variable("col", 3)
        result = evaluator.evaluate("cell\\row\\col")
        assert result == "cell23"

    def test_generated_label(self, evaluator, context):
        """Test generated label from variables."""
        context.set_variable("layer", 3)
        context.set_variable("index", 5)
        result = evaluator.evaluate("L\\layer-N\\index")
        assert result == "L3-N5"

    def test_numeric_sequence(self, evaluator, context):
        """Test generating numeric sequence."""
        results = []
        for i in range(5):
            context.set_variable("n", i)
            results.append(evaluator.evaluate("item\\n"))
        assert results == ["item0", "item1", "item2", "item3", "item4"]


class TestContextIntegration:
    """Test integration with evaluation context."""

    def test_context_scope(self, evaluator, context):
        """Test variable scope in context."""
        # Set variable in parent context
        context.set_variable("x", 1)
        assert evaluator.evaluate("\\x") == "1"

        # Create child context
        child_context = context.create_child_context()
        child_evaluator = StringEvaluator(child_context)

        # Child should see parent's variable
        assert child_evaluator.evaluate("\\x") == "1"

        # Set variable in child
        child_context.set_variable("y", 2)
        assert child_evaluator.evaluate("\\y") == "2"

        # Parent should not see child's variable
        assert evaluator.evaluate("\\y") == "\\y"

    def test_variable_override_in_child(self, evaluator, context):
        """Test variable override in child context."""
        context.set_variable("x", 1)
        assert evaluator.evaluate("\\x") == "1"

        # Create child and override
        child_context = context.create_child_context()
        child_context.set_variable("x", 10)
        child_evaluator = StringEvaluator(child_context)

        # Child sees overridden value
        assert child_evaluator.evaluate("\\x") == "10"

        # Parent still sees original
        assert evaluator.evaluate("\\x") == "1"


class TestPerformance:
    """Test performance with many variables."""

    def test_many_variables_in_string(self, evaluator, context):
        """Test string with many variable references."""
        # Set up 10 variables
        for i in range(10):
            context.set_variable(f"v{i}", i)

        # Build string with all variables
        text = "-".join([f"\\v{i}" for i in range(10)])
        result = evaluator.evaluate(text)
        expected = "-".join(str(i) for i in range(10))
        assert result == expected

    def test_many_context_variables(self, evaluator, context):
        """Test with many variables in context but few in string."""
        # Set up 100 variables in context
        for i in range(100):
            context.set_variable(f"var{i}", i)

        # Use only one
        context.set_variable("x", 42)
        result = evaluator.evaluate("The answer is \\x")
        assert result == "The answer is 42"
