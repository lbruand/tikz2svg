"""Tests for Phase 3 features: Mathematical Expressions."""

import pytest

from tikz2svg.parser.ast_nodes import *
from tikz2svg.parser.parser import TikzParser
from tikz2svg.svg.converter import SVGConverter


@pytest.fixture
def parser():
    """Create parser instance."""
    return TikzParser()


@pytest.fixture
def converter():
    """Create converter instance."""
    return SVGConverter()


class TestBasicArithmetic:
    """Test basic arithmetic operations."""

    def test_addition_in_coordinate(self, parser, converter):
        """Test addition in coordinates."""
        tikz = r"\begin{tikzpicture}\draw (0,0) -- (1+1,2);\end{tikzpicture}"
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg
        assert "<path" in svg

    def test_subtraction_in_coordinate(self, parser, converter):
        """Test subtraction in coordinates."""
        tikz = r"\begin{tikzpicture}\draw (0,0) -- (3-1,4-2);\end{tikzpicture}"
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg

    def test_multiplication_in_coordinate(self, parser, converter):
        """Test multiplication in coordinates."""
        tikz = r"\begin{tikzpicture}\draw (0,0) -- (2*3,1*5);\end{tikzpicture}"
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg

    def test_division_in_coordinate(self, parser, converter):
        """Test division in coordinates."""
        tikz = r"\begin{tikzpicture}\draw (0,0) -- (6/2,8/4);\end{tikzpicture}"
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg

    def test_mixed_operations(self, parser, converter):
        """Test mixed arithmetic operations."""
        tikz = r"\begin{tikzpicture}\draw (0,0) -- (2*3+1,10/2-1);\end{tikzpicture}"
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg


class TestMathFunctions:
    """Test mathematical functions."""

    def test_sqrt_function(self, parser, converter):
        """Test sqrt function."""
        tikz = r"\begin{tikzpicture}\draw (0,0) -- (sqrt(4),sqrt(9));\end{tikzpicture}"
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg

    def test_sin_function(self, parser, converter):
        """Test sin function."""
        tikz = r"\begin{tikzpicture}\draw (0,0) -- (sin(30),sin(90));\end{tikzpicture}"
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg

    def test_cos_function(self, parser, converter):
        """Test cos function."""
        tikz = r"\begin{tikzpicture}\draw (0,0) -- (cos(0),cos(90));\end{tikzpicture}"
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg

    def test_tan_function(self, parser, converter):
        """Test tan function."""
        tikz = r"\begin{tikzpicture}\draw (0,0) -- (tan(45),1);\end{tikzpicture}"
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg


class TestVariables:
    """Test variable definitions and usage."""

    def test_pgfmathsetmacro(self, parser, converter):
        """Test pgfmathsetmacro variable definition."""
        tikz = r"""
        \begin{tikzpicture}
        \pgfmathsetmacro{\r}{2}
        \draw (0,0) circle (\r);
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg

    def test_variable_in_coordinate(self, parser, converter):
        """Test variable usage in coordinates."""
        tikz = r"""
        \begin{tikzpicture}
        \pgfmathsetmacro{\x}{3}
        \pgfmathsetmacro{\y}{4}
        \draw (0,0) -- (\x,\y);
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg

    def test_variable_with_expression(self, parser, converter):
        """Test variable with mathematical expression."""
        tikz = r"""
        \begin{tikzpicture}
        \pgfmathsetmacro{\r}{sqrt(2)}
        \draw (0,0) circle (\r);
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg

    def test_variable_arithmetic(self, parser, converter):
        """Test arithmetic with variables."""
        tikz = r"""
        \begin{tikzpicture}
        \pgfmathsetmacro{\r}{2}
        \draw (0,0) -- (2*\r,\r+1);
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg


class TestComplexExpressions:
    """Test complex mathematical expressions."""

    def test_nested_functions(self, parser, converter):
        """Test nested function calls."""
        tikz = r"\begin{tikzpicture}\draw (0,0) -- (sqrt(sin(30)),1);\end{tikzpicture}"
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg

    def test_parentheses(self, parser, converter):
        """Test parentheses in expressions."""
        tikz = r"\begin{tikzpicture}\draw (0,0) -- ((2+3)*4,(10-5)/2);\end{tikzpicture}"
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg

    def test_expression_in_options(self, parser, converter):
        """Test expressions in options."""
        tikz = r"""
        \begin{tikzpicture}
        \pgfmathsetmacro{\w}{2}
        \draw[line width=\w] (0,0) -- (1,1);
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg


class TestIntegration:
    """Integration tests combining multiple features."""

    def test_complex_drawing_with_math(self, parser, converter):
        """Test complex drawing with mathematical expressions."""
        tikz = r"""
        \begin{tikzpicture}
        \pgfmathsetmacro{\r}{1.5}
        \pgfmathsetmacro{\angle}{45}
        \draw (0,0) -- (\r*cos(\angle),\r*sin(\angle));
        \draw (0,0) circle (\r);
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg
        assert svg.count("<path") >= 2

    def test_multiple_variables(self, parser, converter):
        """Test multiple variable definitions."""
        tikz = r"""
        \begin{tikzpicture}
        \pgfmathsetmacro{\a}{2}
        \pgfmathsetmacro{\b}{3}
        \pgfmathsetmacro{\c}{sqrt(\a*\a + \b*\b)}
        \draw (0,0) -- (\a,0) -- (\a,\b) -- cycle;
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg
