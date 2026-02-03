"""Coordinate resolution for TikZ to SVG conversion."""

from typing import Any, Dict, Optional, Tuple

from ..parser.ast_nodes import Coordinate


class CoordinateResolver:
    """Resolves TikZ coordinates to SVG (x, y) positions.

    Handles all coordinate types:
    - Cartesian: (x, y)
    - Polar: (angle:radius)
    - Named: (A), (node.north)
    - Relative: ++(dx, dy), +(dx, dy)
    """

    def __init__(
        self, coord_transformer, evaluator, named_coordinates: Dict[str, Tuple[float, float]]
    ):
        """Initialize coordinate resolver.

        Args:
            coord_transformer: CoordinateTransformer for TikZ to SVG conversion
            evaluator: MathEvaluator for expression evaluation
            named_coordinates: Dictionary mapping names to (x, y) positions
        """
        self.coord_transformer = coord_transformer
        self.evaluator = evaluator
        self.named_coordinates = named_coordinates

    def resolve(
        self, coord: Coordinate, current_pos: Optional[Tuple[float, float]] = None
    ) -> Tuple[float, float]:
        """Resolve any coordinate type to SVG (x, y) position.

        Args:
            coord: Coordinate AST node
            current_pos: Current position for relative coordinates

        Returns:
            Tuple of (x, y) in SVG coordinate space
        """
        if coord.system == "cartesian":
            return self._resolve_cartesian(coord)
        elif coord.system == "polar":
            return self._resolve_polar(coord)
        elif coord.system == "named":
            return self._resolve_named(coord)
        elif coord.system == "relative":
            return self._resolve_relative(coord, current_pos)
        else:
            # Default to origin
            return self.coord_transformer.tikz_to_svg(0, 0)

    def _resolve_cartesian(self, coord: Coordinate) -> Tuple[float, float]:
        """Resolve (x, y) cartesian coordinates.

        Args:
            coord: Coordinate with cartesian system

        Returns:
            SVG (x, y) position
        """
        x = self.eval_value(coord.values[0])
        y = self.eval_value(coord.values[1])
        return self.coord_transformer.tikz_to_svg(x, y)

    def _resolve_polar(self, coord: Coordinate) -> Tuple[float, float]:
        """Resolve (angle:radius) polar coordinates.

        Args:
            coord: Coordinate with polar system

        Returns:
            SVG (x, y) position
        """
        angle = self.eval_value(coord.values[0])
        radius = self.eval_value(coord.values[1])
        x, y = self.coord_transformer.polar_to_cartesian(angle, radius)
        return self.coord_transformer.tikz_to_svg(x, y)

    def _resolve_named(self, coord: Coordinate) -> Tuple[float, float]:
        """Resolve named coordinates like (A) or (node.north).

        Args:
            coord: Coordinate with named system

        Returns:
            SVG (x, y) position, or origin if not found
        """
        name = coord.name
        if name and name in self.named_coordinates:
            return self.named_coordinates[name]
        # Default to origin if not found
        return self.coord_transformer.tikz_to_svg(0, 0)

    def _resolve_relative(
        self, coord: Coordinate, current_pos: Optional[Tuple[float, float]]
    ) -> Tuple[float, float]:
        """Resolve relative coordinates: ++(dx, dy) or +(dx, dy).

        Args:
            coord: Coordinate with relative system
            current_pos: Current position to offset from

        Returns:
            SVG (x, y) position
        """
        if current_pos:
            inner_system = coord.modifiers.get("inner_system", "cartesian")

            if inner_system == "cartesian":
                dx = self.eval_value(coord.values[0])
                dy = self.eval_value(coord.values[1])
            elif inner_system == "polar":
                angle = self.eval_value(coord.values[0])
                radius = self.eval_value(coord.values[1])
                dx, dy = self.coord_transformer.polar_to_cartesian(angle, radius)
            else:
                dx, dy = 0, 0

            # Convert delta to SVG space
            dx_svg = dx * self.coord_transformer.scale
            dy_svg = -dy * self.coord_transformer.scale

            return (current_pos[0] + dx_svg, current_pos[1] + dy_svg)

        # If no current position, treat as absolute
        if coord.values:
            x = self.eval_value(coord.values[0])
            y = self.eval_value(coord.values[1])
            return self.coord_transformer.tikz_to_svg(x, y)

        return self.coord_transformer.tikz_to_svg(0, 0)

    def eval_value(self, value: Any) -> float:
        """Safely evaluate a numeric value or expression.

        Args:
            value: Number, string expression, or other value

        Returns:
            Float value
        """
        if isinstance(value, (int, float)):
            return float(value)

        if isinstance(value, str):
            try:
                return float(self.evaluator.evaluate(value))
            except Exception:
                # If evaluation fails, try direct conversion
                try:
                    return float(value)
                except Exception:
                    return 0.0

        return 0.0

    def store_named(self, name: str, position: Tuple[float, float]) -> None:
        """Store a named coordinate for later reference.

        Args:
            name: Coordinate name
            position: SVG (x, y) position
        """
        self.named_coordinates[name] = position
