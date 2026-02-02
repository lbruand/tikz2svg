"""Tests for SVG converter."""

import pytest

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


class TestBasicConversion:
    """Test basic TikZ to SVG conversion."""

    def test_simple_line(self, parser, converter):
        """Test converting simple line to SVG."""
        tikz = r"\begin{tikzpicture}\draw (0,0) -- (1,1);\end{tikzpicture}"
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg
        assert "<path" in svg
        assert "d=" in svg

    def test_multiple_lines(self, parser, converter):
        """Test converting multiple lines."""
        tikz = r"\begin{tikzpicture}\draw (0,0) -- (1,0) -- (1,1) -- (0,1);\end{tikzpicture}"
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg
        assert "<path" in svg
        # Should have M, L, L, L commands
        assert "M" in svg
        assert "L" in svg

    def test_colored_line(self, parser, converter):
        """Test line with color."""
        tikz = r"\begin{tikzpicture}\draw[red] (0,0) -- (1,1);\end{tikzpicture}"
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "stroke" in svg
        # Should contain red color
        assert "FF0000" in svg or "red" in svg.lower()

    def test_thick_line(self, parser, converter):
        """Test line with thickness."""
        tikz = r"\begin{tikzpicture}\draw[thick] (0,0) -- (1,1);\end{tikzpicture}"
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "stroke-width" in svg

    def test_filled_shape(self, parser, converter):
        """Test filled shape."""
        tikz = r"\begin{tikzpicture}\fill (0,0) -- (1,0) -- (0,1);\end{tikzpicture}"
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "fill" in svg
        assert "stroke: none" in svg

    def test_node(self, parser, converter):
        """Test text node."""
        tikz = r"\begin{tikzpicture}\node at (0,0) {Hello};\end{tikzpicture}"
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<text" in svg
        assert "Hello" in svg


class TestCoordinateSystems:
    """Test coordinate system handling."""

    def test_polar_coordinates(self, parser, converter):
        """Test polar coordinates."""
        tikz = r"\begin{tikzpicture}\draw (0:1) -- (90:1);\end{tikzpicture}"
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg
        assert "<path" in svg

    def test_named_coordinates(self, parser, converter):
        """Test named coordinates."""
        tikz = r"""
        \begin{tikzpicture}
        \coordinate (A) at (1,1);
        \draw (0,0) -- (A);
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<path" in svg


class TestIntegration:
    """Integration tests with real files."""

    def test_input01(self, parser, converter):
        """Test converting input01.tex."""
        ast = parser.parse_file("inputs/input01.tex")
        svg = converter.convert(ast)

        # Check basic SVG structure
        assert svg.startswith("<svg")
        assert svg.endswith("</svg>")
        assert "<path" in svg
        assert "<text" in svg
        assert "Lorem ipsum" in svg

        # Should have 3 draw statements
        assert svg.count("<path") == 3

        # Should have 1 text node
        assert svg.count("<text") == 1
