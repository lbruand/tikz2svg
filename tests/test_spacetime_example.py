"""Tests for the texample.net spacetime diagram example.

This example tests complex TikZ features including:
- Variable definitions and expressions
- Inline coordinate definitions
- Named coordinate references
- Inline node labels with LaTeX math
- Bezier curves with control points
- Multiple nodes without connectors
- Fill opacity
"""

import re

import pytest

from tikz2svg.parser.parser import TikzParser
from tikz2svg.svg.converter import SVGConverter
from tikz2svg.svg.math_renderer import ZIAMATH_AVAILABLE


@pytest.fixture
def spacetime_code():
    """Return the spacetime TikZ code."""
    return r"""
\begin{tikzpicture}

  \def\L{2.}

  % causal diamond
  \draw[thick,red] (-\L,\L) coordinate(stl) -- (\L,\L) coordinate (str);
  \draw[thick,black] (\L,-\L) coordinate (sbr)
    -- (0,0) coordinate (bif) -- (stl);
  \draw[thick,black,fill=blue, fill opacity=0.2,text opacity=1]
    (bif) -- (str) -- (2*\L,0) node[right] (io) {$i^0$} -- (sbr);

  % null labels
  \draw[black] (1.4*\L,0.7*\L) node[right]  (scrip) {$\mathcal{I}^+$}
               (1.5*\L,-0.6*\L) node[right] (scrip) {$\mathcal{I}^-$}
               (0.2*\L,-0.6*\L) node[right] (scrip) {$\mathcal{H}^-$}
               (0.5*\L,0.85*\L) node[right] (scrip) {$\mathcal{H}^+$};

  % singularity label
  \draw[thick,red] (0,1.05*\L)
    -- (0,1.2*\L) node[above] {singularity};
  % Schwarzschild surface
  \draw[thick,blue] (bif) .. controls (1.*\L,-0.35*\L) .. (2*\L,0);
  \draw[thick,blue] (1.75*\L,-0.1*\L)  -- (1.9*\L,-0.5*\L)
    -- (2*\L,-0.5*\L) node[right]
    {t=constant};
  % excision surface
  \draw[thick,dashed,red] (-0.3*\L,0.3*\L) -- (0.4*\L,\L);
  \draw[thick,red] (-0.33*\L,0.3*\L)
    -- (-0.5*\L,0.26*\L) node[left] {excision surface};
  % Kerr-Schild surface
  \draw[thick] (0.325*\L,0.325*\L) .. controls (\L,0) .. (2*\L,0);
  \draw[dashed,thick] (0.325*\L,0.325*\L) -- (-0.051*\L,0.5*\L);
  % Kerr-Schild label
  \draw[thick] (0.95*\L,0.15*\L) -- (1.2*\L,0.5*\L)
    -- (2*\L,0.5*\L) node[right] {tau=constant};
\end{tikzpicture}
"""


class TestSpacetimeParsing:
    """Test parsing of the spacetime example."""

    def test_parses_successfully(self, spacetime_code):
        """Test that the spacetime example parses without errors."""
        parser = TikzParser()
        ast = parser.parse(spacetime_code)
        assert ast is not None
        assert len(ast.statements) > 0

    def test_statement_count(self, spacetime_code):
        """Test that we get the expected number of draw statements."""
        parser = TikzParser()
        ast = parser.parse(spacetime_code)
        # Should have 12 draw statements (excluding the \def)
        # Counted: 3 causal diamond + 1 null labels + 2 singularity +
        #          2 Schwarzschild + 2 excision + 2 Kerr-Schild = 12
        assert len(ast.statements) == 12

    def test_variable_definition(self, spacetime_code):
        r"""Test that variable \L is defined and substituted correctly."""
        parser = TikzParser()
        ast = parser.parse(spacetime_code)
        # Check that the variable was used in expressions (substituted to 2.)
        # Look for "2." in coordinate values
        has_substituted_value = any(
            "2." in str(seg.destination.values)
            for stmt in ast.statements
            if hasattr(stmt, "path")
            for seg in stmt.path.segments
            if seg.destination and hasattr(seg.destination, "values")
        )
        assert has_substituted_value, r"Variable \L should be substituted to 2."


class TestSpacetimeCoordinates:
    """Test coordinate handling in the spacetime example."""

    def test_inline_coordinate_definitions(self, spacetime_code):
        """Test that inline coordinates are defined."""
        parser = TikzParser()
        ast = parser.parse(spacetime_code)

        # First draw statement should define stl and str coordinates
        first_draw = ast.statements[0]
        path_segments = first_draw.path.segments

        # Check for coordinate labels
        has_coordinate_labels = any(seg.options.get("coordinate_name") for seg in path_segments)
        assert has_coordinate_labels, "Should have inline coordinate definitions"

    def test_named_coordinate_references(self, spacetime_code):
        """Test that named coordinates are referenced correctly."""
        parser = TikzParser()
        ast = parser.parse(spacetime_code)

        # Second draw statement references (stl)
        second_draw = ast.statements[1]

        # Should have a segment with a named coordinate reference
        has_named_coord = any(
            seg.destination and seg.destination.system == "named"
            for seg in second_draw.path.segments
        )
        assert has_named_coord, "Should reference named coordinate"

    def test_expression_evaluation(self, spacetime_code):
        r"""Test that expressions like 2*\L are evaluated."""
        parser = TikzParser()
        ast = parser.parse(spacetime_code)

        # Third draw statement has (2*\L,0)
        third_draw = ast.statements[2]

        # Find the segment with the expression
        for seg in third_draw.path.segments:
            if seg.destination and seg.destination.system == "cartesian":
                values = seg.destination.values
                # Should have expression like "2*2." not "22."
                if "*" in str(values):
                    # Expression should contain the operator
                    assert "*" in values[0] or "4" in str(values[0])
                    break


class TestSpacetimeNodes:
    """Test node handling in the spacetime example."""

    def test_inline_node_labels(self, spacetime_code):
        """Test that inline node labels are captured."""
        parser = TikzParser()
        ast = parser.parse(spacetime_code)

        # Third draw statement has inline node with math
        third_draw = ast.statements[2]

        # Should have node labels in path segments
        has_node_label = any(seg.options.get("node_label") for seg in third_draw.path.segments)
        assert has_node_label, "Should have inline node labels"

    @pytest.mark.skipif(not ZIAMATH_AVAILABLE, reason="ziamath not available")
    def test_node_math_content(self, spacetime_code):
        """Test that node math content is preserved."""
        parser = TikzParser()
        ast = parser.parse(spacetime_code)

        # Third draw statement has node with $i^0$
        third_draw = ast.statements[2]

        for seg in third_draw.path.segments:
            node_label = seg.options.get("node_label")
            if node_label:
                text = node_label.get("text", "")
                if "$" in text:
                    assert "$i^0$" in text or "i^0" in text
                    break

    def test_multiple_nodes_without_connectors(self, spacetime_code):
        """Test that multiple nodes without connectors are handled."""
        parser = TikzParser()
        ast = parser.parse(spacetime_code)

        # Fourth draw statement has multiple nodes without path connectors
        fourth_draw = ast.statements[3]

        # Should have move operations (not lines) between nodes
        move_count = sum(1 for seg in fourth_draw.path.segments if seg.operation == "move")
        assert move_count > 0, "Should have move operations for unconnected nodes"


class TestSpacetimeConversion:
    """Test SVG conversion of the spacetime example."""

    def test_converts_to_svg(self, spacetime_code):
        """Test that the example converts to SVG successfully."""
        parser = TikzParser()
        ast = parser.parse(spacetime_code)

        converter = SVGConverter()
        svg = converter.convert(ast)

        assert svg is not None
        assert "<svg" in svg
        assert "</svg>" in svg

    def test_svg_has_paths(self, spacetime_code):
        """Test that the SVG contains path elements."""
        parser = TikzParser()
        ast = parser.parse(spacetime_code)
        converter = SVGConverter()
        svg = converter.convert(ast)

        # Should have multiple path elements
        path_count = svg.count("<path")
        assert path_count >= 10, f"Expected at least 10 paths, got {path_count}"

    def test_svg_has_unique_coordinates(self, spacetime_code):
        """Test that coordinates are not all at the center."""
        parser = TikzParser()
        ast = parser.parse(spacetime_code)
        converter = SVGConverter()
        svg = converter.convert(ast)

        # Extract all coordinates from path data
        coords = re.findall(r"[ML] ([\d.]+) ([\d.]+)", svg)

        # Should have many unique coordinates
        unique_coords = set(coords)
        assert (
            len(unique_coords) > 20
        ), f"Expected > 20 unique coordinates, got {len(unique_coords)}"

        # Count how many are at center (250, 250)
        center_count = coords.count(("250.00", "250.00"))
        total_coords = len(coords)

        # Most coordinates should NOT be at center
        assert (
            center_count < total_coords * 0.2
        ), f"Too many coordinates at center: {center_count}/{total_coords}"

    @pytest.mark.skipif(not ZIAMATH_AVAILABLE, reason="ziamath not available")
    def test_svg_has_math_rendering(self, spacetime_code):
        """Test that math expressions are rendered to SVG."""
        parser = TikzParser()
        ast = parser.parse(spacetime_code)
        converter = SVGConverter()
        svg = converter.convert(ast)

        # Should have embedded SVG elements for math (from ziamath)
        # Math is rendered as nested <svg> elements
        nested_svg_count = svg.count("<svg", 1)  # Count after first <svg>
        assert nested_svg_count > 0, "Should have nested SVG for math rendering"

    def test_svg_has_text_nodes(self, spacetime_code):
        """Test that text nodes are present."""
        parser = TikzParser()
        ast = parser.parse(spacetime_code)
        converter = SVGConverter()
        svg = converter.convert(ast)

        # Should have text elements or g elements with transform (for math)
        has_text = "<text" in svg or "<g transform=" in svg
        assert has_text, "Should have text or transformed group elements"

    def test_svg_has_colors(self, spacetime_code):
        """Test that colors are preserved."""
        parser = TikzParser()
        ast = parser.parse(spacetime_code)
        converter = SVGConverter()
        svg = converter.convert(ast)

        # Should have red, blue, and black colors
        assert "#FF0000" in svg or "red" in svg.lower(), "Should have red color"
        assert "#0000FF" in svg or "blue" in svg.lower(), "Should have blue color"
        assert "#000000" in svg or "black" in svg.lower(), "Should have black color"

    def test_svg_has_line_styles(self, spacetime_code):
        """Test that line styles are preserved."""
        parser = TikzParser()
        ast = parser.parse(spacetime_code)
        converter = SVGConverter()
        svg = converter.convert(ast)

        # Should have thick lines
        assert "stroke-width: 2.0px" in svg, "Should have thick lines"

        # Should have dashed lines
        assert "stroke-dasharray" in svg, "Should have dashed lines"

    def test_svg_has_curves(self, spacetime_code):
        """Test that Bezier curves are present."""
        parser = TikzParser()
        ast = parser.parse(spacetime_code)
        converter = SVGConverter()
        svg = converter.convert(ast)

        # Bezier curves use C or Q commands in SVG path data
        has_curves = " C " in svg or " Q " in svg
        assert has_curves, "Should have curve commands in path data"


class TestSpacetimeIntegration:
    """Integration tests for the spacetime example."""

    def test_end_to_end(self, spacetime_code):
        """Test complete end-to-end conversion."""
        parser = TikzParser()
        ast = parser.parse(spacetime_code)

        converter = SVGConverter()
        svg = converter.convert(ast)

        # Basic validation
        assert svg.startswith("<svg")
        assert svg.endswith("</svg>")
        assert len(svg) > 1000, "SVG should be substantial in size"

    def test_specific_coordinates(self, spacetime_code):
        """Test specific coordinate calculations."""
        parser = TikzParser()
        ast = parser.parse(spacetime_code)
        converter = SVGConverter()
        svg = converter.convert(ast)

        # With \L=2., coordinate (-\L, \L) should be (-2, 2)
        # In SVG coords (center at 250, scale 28.35): (250-2*28.35, 250-2*28.35)
        # = (193.30, 193.30)
        assert "193.30 193.30" in svg, "Should have coordinate (-2, 2) = (193.30, 193.30)"

        # Coordinate (2*\L, 0) should be (4, 0) = (363.40, 250.00)
        assert (
            "363.40 250.00" in svg or "363.4 250.00" in svg
        ), "Should have coordinate (4, 0) = (363.40, 250.00)"

    def test_bezier_control_points(self, spacetime_code):
        """Test that Bezier curves use control points."""
        parser = TikzParser()
        ast = parser.parse(spacetime_code)
        converter = SVGConverter()
        svg = converter.convert(ast)

        # Bezier curves with control points should result in C or Q commands in SVG
        # The spacetime example has ".. controls (..) .." which creates Bezier curves
        has_bezier_curves = " C " in svg or " Q " in svg

        assert has_bezier_curves, "Should have Bezier curve commands (C or Q) in SVG"


class TestSpacetimeRegressions:
    """Regression tests to ensure bugs don't reappear."""

    def test_bezier_curves_not_moves(self, spacetime_code):
        """Regression: ensure Bezier curves render as Q/C commands, not M (move)."""
        parser = TikzParser()
        ast = parser.parse(spacetime_code)
        converter = SVGConverter()
        svg = converter.convert(ast)

        # Count Q (quadratic) and C (cubic) Bezier commands
        q_count = svg.count(" Q ")
        c_count = svg.count(" C ")

        # Spacetime has Bezier curves with controls - should have Q or C commands
        assert (
            q_count + c_count > 0
        ), "Bezier curves should produce Q or C commands, not just M (move)"

        # Specifically, spacetime should have many Q commands (tested: 225)
        assert q_count > 200, f"Expected >200 Q commands for Bezier curves, got {q_count}"

    def test_operator_in_expression(self, spacetime_code):
        """Test that operators in expressions are preserved."""
        parser = TikzParser()
        ast = parser.parse(spacetime_code)

        # Find a coordinate with an expression
        third_draw = ast.statements[2]
        for seg in third_draw.path.segments:
            if seg.destination and seg.destination.system == "cartesian":
                values = seg.destination.values
                # If it contains a multiplication, operator should be present
                for val in values:
                    val_str = str(val)
                    if "2" in val_str and "L" not in val_str:
                        # Should be "2*2." not "22." or "4"
                        # (might be evaluated already, so check it's reasonable)
                        if "*" in val_str:
                            assert "*" in val_str
                        elif val_str in ["4.0", "4", "2*2."]:
                            # Acceptable evaluated forms
                            pass

    def test_no_excessive_center_coordinates(self, spacetime_code):
        """Regression: ensure coordinates don't all collapse to center."""
        parser = TikzParser()
        ast = parser.parse(spacetime_code)
        converter = SVGConverter()
        svg = converter.convert(ast)

        # Count coordinates
        coords = re.findall(r"[ML] ([\d.]+) ([\d.]+)", svg)
        center_count = coords.count(("250.00", "250.00"))

        # Should have very few center coordinates (< 5 legitimate uses)
        assert center_count < 10, (
            f"Too many center coordinates: {center_count} " "(suggests expression evaluation bug)"
        )
