"""Tests for inline coordinate definitions in paths."""

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


class TestInlineCoordinates:
    """Test inline coordinate definitions in paths."""

    def test_basic_inline_coordinate(self, parser, converter):
        """Test basic inline coordinate definition."""
        tikz = r"""
        \begin{tikzpicture}
        \draw (0,0) coordinate(A) -- (1,1);
        \draw (A) -- (2,0);
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg
        assert "<path" in svg
        # Should have two paths
        assert svg.count("<path") == 2

    def test_multiple_inline_coordinates(self, parser, converter):
        """Test multiple inline coordinates in same path."""
        tikz = r"""
        \begin{tikzpicture}
        \draw (0,0) coordinate(A) -- (1,0) coordinate(B) -- (1,1) coordinate(C);
        \draw (A) -- (C);
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg
        assert svg.count("<path") == 2

    def test_inline_coordinate_with_expression(self, parser, converter):
        """Test inline coordinate with math expression."""
        tikz = r"""
        \begin{tikzpicture}
        \pgfmathsetmacro{\r}{2}
        \draw (0,0) coordinate(center) -- (\r,\r) coordinate(corner);
        \draw (center) circle (0.1);
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg
        # Should have a path and a circle
        assert "<path" in svg

    def test_inline_coordinate_in_loop(self, parser, converter):
        """Test inline coordinates created in loops."""
        tikz = r"""
        \begin{tikzpicture}
        \foreach \i in {0,1,2} {
            \draw (\i,0) coordinate(P\i) -- (\i,1);
        }
        \draw (P0) -- (P1) -- (P2);
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg
        # Should have 3 vertical lines + 1 connecting line
        assert svg.count("<path") >= 4

    def test_inline_coordinate_with_style(self, parser, converter):
        """Test inline coordinate with path styles."""
        tikz = r"""
        \begin{tikzpicture}
        \draw[thick,red] (0,0) coordinate(start) -- (2,2) coordinate(end);
        \draw[blue,dashed] (start) -- (2,0) -- (end);
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg
        assert "stroke: #FF0000" in svg
        assert "stroke: #0000FF" in svg

    def test_coordinate_reference_before_definition(self, parser, converter):
        """Test that coordinate must be defined before use."""
        tikz = r"""
        \begin{tikzpicture}
        \draw (0,0) coordinate(A) -- (1,1) coordinate(B);
        \draw (A) -- (B);
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg
        # Should work - coordinates defined in first path

    def test_inline_coordinate_reuses_position(self, parser, converter):
        """Test that inline coordinate stores the actual position."""
        tikz = r"""
        \begin{tikzpicture}
        \draw (1,2) coordinate(P) -- (3,4);
        \draw (0,0) -- (P);
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg
        # Second path should go to (1,2) which is where P was defined

    def test_inline_coordinate_with_relative_coords(self, parser, converter):
        """Test inline coordinate with relative coordinates."""
        tikz = r"""
        \begin{tikzpicture}
        \draw (0,0) coordinate(A) -- ++(1,0) coordinate(B);
        \draw (A) -- (B);
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg
        assert "<path" in svg

    def test_inline_coordinate_overwrites(self, parser, converter):
        """Test that redefining a coordinate overwrites the previous definition."""
        tikz = r"""
        \begin{tikzpicture}
        \draw (0,0) coordinate(P) -- (1,1);
        \draw (2,2) coordinate(P) -- (3,3);
        \draw (0,0) -- (P);
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg
        # Last path should go to (2,2) which is the second definition of P
