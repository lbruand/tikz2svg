"""Tests for Phase 2 features: Core Drawing."""

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


class TestCircles:
    """Test circle primitives."""

    def test_simple_circle(self, parser, converter):
        """Test circle with radius."""
        tikz = r"\begin{tikzpicture}\draw (0,0) circle (1cm);\end{tikzpicture}"
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg
        assert "<circle" in svg or "<path" in svg  # Can be circle or path

    def test_filled_circle(self, parser, converter):
        """Test filled circle."""
        tikz = r"\begin{tikzpicture}\fill (1,1) circle (0.5);\end{tikzpicture}"
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "fill" in svg


class TestRectangles:
    """Test rectangle primitives."""

    def test_rectangle(self, parser, converter):
        """Test rectangle drawing."""
        tikz = r"\begin{tikzpicture}\draw (0,0) rectangle (2,1);\end{tikzpicture}"
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg
        assert "<rect" in svg or "<path" in svg


class TestArcs:
    """Test arc operations."""

    def test_arc_basic(self, parser, converter):
        """Test basic arc."""
        tikz = r"\begin{tikzpicture}\draw (0,0) arc (0:90:1);\end{tikzpicture}"
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg
        assert "<path" in svg

    def test_arc_with_options(self, parser, converter):
        """Test arc with radius options."""
        tikz = r"\begin{tikzpicture}\draw (0,0) arc [start angle=0, end angle=90, radius=1cm];\end{tikzpicture}"
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg


class TestColorBlending:
    """Test color mixing/blending."""

    def test_color_mixing(self, parser, converter):
        """Test color mixing like blue!30!white."""
        tikz = r"\begin{tikzpicture}\draw[blue!30!white] (0,0) -- (1,1);\end{tikzpicture}"
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "stroke" in svg
        # Should have some color (not pure blue or pure white)

    def test_color_percentage(self, parser, converter):
        """Test color with percentage."""
        tikz = r"\begin{tikzpicture}\fill[red!50] (0,0) rectangle (1,1);\end{tikzpicture}"
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "fill" in svg


class TestEnhancedPaths:
    """Test enhanced path operations."""

    def test_smooth_curve(self, parser, converter):
        """Test smooth curve with controls."""
        tikz = r"\begin{tikzpicture}\draw (0,0) .. controls (1,1) and (2,1) .. (3,0);\end{tikzpicture}"
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<path" in svg
        # Should have cubic Bezier (C command)

    def test_closed_path(self, parser, converter):
        """Test closed path with --cycle."""
        tikz = r"\begin{tikzpicture}\draw (0,0) -- (1,0) -- (1,1) -- cycle;\end{tikzpicture}"
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "Z" in svg or "z" in svg  # Path closing command


class TestArrowTips:
    """Test arrow decorations."""

    def test_arrow_right(self, parser, converter):
        """Test arrow tip at end."""
        tikz = r"\begin{tikzpicture}\draw[->] (0,0) -- (1,0);\end{tikzpicture}"
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<path" in svg or "<defs" in svg  # Arrow marker

    def test_arrow_both(self, parser, converter):
        """Test arrows on both ends."""
        tikz = r"\begin{tikzpicture}\draw[<->] (0,0) -- (1,0);\end{tikzpicture}"
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<path" in svg


class TestLineStyles:
    """Test enhanced line styling."""

    def test_line_cap(self, parser, converter):
        """Test line cap styles."""
        tikz = r"\begin{tikzpicture}\draw[line cap=round] (0,0) -- (1,0);\end{tikzpicture}"
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "stroke-linecap" in svg

    def test_line_join(self, parser, converter):
        """Test line join styles."""
        tikz = r"\begin{tikzpicture}\draw[line join=round] (0,0) -- (1,0) -- (1,1);\end{tikzpicture}"
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "stroke-linejoin" in svg

    def test_double_line(self, parser, converter):
        """Test double line style."""
        tikz = r"\begin{tikzpicture}\draw[double] (0,0) -- (1,0);\end{tikzpicture}"
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        # Double line should create two paths or use stroke-width effects
        assert "<path" in svg


class TestIntegration:
    """Integration tests combining multiple features."""

    def test_complex_shape(self, parser, converter):
        """Test complex shape with multiple features."""
        tikz = r"""
        \begin{tikzpicture}
        \draw[blue!50!white, thick, ->] (0,0) -- (2,0);
        \fill[red!30] (1,1) circle (0.5);
        \draw[dashed] (0,0) rectangle (3,2);
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg
        assert svg.count("<path") >= 2 or svg.count("<circle") >= 1
