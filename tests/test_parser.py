"""Unit tests for TikZ parser."""

import pytest

from tikz2svg.parser.ast_nodes import *
from tikz2svg.parser.parser import TikzParser


@pytest.fixture
def parser():
    """Create parser instance."""
    return TikzParser()


class TestBasicParsing:
    """Test basic parsing functionality."""

    def test_empty_tikzpicture(self, parser):
        """Test parsing empty tikzpicture."""
        tikz = r"\begin{tikzpicture}\end{tikzpicture}"
        ast = parser.parse(tikz)
        assert isinstance(ast, TikzPicture)
        assert len(ast.statements) == 0

    def test_simple_line(self, parser):
        """Test parsing simple line."""
        tikz = r"\begin{tikzpicture}\draw (0,0) -- (1,1);\end{tikzpicture}"
        ast = parser.parse(tikz)
        assert isinstance(ast, TikzPicture)
        assert len(ast.statements) == 1
        assert isinstance(ast.statements[0], DrawStatement)
        assert ast.statements[0].command == "draw"

    def test_multiple_lines(self, parser):
        """Test parsing multiple connected lines."""
        tikz = r"\begin{tikzpicture}\draw (0,0) -- (1,0) -- (1,1) -- (0,1);\end{tikzpicture}"
        ast = parser.parse(tikz)
        assert isinstance(ast, TikzPicture)
        assert len(ast.statements) == 1
        stmt = ast.statements[0]
        assert isinstance(stmt, DrawStatement)
        assert len(stmt.path.segments) == 4  # Start segment + 3 line segments


class TestCoordinates:
    """Test coordinate parsing."""

    def test_cartesian_coordinates(self, parser):
        """Test Cartesian coordinates."""
        tikz = r"\begin{tikzpicture}\draw (0,0) -- (1.5,2.5);\end{tikzpicture}"
        ast = parser.parse(tikz)
        stmt = ast.statements[0]
        # First coordinate is implicit start point, check destination
        assert len(stmt.path.segments) >= 1

    def test_negative_coordinates(self, parser):
        """Test negative coordinates."""
        tikz = r"\begin{tikzpicture}\draw (-1,-1) -- (1,1);\end{tikzpicture}"
        ast = parser.parse(tikz)
        assert isinstance(ast, TikzPicture)

    def test_polar_coordinates(self, parser):
        """Test polar coordinates."""
        tikz = r"\begin{tikzpicture}\draw (0:1) -- (90:1);\end{tikzpicture}"
        ast = parser.parse(tikz)
        stmt = ast.statements[0]
        assert isinstance(stmt, DrawStatement)


class TestOptions:
    """Test option parsing."""

    def test_simple_option(self, parser):
        """Test simple option flag."""
        tikz = r"\begin{tikzpicture}\draw[red] (0,0) -- (1,1);\end{tikzpicture}"
        ast = parser.parse(tikz)
        stmt = ast.statements[0]
        assert "red" in stmt.options
        assert stmt.options["red"] is True

    def test_key_value_option(self, parser):
        """Test key-value option."""
        tikz = r"\begin{tikzpicture}\draw[color=red] (0,0) -- (1,1);\end{tikzpicture}"
        ast = parser.parse(tikz)
        stmt = ast.statements[0]
        assert "color" in stmt.options
        assert stmt.options["color"] == "red"

    def test_multiple_options(self, parser):
        """Test multiple options."""
        tikz = r"\begin{tikzpicture}\draw[red,thick] (0,0) -- (1,1);\end{tikzpicture}"
        ast = parser.parse(tikz)
        stmt = ast.statements[0]
        assert len(stmt.options) >= 2


class TestDrawCommands:
    """Test different draw commands."""

    def test_fill_command(self, parser):
        """Test fill command."""
        tikz = r"\begin{tikzpicture}\fill (0,0) -- (1,0) -- (1,1);\end{tikzpicture}"
        ast = parser.parse(tikz)
        stmt = ast.statements[0]
        assert isinstance(stmt, DrawStatement)
        assert stmt.command == "fill"

    def test_filldraw_command(self, parser):
        """Test filldraw command."""
        tikz = r"\begin{tikzpicture}\filldraw (0,0) -- (1,0) -- (1,1);\end{tikzpicture}"
        ast = parser.parse(tikz)
        stmt = ast.statements[0]
        assert isinstance(stmt, DrawStatement)
        assert stmt.command == "filldraw"

    def test_multiple_statements(self, parser):
        """Test multiple draw statements."""
        tikz = r"""
        \begin{tikzpicture}
        \draw (0,0) -- (1,1);
        \draw (1,0) -- (0,1);
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        assert len(ast.statements) == 2


class TestNodes:
    """Test node parsing."""

    def test_simple_node(self, parser):
        """Test simple node."""
        tikz = r"\begin{tikzpicture}\node at (0,0) {Hello};\end{tikzpicture}"
        ast = parser.parse(tikz)
        stmt = ast.statements[0]
        assert isinstance(stmt, Node)
        assert stmt.text == "Hello"

    def test_named_node(self, parser):
        """Test named node."""
        tikz = r"\begin{tikzpicture}\node (A) at (0,0) {Hello};\end{tikzpicture}"
        ast = parser.parse(tikz)
        stmt = ast.statements[0]
        assert isinstance(stmt, Node)
        assert stmt.name == "A"


class TestCoordinateDefinition:
    """Test coordinate definitions."""

    def test_coordinate_definition(self, parser):
        """Test coordinate definition."""
        tikz = r"\begin{tikzpicture}\coordinate (A) at (1,2);\end{tikzpicture}"
        ast = parser.parse(tikz)
        stmt = ast.statements[0]
        assert isinstance(stmt, CoordinateDefinition)
        assert stmt.name == "A"
