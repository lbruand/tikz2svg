"""Tests for LaTeX math mode rendering using ziamath."""

import pytest

from tikz2svg.svg.math_renderer import ZIAMATH_AVAILABLE, MathRenderer


class TestMathRendererAvailability:
    """Test MathRenderer initialization and availability."""

    def test_math_renderer_initialization(self):
        """Test basic initialization."""
        renderer = MathRenderer()
        assert renderer is not None
        assert renderer.enabled == ZIAMATH_AVAILABLE

    def test_math_renderer_disabled(self):
        """Test initialization with rendering disabled."""
        renderer = MathRenderer(enabled=False)
        assert renderer.enabled is False

    def test_math_renderer_enabled_without_ziamath(self):
        """Test that renderer respects ziamath availability."""
        renderer = MathRenderer(enabled=True)
        # If ziamath is not available, renderer should be disabled
        if not ZIAMATH_AVAILABLE:
            assert renderer.enabled is False


class TestMathDetection:
    """Test detection of math mode in text."""

    def test_has_math_simple(self):
        """Test detection of simple math expression."""
        renderer = MathRenderer()
        assert renderer.has_math("$x$") is True

    def test_has_math_complex(self):
        """Test detection of complex math expression."""
        renderer = MathRenderer()
        assert renderer.has_math("$x^2 + y^2 = r^2$") is True

    def test_has_math_with_commands(self):
        """Test detection of math with LaTeX commands."""
        renderer = MathRenderer()
        assert renderer.has_math(r"$\mathcal{I}^+$") is True

    def test_has_math_in_text(self):
        """Test detection of math within text."""
        renderer = MathRenderer()
        assert renderer.has_math("The formula $E=mc^2$ is famous") is True

    def test_has_math_no_math(self):
        """Test detection returns False for plain text."""
        renderer = MathRenderer()
        assert renderer.has_math("Plain text") is False

    def test_has_math_empty_string(self):
        """Test detection with empty string."""
        renderer = MathRenderer()
        assert renderer.has_math("") is False

    def test_has_math_none(self):
        """Test detection with None."""
        renderer = MathRenderer()
        assert renderer.has_math(None) is False

    def test_has_math_single_dollar(self):
        """Test detection with single dollar sign."""
        renderer = MathRenderer()
        assert renderer.has_math("$") is False

    def test_has_math_unclosed_dollar(self):
        """Test detection with unclosed dollar sign."""
        renderer = MathRenderer()
        assert renderer.has_math("$x") is False


@pytest.mark.skipif(not ZIAMATH_AVAILABLE, reason="ziamath not available")
class TestMathRendering:
    """Test actual math rendering (requires ziamath)."""

    def test_render_simple_variable(self):
        """Test rendering a simple variable."""
        renderer = MathRenderer()
        text, svg = renderer.render("$x$")
        assert svg is not None
        assert "<svg" in svg
        assert text == "$x$"

    def test_render_superscript(self):
        """Test rendering with superscript."""
        renderer = MathRenderer()
        text, svg = renderer.render("$i^0$")
        assert svg is not None
        assert "<svg" in svg

    def test_render_subscript(self):
        """Test rendering with subscript."""
        renderer = MathRenderer()
        text, svg = renderer.render("$x_0$")
        assert svg is not None
        assert "<svg" in svg

    def test_render_fraction(self):
        """Test rendering a fraction."""
        renderer = MathRenderer()
        text, svg = renderer.render(r"$\frac{1}{2}$")
        assert svg is not None
        assert "<svg" in svg

    def test_render_mathcal(self):
        """Test rendering with mathcal command."""
        renderer = MathRenderer()
        text, svg = renderer.render(r"$\mathcal{I}^+$")
        assert svg is not None
        assert "<svg" in svg

    def test_render_complex_expression(self):
        """Test rendering a complex expression."""
        renderer = MathRenderer()
        text, svg = renderer.render(r"$x^2 + y^2 = r^2$")
        assert svg is not None
        assert "<svg" in svg

    def test_render_greek_letters(self):
        """Test rendering Greek letters."""
        renderer = MathRenderer()
        text, svg = renderer.render(r"$\alpha + \beta = \gamma$")
        assert svg is not None
        assert "<svg" in svg

    def test_render_removes_xml_declaration(self):
        """Test that XML declaration is removed from SVG."""
        renderer = MathRenderer()
        text, svg = renderer.render("$x$")
        assert svg is not None
        assert not svg.startswith("<?xml")

    def test_render_no_math(self):
        """Test rendering text without math."""
        renderer = MathRenderer()
        text, svg = renderer.render("Plain text")
        assert svg is None
        assert text == "Plain text"

    def test_render_empty_string(self):
        """Test rendering empty string."""
        renderer = MathRenderer()
        text, svg = renderer.render("")
        assert svg is None
        assert text == ""

    def test_render_with_text_around_math(self):
        """Test rendering when math is within text."""
        renderer = MathRenderer()
        text, svg = renderer.render("Formula: $x^2$")
        # Currently only extracts first math expression
        assert svg is not None
        assert "<svg" in svg


class TestMathRenderingDisabled:
    """Test math rendering when disabled."""

    def test_render_disabled_returns_none(self):
        """Test that disabled renderer returns None for SVG."""
        renderer = MathRenderer(enabled=False)
        text, svg = renderer.render("$x$")
        assert svg is None
        assert text == "$x$"

    def test_has_math_when_disabled(self):
        """Test has_math still works when disabled."""
        renderer = MathRenderer(enabled=False)
        # has_math should still detect math patterns
        assert renderer.has_math("$x$") is True


class TestMathRenderingErrors:
    """Test error handling in math rendering."""

    @pytest.mark.skipif(not ZIAMATH_AVAILABLE, reason="ziamath not available")
    def test_render_invalid_latex(self):
        """Test rendering with invalid LaTeX falls back gracefully."""
        renderer = MathRenderer()
        # Use an expression that might fail to render
        text, svg = renderer.render(r"$\invalidcommand{x}$")
        # Should fall back to plain text without $ delimiters
        if svg is None:
            assert text == r"\invalidcommand{x}"


class TestExtractPlainText:
    """Test plain text extraction."""

    def test_extract_plain_text_simple(self):
        """Test extracting plain text from simple math."""
        renderer = MathRenderer()
        plain = renderer.extract_plain_text("$x$")
        assert plain == "x"

    def test_extract_plain_text_complex(self):
        """Test extracting plain text from complex expression."""
        renderer = MathRenderer()
        plain = renderer.extract_plain_text("$x^2 + y^2$")
        assert plain == "x^2 + y^2"

    def test_extract_plain_text_with_surrounding_text(self):
        """Test extraction with text around math."""
        renderer = MathRenderer()
        plain = renderer.extract_plain_text("Formula: $E=mc^2$ is famous")
        assert plain == "Formula: E=mc^2 is famous"

    def test_extract_plain_text_no_math(self):
        """Test extraction from plain text."""
        renderer = MathRenderer()
        plain = renderer.extract_plain_text("Plain text")
        assert plain == "Plain text"

    def test_extract_plain_text_multiple_math(self):
        """Test extraction with multiple math expressions."""
        renderer = MathRenderer()
        plain = renderer.extract_plain_text("$x$ and $y$")
        assert plain == "x and y"


class TestMathRenderingIntegration:
    """Integration tests with TikZ parser and converter."""

    @pytest.mark.skipif(not ZIAMATH_AVAILABLE, reason="ziamath not available")
    def test_node_with_math(self):
        """Test rendering a node with math content."""
        from tikz2svg.parser.parser import TikzParser
        from tikz2svg.svg.converter import SVGConverter

        tikz_code = r"""
\begin{tikzpicture}
\node at (0,0) {$x^2$};
\end{tikzpicture}
"""
        parser = TikzParser()
        ast = parser.parse(tikz_code)
        converter = SVGConverter()
        svg = converter.convert(ast)

        assert svg is not None
        assert "<svg" in svg
        # Should contain embedded math SVG in a <g> element
        assert "<g transform=" in svg

    @pytest.mark.skipif(not ZIAMATH_AVAILABLE, reason="ziamath not available")
    def test_inline_node_with_math(self):
        """Test rendering inline node labels with math."""
        from tikz2svg.parser.parser import TikzParser
        from tikz2svg.svg.converter import SVGConverter

        tikz_code = r"""
\begin{tikzpicture}
\draw (0,0) -- (1,1) node[right] {$\alpha$};
\end{tikzpicture}
"""
        parser = TikzParser()
        ast = parser.parse(tikz_code)
        converter = SVGConverter()
        svg = converter.convert(ast)

        assert svg is not None
        assert "<svg" in svg
        # Should contain both path and embedded math SVG
        assert "<path" in svg
        assert "<g transform=" in svg

    @pytest.mark.skipif(not ZIAMATH_AVAILABLE, reason="ziamath not available")
    def test_multiple_nodes_with_math(self):
        """Test rendering multiple nodes with different math expressions."""
        from tikz2svg.parser.parser import TikzParser
        from tikz2svg.svg.converter import SVGConverter

        tikz_code = r"""
\begin{tikzpicture}
\node at (0,0) {$i^0$};
\node at (1,1) {$\mathcal{I}^+$};
\end{tikzpicture}
"""
        parser = TikzParser()
        ast = parser.parse(tikz_code)
        converter = SVGConverter()
        svg = converter.convert(ast)

        assert svg is not None
        assert "<svg" in svg
        # Should contain two embedded math SVGs
        assert svg.count("<g transform=") >= 2

    def test_node_without_math_fallback(self):
        """Test that nodes without math still render correctly."""
        from tikz2svg.parser.parser import TikzParser
        from tikz2svg.svg.converter import SVGConverter

        tikz_code = r"""
\begin{tikzpicture}
\node at (0,0) {Plain text};
\end{tikzpicture}
"""
        parser = TikzParser()
        ast = parser.parse(tikz_code)
        converter = SVGConverter()
        svg = converter.convert(ast)

        assert svg is not None
        assert "<svg" in svg
        # Should use regular text element
        assert "<text" in svg
        assert "Plain text" in svg
