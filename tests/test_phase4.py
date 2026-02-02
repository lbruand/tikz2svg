"""Tests for Phase 4 features: Control Flow."""

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


class TestForeachBasic:
    """Test basic foreach loop functionality."""

    def test_foreach_simple_list(self, parser, converter):
        """Test foreach with simple number list."""
        tikz = r"""
        \begin{tikzpicture}
        \foreach \i in {1,2,3} {
            \draw (\i,0) circle (0.1);
        }
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg
        # Should have 3 circles
        assert svg.count("<path") >= 3

    def test_foreach_range(self, parser, converter):
        """Test foreach with range notation."""
        tikz = r"""
        \begin{tikzpicture}
        \foreach \i in {0,...,4} {
            \draw (\i,0) -- (\i,1);
        }
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg
        # Should have 5 lines
        assert svg.count("<path") >= 5

    def test_foreach_range_with_step(self, parser, converter):
        """Test foreach with explicit step."""
        tikz = r"""
        \begin{tikzpicture}
        \foreach \i in {0,2,...,8} {
            \draw (\i,0) circle (0.2);
        }
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg
        # Should have 5 circles (0,2,4,6,8)
        assert svg.count("<path") >= 5


class TestForeachVariables:
    """Test foreach loop variable substitution."""

    def test_variable_in_coordinate(self, parser, converter):
        """Test loop variable used in coordinates."""
        tikz = r"""
        \begin{tikzpicture}
        \foreach \x in {0,1,2} {
            \draw (\x,0) -- (\x,\x);
        }
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg
        assert svg.count("<path") >= 3

    def test_variable_in_expression(self, parser, converter):
        """Test loop variable in mathematical expression."""
        tikz = r"""
        \begin{tikzpicture}
        \foreach \i in {1,2,3} {
            \draw (0,0) circle (\i*0.5);
        }
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg
        assert svg.count("<path") >= 3

    def test_multiple_variables(self, parser, converter):
        """Test foreach with multiple variables."""
        tikz = r"""
        \begin{tikzpicture}
        \foreach \x/\y in {0/0, 1/1, 2/0} {
            \draw (\x,\y) circle (0.1);
        }
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg
        assert svg.count("<path") >= 3


class TestForeachEvaluate:
    """Test foreach with evaluate clause."""

    def test_evaluate_basic(self, parser, converter):
        """Test basic evaluate clause."""
        tikz = r"""
        \begin{tikzpicture}
        \foreach \i [evaluate=\i as \x using \i*2] in {0,1,2} {
            \draw (\x,0) circle (0.1);
        }
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg
        # Circles should be at x=0, x=2, x=4

    def test_evaluate_with_expression(self, parser, converter):
        """Test evaluate with complex expression."""
        tikz = r"""
        \begin{tikzpicture}
        \foreach \i [evaluate=\i as \r using \i*0.5+1] in {0,1,2} {
            \draw (0,0) circle (\r);
        }
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg


class TestNestedLoops:
    """Test nested foreach loops."""

    def test_nested_loops_simple(self, parser, converter):
        """Test simple nested loops."""
        tikz = r"""
        \begin{tikzpicture}
        \foreach \x in {0,1} {
            \foreach \y in {0,1} {
                \draw (\x,\y) circle (0.1);
            }
        }
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg
        # Should have 4 circles (2x2 grid)
        assert svg.count("<path") >= 4

    def test_nested_loops_with_variables(self, parser, converter):
        """Test nested loops using both loop variables."""
        tikz = r"""
        \begin{tikzpicture}
        \foreach \x in {0,1,2} {
            \foreach \y in {0,1} {
                \draw (\x,\y) -- (\x+0.5,\y+0.5);
            }
        }
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg
        # Should have 6 lines (3x2)
        assert svg.count("<path") >= 6


class TestIntegration:
    """Integration tests combining multiple features."""

    def test_loop_with_math_and_variables(self, parser, converter):
        """Test loop with mathematical expressions and variables."""
        tikz = r"""
        \begin{tikzpicture}
        \pgfmathsetmacro{\r}{1}
        \foreach \i in {0,...,5} {
            \draw (\i*60:\r) circle (0.1);
        }
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg

    def test_complex_foreach_pattern(self, parser, converter):
        """Test complex foreach usage."""
        tikz = r"""
        \begin{tikzpicture}
        \foreach \i [evaluate=\i as \angle using \i*45] in {0,...,7} {
            \draw (0,0) -- (\angle:1);
        }
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg
        # Should have 8 lines radiating from origin

    def test_grid_with_foreach(self, parser, converter):
        """Test creating a grid with foreach."""
        tikz = r"""
        \begin{tikzpicture}
        \foreach \x in {0,...,3} {
            \foreach \y in {0,...,3} {
                \filldraw (\x,\y) circle (0.05);
            }
        }
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg
        # Should have 16 circles (4x4 grid)
        assert svg.count("<path") >= 16
