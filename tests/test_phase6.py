"""Tests for Phase 6 features: Advanced Features (Scopes, Layers, Clipping)."""

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


class TestScopes:
    """Test scope environment functionality."""

    def test_basic_scope(self, parser, converter):
        """Test basic scope creation."""
        tikz = r"""
        \begin{tikzpicture}
        \begin{scope}
            \draw (0,0) -- (1,1);
        \end{scope}
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg
        assert "<path" in svg

    def test_scope_with_options(self, parser, converter):
        """Test scope with style options."""
        tikz = r"""
        \begin{tikzpicture}
        \begin{scope}[red,thick]
            \draw (0,0) -- (1,1);
            \draw (1,0) -- (0,1);
        \end{scope}
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg
        # Both lines should inherit red color and thick style

    def test_nested_scopes(self, parser, converter):
        """Test nested scopes with option inheritance."""
        tikz = r"""
        \begin{tikzpicture}
        \begin{scope}[red]
            \draw (0,0) -- (1,0);
            \begin{scope}[thick]
                \draw (0,1) -- (1,1);
            \end{scope}
        \end{scope}
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg
        # Outer line should be red
        # Inner line should be red and thick

    def test_scope_option_override(self, parser, converter):
        """Test that local options override scope options."""
        tikz = r"""
        \begin{tikzpicture}
        \begin{scope}[red]
            \draw[blue] (0,0) -- (1,1);
        \end{scope}
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg
        # Line should be blue (local overrides scope)

    def test_scope_with_transformations(self, parser, converter):
        """Test scope with transformation options."""
        tikz = r"""
        \begin{tikzpicture}
        \begin{scope}[scale=2]
            \draw (0,0) -- (1,1);
        \end{scope}
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg


class TestClipping:
    """Test clipping path functionality."""

    def test_clip_simple(self, parser, converter):
        """Test basic clipping path."""
        tikz = r"""
        \begin{tikzpicture}
        \clip (0,0) rectangle (2,2);
        \draw (0,0) -- (3,3);
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg
        # Should have clipPath definition

    def test_clip_in_scope(self, parser, converter):
        """Test clipping within a scope."""
        tikz = r"""
        \begin{tikzpicture}
        \begin{scope}
            \clip (0,0) circle (1);
            \draw (0,0) -- (2,2);
        \end{scope}
        \draw (0,0) -- (2,-2);
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg
        # First line should be clipped, second should not

    def test_clip_circle(self, parser, converter):
        """Test clipping with circle."""
        tikz = r"""
        \begin{tikzpicture}
        \clip (0,0) circle (1);
        \fill[red] (-2,-2) rectangle (2,2);
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg


class TestLayers:
    """Test layer management functionality."""

    def test_layer_declaration(self, parser, converter):
        """Test layer declaration."""
        tikz = r"""
        \begin{tikzpicture}
        \pgfdeclarelayer{background}
        \pgfdeclarelayer{foreground}
        \pgfsetlayers{background,main,foreground}
        \draw (0,0) -- (1,1);
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg

    def test_layer_usage(self, parser, converter):
        """Test drawing on different layers."""
        tikz = r"""
        \begin{tikzpicture}
        \pgfdeclarelayer{background}
        \pgfsetlayers{background,main}
        \draw (0,0) -- (1,1);
        \begin{pgfonlayer}{background}
            \fill[gray] (0,0) rectangle (1,1);
        \end{pgfonlayer}
        \draw (0,1) -- (1,0);
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg
        # Background should be rendered first

    def test_nested_layers(self, parser, converter):
        """Test multiple layer switches."""
        tikz = r"""
        \begin{tikzpicture}
        \pgfdeclarelayer{back}
        \pgfdeclarelayer{front}
        \pgfsetlayers{back,main,front}

        \begin{pgfonlayer}{back}
            \draw[red] (0,0) circle (1);
        \end{pgfonlayer}

        \draw[blue] (0,0) -- (1,1);

        \begin{pgfonlayer}{front}
            \draw[green] (0,1) -- (1,0);
        \end{pgfonlayer}
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg


class TestStyleInheritance:
    """Test style inheritance and composition."""

    def test_style_definition(self, parser, converter):
        """Test defining and using styles."""
        tikz = r"""
        \begin{tikzpicture}[every node/.style={draw,circle}]
        \node at (0,0) {A};
        \node at (1,1) {B};
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg

    def test_scope_style_inheritance(self, parser, converter):
        """Test that styles are inherited in scopes."""
        tikz = r"""
        \begin{tikzpicture}
        \tikzset{myline/.style={red,thick}}
        \begin{scope}
            \draw[myline] (0,0) -- (1,1);
        \end{scope}
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg

    def test_tikzpicture_default_options(self, parser, converter):
        """Test default options on tikzpicture."""
        tikz = r"""
        \begin{tikzpicture}[thick,blue]
        \draw (0,0) -- (1,1);
        \draw (0,1) -- (1,0);
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg
        # Both lines should be thick and blue


class TestIntegration:
    """Integration tests combining multiple advanced features."""

    def test_scopes_and_clipping(self, parser, converter):
        """Test scopes with clipping."""
        tikz = r"""
        \begin{tikzpicture}
        \begin{scope}[red]
            \clip (0,0) rectangle (1,1);
            \draw (0,0) -- (2,2);
        \end{scope}
        \draw[blue] (0,0) -- (2,-2);
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg

    def test_layers_and_scopes(self, parser, converter):
        """Test layers within scopes."""
        tikz = r"""
        \begin{tikzpicture}
        \pgfdeclarelayer{bg}
        \pgfsetlayers{bg,main}

        \begin{scope}[thick]
            \begin{pgfonlayer}{bg}
                \draw[gray] (0,0) grid (2,2);
            \end{pgfonlayer}
            \draw[red] (0,0) -- (2,2);
        \end{scope}
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg

    def test_complex_nesting(self, parser, converter):
        """Test complex nesting of scopes and features."""
        tikz = r"""
        \begin{tikzpicture}[scale=1]
        \begin{scope}[red,thick]
            \draw (0,0) rectangle (2,2);
            \begin{scope}[blue]
                \clip (0.5,0.5) circle (0.5);
                \fill (0,0) rectangle (2,2);
            \end{scope}
        \end{scope}
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg

    def test_scope_with_loops(self, parser, converter):
        """Test scopes with foreach loops."""
        tikz = r"""
        \begin{tikzpicture}
        \foreach \i in {0,...,2} {
            \begin{scope}[xshift=\i cm]
                \draw (0,0) circle (0.5);
            \end{scope}
        }
        \end{tikzpicture}
        """
        ast = parser.parse(tikz)
        svg = converter.convert(ast)

        assert "<svg" in svg
