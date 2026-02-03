"""Unit tests for PathRenderer."""

import pytest
from tikz2svg.svg.path_renderer import PathRenderer
from tikz2svg.svg.coordinate_resolver import CoordinateResolver
from tikz2svg.svg.geometry import CoordinateTransformer
from tikz2svg.evaluator.math_eval import MathEvaluator
from tikz2svg.parser.ast_nodes import Path, PathSegment, Coordinate


@pytest.fixture
def setup_renderer():
    """Create PathRenderer with dependencies."""
    evaluator = MathEvaluator()
    transformer = CoordinateTransformer(scale=1.0, offset_x=250, offset_y=250)
    resolver = CoordinateResolver(transformer, evaluator, {})
    renderer = PathRenderer(resolver, transformer)
    return renderer, resolver, transformer


def test_render_simple_line(setup_renderer):
    """Test rendering a simple line path."""
    renderer, resolver, transformer = setup_renderer

    path = Path(
        segments=[
            PathSegment(
                operation="start",
                destination=Coordinate(system="cartesian", values=[0, 0])
            ),
            PathSegment(
                operation="--",
                destination=Coordinate(system="cartesian", values=[1, 1])
            ),
        ]
    )

    result = renderer.render_path(path)
    assert "M" in result
    assert "L" in result


def test_render_empty_path(setup_renderer):
    """Test rendering an empty path."""
    renderer, _, _ = setup_renderer

    path = Path(segments=[])
    result = renderer.render_path(path)
    assert result == ""


def test_render_cycle(setup_renderer):
    """Test path with cycle (closed path)."""
    renderer, _, _ = setup_renderer

    path = Path(
        segments=[
            PathSegment(
                operation="start",
                destination=Coordinate(system="cartesian", values=[0, 0])
            ),
            PathSegment(
                operation="--",
                destination=Coordinate(system="cartesian", values=[1, 0])
            ),
            PathSegment(operation="cycle", destination=None),
        ]
    )

    result = renderer.render_path(path)
    assert "Z" in result


def test_render_circle_as_path(setup_renderer):
    """Test circle rendering as path."""
    renderer, _, _ = setup_renderer

    center = (100, 100)
    radius = 50

    result = renderer._render_circle_as_path(center, radius)

    assert len(result) == 3
    assert result[0].startswith("M")
    assert result[1].startswith("A")
    assert result[2].startswith("A")


def test_render_circle_operation(setup_renderer):
    """Test circle operation in path."""
    renderer, _, _ = setup_renderer

    path = Path(
        segments=[
            PathSegment(
                operation="start",
                destination=Coordinate(system="cartesian", values=[0, 0])
            ),
            PathSegment(
                operation={"_type": "circle", "spec": {"radius": 1.0}},
                destination=None
            ),
        ]
    )

    result = renderer.render_path(path)
    assert "M" in result
    assert "A" in result


def test_render_bezier_cubic(setup_renderer):
    """Test cubic Bezier curve with two control points."""
    renderer, _, _ = setup_renderer

    current_pos = (0, 0)
    dest = (100, 100)
    controls = [
        Coordinate(system="cartesian", values=[30, 30]),
        Coordinate(system="cartesian", values=[70, 70]),
    ]

    result = renderer._render_bezier(dest, controls, current_pos)

    assert result is not None
    assert result.startswith("C")
    # Verify it has 6 coordinate values (2 control points + 1 destination)
    parts = result.split()
    assert len(parts) == 7  # C + 6 numbers


def test_render_bezier_quadratic(setup_renderer):
    """Test quadratic Bezier curve with one control point."""
    renderer, _, _ = setup_renderer

    current_pos = (0, 0)
    dest = (100, 100)
    controls = [Coordinate(system="cartesian", values=[50, 50])]

    result = renderer._render_bezier(dest, controls, current_pos)

    assert result is not None
    assert result.startswith("Q")
    # Verify it has 4 coordinate values (1 control point + 1 destination)
    parts = result.split()
    assert len(parts) == 5  # Q + 4 numbers


def test_render_bezier_no_controls(setup_renderer):
    """Test Bezier with no control points returns None."""
    renderer, _, _ = setup_renderer

    current_pos = (0, 0)
    dest = (100, 100)
    controls = []

    result = renderer._render_bezier(dest, controls, current_pos)
    assert result is None


def test_render_simple_curve(setup_renderer):
    """Test simple curve rendering (.. operation)."""
    renderer, _, _ = setup_renderer

    current_pos = (0, 0)
    x, y = 100, 100

    result = renderer._render_simple_curve(x, y, current_pos)

    assert result.startswith("Q")
    # Control point should be midpoint
    assert "50" in result


def test_render_simple_curve_no_current_pos(setup_renderer):
    """Test simple curve falls back to line without current position."""
    renderer, _, _ = setup_renderer

    result = renderer._render_simple_curve(100, 100, None)
    assert result.startswith("L")


def test_render_orthogonal_horizontal_vertical(setup_renderer):
    """Test orthogonal line |- (horizontal then vertical)."""
    renderer, _, _ = setup_renderer

    current_pos = (0, 0)
    x, y = 100, 100

    result = renderer._render_orthogonal("|-", x, y, current_pos)

    assert len(result) == 2
    assert result[0].startswith("L")
    assert result[1].startswith("L")
    # First move horizontal (y stays 0), then vertical
    assert "100.00 0.00" in result[0]
    assert "100.00 100.00" in result[1]


def test_render_orthogonal_vertical_horizontal(setup_renderer):
    """Test orthogonal line -| (vertical then horizontal)."""
    renderer, _, _ = setup_renderer

    current_pos = (0, 0)
    x, y = 100, 100

    result = renderer._render_orthogonal("-|", x, y, current_pos)

    assert len(result) == 2
    # First move vertical (x stays 0), then horizontal
    assert "0.00 100.00" in result[0]
    assert "100.00 100.00" in result[1]


def test_render_orthogonal_no_current_pos(setup_renderer):
    """Test orthogonal line without current position falls back to line."""
    renderer, _, _ = setup_renderer

    result = renderer._render_orthogonal("|-", 100, 100, None)

    assert len(result) == 1
    assert result[0].startswith("L")


def test_render_rectangle(setup_renderer):
    """Test rectangle rendering."""
    renderer, _, _ = setup_renderer

    current_pos = (0, 0)
    x, y = 100, 100

    result = renderer._render_rectangle(x, y, current_pos)

    assert len(result) == 4
    assert result[0].startswith("L")  # Top edge
    assert result[1].startswith("L")  # Right edge
    assert result[2].startswith("L")  # Bottom edge
    assert result[3] == "Z"  # Close path


def test_render_rectangle_no_current_pos(setup_renderer):
    """Test rectangle without current position returns empty."""
    renderer, _, _ = setup_renderer

    result = renderer._render_rectangle(100, 100, None)
    assert result == []


def test_render_grid(setup_renderer):
    """Test grid rendering."""
    renderer, _, _ = setup_renderer

    current_pos = (0, 0)
    x, y = 100, 100

    result = renderer._render_grid(x, y, current_pos)

    # Grid should have multiple M and L commands for lines
    assert len(result) > 0
    assert any("M" in cmd for cmd in result)
    assert any("L" in cmd for cmd in result)


def test_render_grid_no_current_pos(setup_renderer):
    """Test grid without current position returns empty."""
    renderer, _, _ = setup_renderer

    result = renderer._render_grid(100, 100, None)
    assert result == []


def test_render_arc_angles_format(setup_renderer):
    """Test arc with angles format (start:end:radius)."""
    renderer, _, _ = setup_renderer

    arc_spec = {
        "format": "angles",
        "start_angle": 0,
        "end_angle": 90,
        "radius": 50,
    }
    current_pos = (100, 100)

    result = renderer.render_arc(arc_spec, current_pos)

    assert result.startswith("A")
    assert "50" in result  # radius


def test_render_arc_options_format(setup_renderer):
    """Test arc with options format."""
    renderer, _, _ = setup_renderer

    arc_spec = {
        "format": "options",
        "start_angle": 0,
        "end_angle": 180,
        "radius": 30,
    }
    current_pos = (100, 100)

    result = renderer.render_arc(arc_spec, current_pos)

    assert result.startswith("A")
    assert "30" in result


def test_render_arc_no_current_pos(setup_renderer):
    """Test arc without current position returns empty."""
    renderer, _, _ = setup_renderer

    arc_spec = {"format": "angles", "start_angle": 0, "end_angle": 90, "radius": 50}

    result = renderer.render_arc(arc_spec, None)
    assert result == ""


def test_render_arc_no_spec(setup_renderer):
    """Test arc with no specification returns empty."""
    renderer, _, _ = setup_renderer

    result = renderer.render_arc({}, (100, 100))
    assert result == ""


def test_render_controls_operation(setup_renderer):
    """Test controls operation (Bezier with explicit control points)."""
    renderer, _, _ = setup_renderer

    path = Path(
        segments=[
            PathSegment(
                operation="start",
                destination=Coordinate(system="cartesian", values=[0, 0])
            ),
            PathSegment(
                operation={
                    "_type": "controls",
                    "points": [
                        Coordinate(system="cartesian", values=[30, 30]),
                        Coordinate(system="cartesian", values=[70, 70]),
                    ],
                },
                destination=Coordinate(system="cartesian", values=[100, 100])
            ),
        ]
    )

    result = renderer.render_path(path)
    assert "M" in result
    assert "C" in result  # Cubic Bezier


def test_render_curve_operation(setup_renderer):
    """Test .. curve operation."""
    renderer, _, _ = setup_renderer

    path = Path(
        segments=[
            PathSegment(
                operation="start",
                destination=Coordinate(system="cartesian", values=[0, 0])
            ),
            PathSegment(
                operation="..",
                destination=Coordinate(system="cartesian", values=[100, 100])
            ),
        ]
    )

    result = renderer.render_path(path)
    assert "M" in result
    assert "Q" in result  # Quadratic curve


def test_render_rectangle_operation(setup_renderer):
    """Test rectangle operation."""
    renderer, _, _ = setup_renderer

    path = Path(
        segments=[
            PathSegment(
                operation="start",
                destination=Coordinate(system="cartesian", values=[0, 0])
            ),
            PathSegment(
                operation="rectangle",
                destination=Coordinate(system="cartesian", values=[100, 100])
            ),
        ]
    )

    result = renderer.render_path(path)
    assert "M" in result
    assert "L" in result
    assert "Z" in result


def test_render_grid_operation(setup_renderer):
    """Test grid operation."""
    renderer, _, _ = setup_renderer

    path = Path(
        segments=[
            PathSegment(
                operation="start",
                destination=Coordinate(system="cartesian", values=[0, 0])
            ),
            PathSegment(
                operation="grid",
                destination=Coordinate(system="cartesian", values=[100, 100])
            ),
        ]
    )

    result = renderer.render_path(path)
    # Grid should produce multiple move and line commands
    assert result.count("M") > 1
    assert result.count("L") > 1
