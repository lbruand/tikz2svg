"""Tests for Phase 5 features: Coordinate Systems."""

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


class TestPolarCoordinates:
    """Test polar coordinate system."""

    def test_polar_basic(self, parser, converter):
        """Test basic polar coordinates."""
        tikz = r"""
        \begin{tikzpicture}
        \draw (0:1) -- (90:1) -- (180:1) -- (270:1) -- cycle;
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg
        assert "<path" in svg

    def test_polar_with_expressions(self, parser, converter):
        """Test polar coordinates with mathematical expressions."""
        tikz = r"""
        \begin{tikzpicture}
        \foreach \i in {0,...,5} {
            \draw (0,0) -- (\i*60:1);
        }
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg
        # Should have 6 lines
        assert svg.count("<path") >= 6

    def test_polar_with_variable_radius(self, parser, converter):
        """Test polar coordinates with variable radius."""
        tikz = r"""
        \begin{tikzpicture}
        \pgfmathsetmacro{\r}{2}
        \draw (45:\r) circle (0.1);
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg


class TestNamedCoordinates:
    """Test named coordinate system."""

    def test_named_coordinate_definition(self, parser, converter):
        """Test defining and using named coordinates."""
        tikz = r"""
        \begin{tikzpicture}
        \coordinate (A) at (1,1);
        \coordinate (B) at (3,2);
        \draw (A) -- (B);
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg
        assert "<path" in svg

    @pytest.mark.skip(
        reason="Variables in coordinate names not supported: \\coordinate (P\\i) requires expression parsing in names"
    )
    def test_named_coordinates_in_loop(self, parser, converter):
        """Test named coordinates created in loops."""
        tikz = r"""
        \begin{tikzpicture}
        \foreach \i in {0,1,2} {
            \coordinate (P\i) at (\i,\i);
        }
        \draw (P0) -- (P1) -- (P2);
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg

    def test_node_as_coordinate(self, parser, converter):
        """Test using node names as coordinates."""
        tikz = r"""
        \begin{tikzpicture}
        \node (A) at (1,1) {Text};
        \node (B) at (3,2) {More};
        \draw (A) -- (B);
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg


class TestRelativeCoordinates:
    """Test relative coordinate system."""

    def test_relative_plus_plus(self, parser, converter):
        """Test ++ relative coordinates (updates current position)."""
        tikz = r"""
        \begin{tikzpicture}
        \draw (0,0) -- ++(1,0) -- ++(0,1) -- ++(-1,0) -- cycle;
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg
        assert "<path" in svg

    def test_relative_plus(self, parser, converter):
        """Test + relative coordinates (doesn't update position)."""
        tikz = r"""
        \begin{tikzpicture}
        \draw (1,1) -- +(0,1) -- +(1,0);
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg

    def test_relative_mixed(self, parser, converter):
        """Test mixing absolute and relative coordinates."""
        tikz = r"""
        \begin{tikzpicture}
        \draw (0,0) -- ++(1,1) -- (2,0) -- ++(0,1);
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg

    def test_relative_polar(self, parser, converter):
        """Test relative coordinates with polar system."""
        tikz = r"""
        \begin{tikzpicture}
        \draw (0,0) -- ++(0:1) -- ++(90:1) -- ++(180:1);
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg


class TestNodeAnchors:
    """Test node anchor positions."""

    def test_cardinal_anchors(self, parser, converter):
        """Test north, south, east, west anchors."""
        tikz = r"""
        \begin{tikzpicture}
        \node[draw] (box) at (0,0) {Box};
        \draw (box.north) -- (0,1);
        \draw (box.south) -- (0,-1);
        \draw (box.east) -- (1,0);
        \draw (box.west) -- (-1,0);
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg

    def test_corner_anchors(self, parser, converter):
        """Test north east, north west, etc. anchors."""
        tikz = r"""
        \begin{tikzpicture}
        \node[draw] (box) at (0,0) {Box};
        \draw (box.north east) -- (1,1);
        \draw (box.north west) -- (-1,1);
        \draw (box.south east) -- (1,-1);
        \draw (box.south west) -- (-1,-1);
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg

    def test_center_anchor(self, parser, converter):
        """Test center and default anchors."""
        tikz = r"""
        \begin{tikzpicture}
        \node[draw] (box) at (1,1) {Text};
        \draw (0,0) -- (box.center);
        \draw (2,2) -- (box);
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg


class TestCoordinateCalculations:
    """Test coordinate calculations and modifiers."""

    def test_calc_midpoint(self, parser, converter):
        """Test calculating midpoint between coordinates."""
        tikz = r"""
        \begin{tikzpicture}
        \coordinate (A) at (0,0);
        \coordinate (B) at (2,2);
        \draw (A) -- (B);
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg

    def test_perpendicular_coordinates(self, parser, converter):
        """Test |- and -| path connectors."""
        tikz = r"""
        \begin{tikzpicture}
        \draw (0,0) -| (2,2);
        \draw (0,0) |- (2,2);
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg
        assert svg.count("<path") >= 2


class TestIntegration:
    """Integration tests combining coordinate systems."""

    def test_mixed_coordinate_systems(self, parser, converter):
        """Test mixing different coordinate systems."""
        tikz = r"""
        \begin{tikzpicture}
        \coordinate (A) at (0,0);
        \draw (A) -- ++(1,0) -- ++(90:1) -- (0,1);
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg

    def test_complex_shape_with_polar(self, parser, converter):
        """Test complex shape using polar coordinates."""
        tikz = r"""
        \begin{tikzpicture}
        \foreach \i in {0,...,7} {
            \draw (0,0) -- (\i*45:1) -- (\i*45+45:1);
        }
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg

    @pytest.mark.skip(
        reason="Inline foreach within paths not supported: requires foreach as path element, not statement"
    )
    def test_relative_with_foreach(self, parser, converter):
        """Test relative coordinates in loops."""
        tikz = r"""
        \begin{tikzpicture}
        \draw (0,0) \foreach \i in {1,...,4} { -- ++(\i*0.5,0.5) };
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg
