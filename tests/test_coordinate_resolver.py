"""Unit tests for CoordinateResolver."""

import pytest

from tikz2svg.evaluator.math_eval import MathEvaluator
from tikz2svg.parser.ast_nodes import Coordinate
from tikz2svg.svg.coordinate_resolver import CoordinateResolver
from tikz2svg.svg.geometry import CoordinateTransformer


@pytest.fixture
def setup_resolver():
    """Create CoordinateResolver with dependencies."""
    evaluator = MathEvaluator()
    transformer = CoordinateTransformer(scale=1.0, offset_x=250, offset_y=250)
    named_coords = {"A": (100, 100), "B": (200, 200)}
    resolver = CoordinateResolver(transformer, evaluator, named_coords)
    return resolver, transformer, evaluator


def test_resolve_cartesian(setup_resolver):
    """Test resolving Cartesian coordinates (x, y)."""
    resolver, _, _ = setup_resolver

    coord = Coordinate(system="cartesian", values=[1, 2])
    result = resolver.resolve(coord)

    assert isinstance(result, tuple)
    assert len(result) == 2


def test_resolve_polar(setup_resolver):
    """Test resolving polar coordinates (angle:radius)."""
    resolver, _, _ = setup_resolver

    coord = Coordinate(system="polar", values=[0, 1])
    result = resolver.resolve(coord)

    assert isinstance(result, tuple)
    assert len(result) == 2


def test_resolve_named_found(setup_resolver):
    """Test resolving named coordinate that exists."""
    resolver, _, _ = setup_resolver

    coord = Coordinate(system="named", name="A")
    result = resolver.resolve(coord)

    assert result == (100, 100)


def test_resolve_named_not_found(setup_resolver):
    """Test resolving named coordinate that doesn't exist returns origin."""
    resolver, transformer, _ = setup_resolver

    coord = Coordinate(system="named", name="NonExistent")
    result = resolver.resolve(coord)

    # Should return origin (0, 0) in SVG space
    expected = transformer.tikz_to_svg(0, 0)
    assert result == expected


def test_resolve_relative_cartesian(setup_resolver):
    """Test resolving relative Cartesian coordinates ++(dx, dy)."""
    resolver, _, _ = setup_resolver

    current_pos = (100, 100)
    coord = Coordinate(
        system="relative", values=[1, 1], modifiers={"inner_system": "cartesian", "operator": "++"}
    )

    result = resolver.resolve(coord, current_pos)

    assert isinstance(result, tuple)
    assert len(result) == 2


def test_resolve_relative_polar(setup_resolver):
    """Test resolving relative polar coordinates ++(angle:radius)."""
    resolver, _, _ = setup_resolver

    current_pos = (100, 100)
    coord = Coordinate(
        system="relative",
        values=[0, 1],  # 0 degrees, radius 1
        modifiers={"inner_system": "polar", "operator": "++"},
    )

    result = resolver.resolve(coord, current_pos)

    assert isinstance(result, tuple)
    assert len(result) == 2
    # Position should be offset from current_pos
    assert result != current_pos


def test_resolve_relative_no_current_pos_with_values(setup_resolver):
    """Test relative coordinate without current position falls back to absolute."""
    resolver, transformer, _ = setup_resolver

    coord = Coordinate(
        system="relative", values=[1, 2], modifiers={"inner_system": "cartesian", "operator": "++"}
    )

    result = resolver.resolve(coord, current_pos=None)

    # Should treat as absolute coordinate
    expected = transformer.tikz_to_svg(1, 2)
    assert result == expected


def test_resolve_relative_no_current_pos_no_values(setup_resolver):
    """Test relative coordinate without current position and no values returns origin."""
    resolver, transformer, _ = setup_resolver

    coord = Coordinate(
        system="relative", values=[], modifiers={"inner_system": "cartesian", "operator": "++"}
    )

    result = resolver.resolve(coord, current_pos=None)

    # Should return origin
    expected = transformer.tikz_to_svg(0, 0)
    assert result == expected


def test_resolve_unknown_system(setup_resolver):
    """Test resolving coordinate with unknown system returns origin."""
    resolver, transformer, _ = setup_resolver

    coord = Coordinate(system="unknown_system", values=[1, 2])
    result = resolver.resolve(coord)

    # Should return origin as fallback
    expected = transformer.tikz_to_svg(0, 0)
    assert result == expected


def test_eval_value_number(setup_resolver):
    """Test evaluating numeric values."""
    resolver, _, _ = setup_resolver

    assert resolver.eval_value(42) == 42.0
    assert resolver.eval_value(3.14) == 3.14


def test_eval_value_string_expression(setup_resolver):
    """Test evaluating string expressions."""
    resolver, _, _ = setup_resolver

    result = resolver.eval_value("2+3")
    assert result == 5.0


def test_eval_value_string_number(setup_resolver):
    """Test evaluating string that's just a number."""
    resolver, _, _ = setup_resolver

    result = resolver.eval_value("42")
    assert result == 42.0


def test_eval_value_invalid_string(setup_resolver):
    """Test evaluating invalid string returns 0.0."""
    resolver, _, _ = setup_resolver

    result = resolver.eval_value("invalid_expression!!!")
    assert result == 0.0


def test_eval_value_non_numeric_type(setup_resolver):
    """Test evaluating non-numeric type returns 0.0."""
    resolver, _, _ = setup_resolver

    result = resolver.eval_value(None)
    assert result == 0.0

    result = resolver.eval_value([1, 2, 3])
    assert result == 0.0


def test_store_named(setup_resolver):
    """Test storing a named coordinate."""
    resolver, _, _ = setup_resolver

    # Store new coordinate
    resolver.store_named("C", (300, 300))

    # Verify it can be resolved
    coord = Coordinate(system="named", name="C")
    result = resolver.resolve(coord)

    assert result == (300, 300)


def test_store_named_overwrites(setup_resolver):
    """Test storing named coordinate overwrites existing one."""
    resolver, _, _ = setup_resolver

    # A initially exists at (100, 100)
    resolver.store_named("A", (999, 999))

    # Verify it was overwritten
    coord = Coordinate(system="named", name="A")
    result = resolver.resolve(coord)

    assert result == (999, 999)


def test_resolve_cartesian_with_expressions(setup_resolver):
    """Test Cartesian coordinates with expression values."""
    resolver, _, _ = setup_resolver

    coord = Coordinate(system="cartesian", values=["1+1", "2*2"])
    result = resolver.resolve(coord)

    # Should evaluate expressions: (2, 4)
    assert isinstance(result, tuple)
    assert len(result) == 2


def test_resolve_polar_with_expressions(setup_resolver):
    """Test polar coordinates with expression values."""
    resolver, _, _ = setup_resolver

    coord = Coordinate(system="polar", values=["45", "sqrt(2)"])
    result = resolver.resolve(coord)

    assert isinstance(result, tuple)
    assert len(result) == 2


def test_resolve_relative_unknown_inner_system(setup_resolver):
    """Test relative coordinate with unknown inner system."""
    resolver, _, _ = setup_resolver

    current_pos = (100, 100)
    coord = Coordinate(
        system="relative", values=[1, 1], modifiers={"inner_system": "unknown", "operator": "++"}
    )

    result = resolver.resolve(coord, current_pos)

    # Should fall back to (0, 0) delta, so result = current_pos
    assert isinstance(result, tuple)
