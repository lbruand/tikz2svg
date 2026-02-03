"""Path rendering for TikZ to SVG conversion."""

from typing import List, Optional, Tuple

from ..parser.ast_nodes import Path


class PathRenderer:
    """Renders TikZ paths as SVG path data strings.

    Handles all path operations:
    - Lines (--), curves (..), control points
    - Arcs, circles, rectangles, grids
    - Orthogonal lines (|-, -|)
    - Path closing (cycle)
    """

    def __init__(self, coord_resolver, coord_transformer):
        """Initialize path renderer.

        Args:
            coord_resolver: CoordinateResolver for coordinate evaluation
            coord_transformer: CoordinateTransformer for coordinate math
        """
        self.coord_resolver = coord_resolver
        self.coord_transformer = coord_transformer

    def render_path(self, path: Path) -> str:
        """Convert TikZ Path AST to SVG path data string.

        Args:
            path: Path AST node with segments

        Returns:
            SVG path data (M, L, C, A, Z commands)
        """
        path_data = []
        current_pos = None

        for i, segment in enumerate(path.segments):
            # Handle operation types
            op = segment.operation

            if op == "cycle":
                path_data.append("Z")

            elif isinstance(op, dict):
                # Handle dict-based operations (arc, circle, controls)
                op_type = op.get("_type")

                if op_type == "arc":
                    arc_cmd = self.render_arc(op.get("spec", {}), current_pos)
                    if arc_cmd:
                        path_data.append(arc_cmd)

                elif op_type == "circle":
                    # Circle at current position
                    circle_spec = op.get("spec", {})
                    if current_pos and segment.destination:
                        # Circle at specific coordinate
                        center = self.coord_resolver.resolve(segment.destination, current_pos)
                    elif current_pos:
                        center = current_pos
                    else:
                        center = self.coord_transformer.tikz_to_svg(0, 0)

                    radius = (
                        self.coord_resolver.eval_value(circle_spec.get("radius", 1.0))
                        * self.coord_transformer.scale
                    )

                    # Draw circle as path (M, A, A, Z)
                    circle_cmds = self._render_circle_as_path(center, radius)
                    path_data.extend(circle_cmds)
                    current_pos = center

                elif op_type == "controls":
                    # Bezier curve with explicit control points
                    if segment.destination and current_pos:
                        dest = self.coord_resolver.resolve(segment.destination, current_pos)
                        controls = op.get("points", [])

                        curve_cmd = self._render_bezier(dest, controls, current_pos)
                        if curve_cmd:
                            path_data.append(curve_cmd)
                            current_pos = dest

            elif segment.destination:
                # Handle standard operations with destination
                coord = self.coord_resolver.resolve(segment.destination, current_pos)
                x, y = coord

                if op == "start":
                    path_data.append(f"M {x:.2f} {y:.2f}")
                elif op == "move":
                    # Move without drawing (for placing nodes without connecting lines)
                    path_data.append(f"M {x:.2f} {y:.2f}")
                elif op == "--":
                    path_data.append(f"L {x:.2f} {y:.2f}")
                elif op == "..":
                    # Curve (simplified as quadratic)
                    curve_cmd = self._render_simple_curve(x, y, current_pos)
                    path_data.append(curve_cmd)
                elif op in ("|-", "-|"):
                    # Orthogonal lines
                    ortho_cmds = self._render_orthogonal(op, x, y, current_pos)
                    path_data.extend(ortho_cmds)
                elif op == "rectangle":
                    rect_cmds = self._render_rectangle(x, y, current_pos)
                    path_data.extend(rect_cmds)
                elif op == "grid":
                    grid_cmds = self._render_grid(x, y, current_pos)
                    path_data.extend(grid_cmds)
                else:
                    # Default to line
                    path_data.append(f"L {x:.2f} {y:.2f}")

                # Update current position
                if segment.destination.system == "relative":
                    operator = segment.destination.modifiers.get("operator", "++")
                    if operator == "++":
                        current_pos = (x, y)
                else:
                    current_pos = (x, y)

        return " ".join(path_data)

    def render_arc(self, arc_spec: dict, current_pos: Optional[Tuple[float, float]]) -> str:
        """Convert TikZ arc specification to SVG arc command.

        Args:
            arc_spec: Arc specification dictionary
            current_pos: Current position for relative arc

        Returns:
            SVG arc command (A ...)
        """
        if not arc_spec or not current_pos:
            return ""

        format_type = arc_spec.get("format", "angles")

        if format_type == "angles":
            # (start:end:radius) format
            start_angle = self.coord_resolver.eval_value(arc_spec.get("start_angle", 0))
            end_angle = self.coord_resolver.eval_value(arc_spec.get("end_angle", 90))
            radius = (
                self.coord_resolver.eval_value(arc_spec.get("radius", 1.0))
                * self.coord_transformer.scale
            )

            # Calculate end point
            import math

            start_rad = math.radians(start_angle)
            end_rad = math.radians(end_angle)

            # Arc starts at current position
            dx = radius * (math.cos(end_rad) - math.cos(start_rad))
            dy = radius * (math.sin(end_rad) - math.sin(start_rad))

            end_x = current_pos[0] + dx * self.coord_transformer.scale
            end_y = current_pos[1] - dy * self.coord_transformer.scale

            # Large arc flag
            large_arc = 1 if abs(end_angle - start_angle) > 180 else 0
            sweep = 1 if end_angle > start_angle else 0

            return f"A {radius:.2f} {radius:.2f} 0 {large_arc} {sweep} {end_x:.2f} {end_y:.2f}"

        else:
            # Options format [start angle=..., end angle=..., radius=...]
            start_angle = self.coord_resolver.eval_value(arc_spec.get("start_angle", 0))
            end_angle = self.coord_resolver.eval_value(arc_spec.get("end_angle", 90))
            radius = (
                self.coord_resolver.eval_value(arc_spec.get("radius", 1.0))
                * self.coord_transformer.scale
            )

            import math

            end_rad = math.radians(end_angle)
            end_x = current_pos[0] + radius * math.cos(end_rad)
            end_y = current_pos[1] - radius * math.sin(end_rad)

            large_arc = 1 if abs(end_angle - start_angle) > 180 else 0
            sweep = 1

            return f"A {radius:.2f} {radius:.2f} 0 {large_arc} {sweep} {end_x:.2f} {end_y:.2f}"

    def _render_circle_as_path(self, center: Tuple[float, float], radius: float) -> List[str]:
        """Render circle as SVG path commands.

        Args:
            center: Circle center (x, y)
            radius: Circle radius

        Returns:
            List of path commands (M, A, A, Z)
        """
        cx, cy = center
        return [
            f"M {cx - radius:.2f} {cy}",
            f"A {radius:.2f} {radius:.2f} 0 1 0 {cx + radius:.2f} {cy}",
            f"A {radius:.2f} {radius:.2f} 0 1 0 {cx - radius:.2f} {cy}",
        ]

    def _render_bezier(
        self,
        dest: Tuple[float, float],
        controls: list,
        current_pos: Tuple[float, float],
    ) -> Optional[str]:
        """Render Bezier curve with control points.

        Args:
            dest: Destination point
            controls: List of control point coordinates
            current_pos: Current position

        Returns:
            SVG curve command (C or Q)
        """
        if len(controls) == 2:
            # Cubic Bezier
            c1 = self.coord_resolver.resolve(controls[0], current_pos)
            c2 = self.coord_resolver.resolve(controls[1], current_pos)
            return f"C {c1[0]:.2f} {c1[1]:.2f} {c2[0]:.2f} {c2[1]:.2f} {dest[0]:.2f} {dest[1]:.2f}"
        elif len(controls) == 1:
            # Quadratic Bezier
            c1 = self.coord_resolver.resolve(controls[0], current_pos)
            return f"Q {c1[0]:.2f} {c1[1]:.2f} {dest[0]:.2f} {dest[1]:.2f}"
        return None

    def _render_simple_curve(
        self, x: float, y: float, current_pos: Optional[Tuple[float, float]]
    ) -> str:
        """Render simple curve (no explicit controls).

        Args:
            x: Destination x
            y: Destination y
            current_pos: Current position

        Returns:
            SVG quadratic curve command
        """
        if current_pos:
            cx = (current_pos[0] + x) / 2
            cy = (current_pos[1] + y) / 2
            return f"Q {cx:.2f} {cy:.2f} {x:.2f} {y:.2f}"
        return f"L {x:.2f} {y:.2f}"

    def _render_orthogonal(
        self, op: str, x: float, y: float, current_pos: Optional[Tuple[float, float]]
    ) -> List[str]:
        """Render orthogonal lines (|- or -|).

        Args:
            op: Operation type ("|-" or "-|")
            x: Destination x
            y: Destination y
            current_pos: Current position

        Returns:
            List of line commands
        """
        if current_pos:
            if op == "|-":
                # Horizontal then vertical
                return [f"L {x:.2f} {current_pos[1]:.2f}", f"L {x:.2f} {y:.2f}"]
            else:
                # Vertical then horizontal
                return [f"L {current_pos[0]:.2f} {y:.2f}", f"L {x:.2f} {y:.2f}"]
        return [f"L {x:.2f} {y:.2f}"]

    def _render_rectangle(
        self, x: float, y: float, current_pos: Optional[Tuple[float, float]]
    ) -> List[str]:
        """Render rectangle from current position to destination.

        Args:
            x: Destination x
            y: Destination y
            current_pos: Current position (corner)

        Returns:
            List of path commands forming rectangle
        """
        if current_pos:
            x1, y1 = current_pos
            return [
                f"L {x:.2f} {y1:.2f}",
                f"L {x:.2f} {y:.2f}",
                f"L {x1:.2f} {y:.2f}",
                "Z",
            ]
        return []

    def _render_grid(
        self, x: float, y: float, current_pos: Optional[Tuple[float, float]]
    ) -> List[str]:
        """Render grid from current position to destination.

        Args:
            x: Destination x
            y: Destination y
            current_pos: Grid start position

        Returns:
            List of path commands forming grid lines
        """
        if not current_pos:
            return []

        x1, y1 = current_pos
        x2, y2 = x, y

        # Default step is 1cm = 28.35pt in TikZ
        step = self.coord_transformer.scale * 28.35

        commands = []

        # Draw vertical lines
        x_start = min(x1, x2)
        x_end = max(x1, x2)
        y_start = min(y1, y2)
        y_end = max(y1, y2)

        current_x = x_start
        while current_x <= x_end + 0.01:
            commands.append(f"M {current_x:.2f} {y_start:.2f}")
            commands.append(f"L {current_x:.2f} {y_end:.2f}")
            current_x += step

        # Draw horizontal lines
        current_y = y_start
        while current_y <= y_end + 0.01:
            commands.append(f"M {x_start:.2f} {current_y:.2f}")
            commands.append(f"L {x_end:.2f} {current_y:.2f}")
            current_y += step

        return commands
