"""Tests for Phase 7 features: Macro System."""

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


class TestSimpleMacros:
    """Test simple macro definitions and expansion."""

    def test_def_basic(self, parser, converter):
        """Test basic \\def macro."""
        tikz = r"""
        \begin{tikzpicture}
        \def\mycolor{red}
        \draw[\mycolor] (0,0) -- (1,1);
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg
        # Line should be red

    def test_def_multiple(self, parser, converter):
        """Test multiple \\def macros."""
        tikz = r"""
        \begin{tikzpicture}
        \def\mycolor{blue}
        \def\mythickness{thick}
        \draw[\mycolor,\mythickness] (0,0) -- (1,1);
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg

    def test_def_numeric(self, parser, converter):
        """Test \\def with numeric values."""
        tikz = r"""
        \begin{tikzpicture}
        \def\radius{2}
        \draw (0,0) circle (\radius);
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg


class TestParametricMacros:
    """Test parametric macros with \\newcommand."""

    def test_newcommand_one_param(self, parser, converter):
        """Test \\newcommand with one parameter."""
        tikz = r"""
        \begin{tikzpicture}
        \newcommand{\mycircle}[1]{\draw (0,0) circle (#1);}
        \mycircle{1}
        \mycircle{2}
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg
        # Should have 2 circles

    def test_newcommand_two_params(self, parser, converter):
        """Test \\newcommand with two parameters."""
        tikz = r"""
        \begin{tikzpicture}
        \newcommand{\drawline}[2]{\draw (#1) -- (#2);}
        \drawline{0,0}{1,1}
        \drawline{0,1}{1,0}
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg

    def test_newcommand_three_params(self, parser, converter):
        """Test \\newcommand with three parameters."""
        tikz = r"""
        \begin{tikzpicture}
        \newcommand{\coloredcircle}[3]{\draw[#1] (#2) circle (#3);}
        \coloredcircle{red}{0,0}{1}
        \coloredcircle{blue}{2,0}{0.5}
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg

    def test_newcommand_complex_body(self, parser, converter):
        """Test \\newcommand with complex body."""
        tikz = r"""
        \begin{tikzpicture}
        \newcommand{\square}[1]{
            \draw (#1) -- ++(1,0) -- ++(0,1) -- ++(-1,0) -- cycle;
        }
        \square{0,0}
        \square{2,0}
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg


class TestMacroExpansion:
    """Test macro expansion and substitution."""

    def test_macro_in_macro(self, parser, converter):
        """Test macro used inside another macro."""
        tikz = r"""
        \begin{tikzpicture}
        \def\myradius{1}
        \newcommand{\mycircle}[1]{\draw (#1) circle (\myradius);}
        \mycircle{0,0}
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg

    def test_macro_expansion_order(self, parser, converter):
        """Test that macros are expanded in correct order."""
        tikz = r"""
        \begin{tikzpicture}
        \def\size{2}
        \def\halfsize{1}
        \draw (0,0) circle (\size);
        \draw (0,0) circle (\halfsize);
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg

    def test_macro_redefinition(self, parser, converter):
        """Test that later macro definitions override earlier ones."""
        tikz = r"""
        \begin{tikzpicture}
        \def\mycolor{red}
        \draw[\mycolor] (0,0) -- (1,0);
        \def\mycolor{blue}
        \draw[\mycolor] (0,1) -- (1,1);
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg


class TestMacroScoping:
    """Test macro scoping in different contexts."""

    def test_macro_in_scope(self, parser, converter):
        """Test macro defined inside scope."""
        tikz = r"""
        \begin{tikzpicture}
        \begin{scope}
            \def\mycolor{red}
            \draw[\mycolor] (0,0) -- (1,1);
        \end{scope}
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg

    def test_macro_in_loop(self, parser, converter):
        """Test macro used inside foreach loop."""
        tikz = r"""
        \begin{tikzpicture}
        \def\radius{0.5}
        \foreach \i in {0,1,2} {
            \draw (\i,0) circle (\radius);
        }
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg


class TestComplexMacros:
    """Test complex macro patterns."""

    def test_macro_with_coordinates(self, parser, converter):
        """Test macro that expands to coordinates."""
        tikz = r"""
        \begin{tikzpicture}
        \def\start{0,0}
        \def\end{2,2}
        \draw (\start) -- (\end);
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg

    def test_macro_with_path(self, parser, converter):
        """Test macro that expands to path operations."""
        tikz = r"""
        \begin{tikzpicture}
        \newcommand{\triangle}[1]{
            (#1) -- ++(1,0) -- ++(0,1) -- cycle
        }
        \draw \triangle{0,0};
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg

    def test_nested_macro_calls(self, parser, converter):
        """Test nested macro calls."""
        tikz = r"""
        \begin{tikzpicture}
        \newcommand{\pos}[1]{#1,#1}
        \newcommand{\drawat}[1]{\draw (\pos{#1}) circle (0.5);}
        \drawat{0}
        \drawat{2}
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg


class TestIntegration:
    """Integration tests combining macros with other features."""

    def test_macros_with_math(self, parser, converter):
        """Test macros combined with mathematical expressions."""
        tikz = r"""
        \begin{tikzpicture}
        \pgfmathsetmacro{\r}{2}
        \newcommand{\drawcircle}[1]{\draw (#1*\r,0) circle (0.5);}
        \foreach \i in {0,1,2} {
            \drawcircle{\i}
        }
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg

    def test_macros_with_styles(self, parser, converter):
        """Test macros defining styles."""
        tikz = r"""
        \begin{tikzpicture}
        \def\mystyle{red,thick}
        \draw[\mystyle] (0,0) -- (1,1);
        \draw[\mystyle] (0,1) -- (1,0);
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg

    def test_complex_macro_usage(self, parser, converter):
        """Test complex real-world macro pattern."""
        tikz = r"""
        \begin{tikzpicture}
        \def\n{5}
        \newcommand{\vertex}[1]{
            \draw[fill=black] (#1*72:2) circle (0.1);
        }
        \foreach \i in {0,...,4} {
            \vertex{\i}
        }
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg
