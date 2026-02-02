"""Convert TikZ AST to SVG."""

from typing import Dict, Optional, Tuple

from ..parser.ast_nodes import *
from .geometry import CoordinateTransformer
from .styles import StyleConverter


class SVGConverter:
    """Converts TikZ AST to SVG document."""

    def __init__(self, scale: float = 28.35, width: int = 500, height: int = 500):
        """
        Initialize SVG converter.

        Args:
            scale: Points to pixels scale (28.35 = 1cm to pixels at 72dpi)
            width: Default canvas width
            height: Default canvas height
        """
        self.scale = scale
        self.width = width
        self.height = height
        self.coord_transformer = CoordinateTransformer(scale, width // 2, height // 2)
        self.style_converter = StyleConverter()
        self.named_coordinates: Dict[str, Tuple[float, float]] = {}

    def convert(self, ast: TikzPicture) -> str:
        """Convert TikZ AST to SVG string."""
        elements = []

        # Check if we need arrow markers
        has_arrows = self._check_for_arrows(ast)

        # Add marker definitions if needed
        if has_arrows:
            elements.append(self._create_arrow_markers())

        # Process all statements
        for stmt in ast.statements:
            svg_element = self.visit_statement(stmt)
            if svg_element:
                elements.append(svg_element)

        # Build SVG document
        svg_content = "\n  ".join(elements)
        svg_doc = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" height="{self.height}" viewBox="0 0 {self.width} {self.height}">
  {svg_content}
</svg>"""

        return svg_doc

    def _check_for_arrows(self, ast: TikzPicture) -> bool:
        """Check if any statements use arrows."""
        for stmt in ast.statements:
            if isinstance(stmt, DrawStatement) and "arrow" in stmt.options:
                return True
        return False

    def _create_arrow_markers(self) -> str:
        """Create SVG marker definitions for arrows."""
        return """<defs>
    <marker id="arrow-end" viewBox="0 0 10 10" refX="9" refY="5"
            markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="context-stroke"/>
    </marker>
    <marker id="arrow-start" viewBox="0 0 10 10" refX="1" refY="5"
            markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 10 0 L 0 5 L 10 10 z" fill="context-stroke"/>
    </marker>
  </defs>"""

    def visit_statement(self, stmt: ASTNode) -> Optional[str]:
        """Visit a statement node."""
        if isinstance(stmt, DrawStatement):
            return self.visit_draw_statement(stmt)
        elif isinstance(stmt, Node):
            return self.visit_node(stmt)
        elif isinstance(stmt, CoordinateDefinition):
            return self.visit_coordinate_definition(stmt)
        elif isinstance(stmt, Scope):
            return self.visit_scope(stmt)
        elif isinstance(stmt, ForeachLoop):
            return self.visit_foreach_loop(stmt)
        return None

    def visit_draw_statement(self, stmt: DrawStatement) -> str:
        """Convert draw statement to SVG path."""
        path_data = self.convert_path(stmt.path)
        style = self.style_converter.convert(stmt.options, stmt.command)

        # Check for arrows
        arrow_spec = stmt.options.get("arrow", "")
        marker_start = ""
        marker_end = ""

        if arrow_spec:
            if "<-" in arrow_spec:
                marker_start = ' marker-start="url(#arrow-start)"'
            if "->" in arrow_spec:
                marker_end = ' marker-end="url(#arrow-end)"'

        return f'<path d="{path_data}" style="{style}"{marker_start}{marker_end}/>'

    def convert_path(self, path: Path) -> str:
        """Convert TikZ path to SVG path data."""
        if not path.segments:
            return ""

        path_data = []
        current_pos = None

        for i, segment in enumerate(path.segments):
            # Handle operation types
            op = segment.operation

            if op == "cycle":
                path_data.append("Z")
                continue

            # Handle dict-based operations (arc, circle)
            if isinstance(op, dict):
                op_type = op.get("_type")

                if op_type == "arc":
                    arc_cmd = self.convert_arc(op.get("spec", {}), current_pos)
                    if arc_cmd:
                        path_data.append(arc_cmd)
                        # Update current_pos based on arc end point
                    continue

                elif op_type == "circle":
                    # Circle at current position
                    circle_spec = op.get("spec", {})
                    if current_pos and segment.destination:
                        # Circle at specific coordinate
                        center = self.evaluate_coordinate(segment.destination, current_pos)
                    elif current_pos:
                        center = current_pos
                    else:
                        center = self.coord_transformer.tikz_to_svg(0, 0)

                    radius = circle_spec.get("radius", 1.0) * self.coord_transformer.scale
                    # Draw circle as path (M, A, A, Z)
                    cx, cy = center
                    path_data.append(f"M {cx - radius:.2f} {cy}")
                    path_data.append(f"A {radius:.2f} {radius:.2f} 0 1 0 {cx + radius:.2f} {cy}")
                    path_data.append(f"A {radius:.2f} {radius:.2f} 0 1 0 {cx - radius:.2f} {cy}")
                    current_pos = center
                    continue

                elif op_type == "controls":
                    # Bezier curve with explicit control points
                    if segment.destination and current_pos:
                        dest = self.evaluate_coordinate(segment.destination, current_pos)
                        controls = op.get("points", [])
                        if len(controls) == 2:
                            # Cubic Bezier
                            c1 = self.evaluate_coordinate(controls[0], current_pos)
                            c2 = self.evaluate_coordinate(controls[1], current_pos)
                            path_data.append(
                                f"C {c1[0]:.2f} {c1[1]:.2f} {c2[0]:.2f} {c2[1]:.2f} {dest[0]:.2f} {dest[1]:.2f}"
                            )
                            current_pos = dest
                        elif len(controls) == 1:
                            # Quadratic Bezier
                            c1 = self.evaluate_coordinate(controls[0], current_pos)
                            path_data.append(
                                f"Q {c1[0]:.2f} {c1[1]:.2f} {dest[0]:.2f} {dest[1]:.2f}"
                            )
                            current_pos = dest
                    continue

            # Handle standard operations with destination
            if segment.destination:
                coord = self.evaluate_coordinate(segment.destination, current_pos)
                x, y = coord

                if op == "start":
                    # Starting point - move to start
                    path_data.append(f"M {x:.2f} {y:.2f}")
                elif op == "--":
                    # Line to
                    path_data.append(f"L {x:.2f} {y:.2f}")
                elif op == "..":
                    # Curve (simplified as quadratic for now)
                    if current_pos:
                        cx = (current_pos[0] + x) / 2
                        cy = (current_pos[1] + y) / 2
                        path_data.append(f"Q {cx:.2f} {cy:.2f} {x:.2f} {y:.2f}")
                    else:
                        path_data.append(f"L {x:.2f} {y:.2f}")
                elif op in ("|-", "-|"):
                    # Orthogonal lines
                    if current_pos:
                        if op == "|-":
                            # Horizontal then vertical
                            path_data.append(f"L {x:.2f} {current_pos[1]:.2f}")
                            path_data.append(f"L {x:.2f} {y:.2f}")
                        else:
                            # Vertical then horizontal
                            path_data.append(f"L {current_pos[0]:.2f} {y:.2f}")
                            path_data.append(f"L {x:.2f} {y:.2f}")
                    else:
                        path_data.append(f"L {x:.2f} {y:.2f}")
                elif op == "rectangle":
                    # Rectangle from current_pos to destination
                    if current_pos:
                        x1, y1 = current_pos
                        path_data.append(f"L {x:.2f} {y1:.2f}")
                        path_data.append(f"L {x:.2f} {y:.2f}")
                        path_data.append(f"L {x1:.2f} {y:.2f}")
                        path_data.append("Z")
                else:
                    # Default to line
                    path_data.append(f"L {x:.2f} {y:.2f}")

                current_pos = (x, y)

        if path.closed:
            path_data.append("Z")

        return " ".join(path_data)

    def convert_arc(
        self, arc_spec: Dict[str, any], current_pos: Optional[Tuple[float, float]] = None
    ) -> str:
        """Convert arc specification to SVG arc command."""
        if not arc_spec or not current_pos:
            return ""

        format_type = arc_spec.get("format", "angles")

        if format_type == "angles":
            # (start:end:radius) format
            start_angle = arc_spec.get("start_angle", 0)
            end_angle = arc_spec.get("end_angle", 90)
            radius = arc_spec.get("radius", 1.0) * self.coord_transformer.scale

            # Calculate end point
            import math

            start_rad = math.radians(start_angle)
            end_rad = math.radians(end_angle)

            # Arc starts at current position
            # End point relative to start
            dx = radius * (math.cos(end_rad) - math.cos(start_rad))
            dy = radius * (math.sin(end_rad) - math.sin(start_rad))

            end_x = current_pos[0] + dx * self.coord_transformer.scale
            end_y = current_pos[1] - dy * self.coord_transformer.scale  # Flip Y

            # Large arc flag
            large_arc = 1 if abs(end_angle - start_angle) > 180 else 0
            sweep = 1 if end_angle > start_angle else 0

            return f"A {radius:.2f} {radius:.2f} 0 {large_arc} {sweep} {end_x:.2f} {end_y:.2f}"

        else:
            # Options format [start angle=..., end angle=..., radius=...]
            start_angle = arc_spec.get("start_angle", 0)
            end_angle = arc_spec.get("end_angle", 90)
            radius = arc_spec.get("radius", 1.0) * self.coord_transformer.scale

            # Similar calculation as above
            import math

            end_rad = math.radians(end_angle)
            end_x = current_pos[0] + radius * math.cos(end_rad)
            end_y = current_pos[1] - radius * math.sin(end_rad)

            large_arc = 1 if abs(end_angle - start_angle) > 180 else 0
            sweep = 1

            return f"A {radius:.2f} {radius:.2f} 0 {large_arc} {sweep} {end_x:.2f} {end_y:.2f}"

    def evaluate_coordinate(
        self, coord: Coordinate, current_pos: Optional[Tuple[float, float]] = None
    ) -> Tuple[float, float]:
        """Evaluate a coordinate to (x, y) in SVG space."""
        if coord.system == "cartesian":
            x, y = coord.values[0], coord.values[1]
            return self.coord_transformer.tikz_to_svg(x, y)

        elif coord.system == "polar":
            angle, radius = coord.values[0], coord.values[1]
            x, y = self.coord_transformer.polar_to_cartesian(angle, radius)
            return self.coord_transformer.tikz_to_svg(x, y)

        elif coord.system == "named":
            if coord.name in self.named_coordinates:
                return self.named_coordinates[coord.name]
            else:
                # Unknown coordinate, return origin
                return self.coord_transformer.tikz_to_svg(0, 0)

        elif coord.system == "relative":
            # Relative to current position
            if current_pos and len(coord.values) >= 2:
                dx, dy = coord.values[0], coord.values[1]
                # Convert delta to SVG space
                dx_svg = dx * self.coord_transformer.scale
                dy_svg = -dy * self.coord_transformer.scale  # Flip Y
                return (current_pos[0] + dx_svg, current_pos[1] + dy_svg)
            else:
                return self.coord_transformer.tikz_to_svg(0, 0)

        # Default
        return self.coord_transformer.tikz_to_svg(0, 0)

    def visit_node(self, node: Node) -> str:
        """Convert node to SVG text element."""
        if node.position:
            x, y = self.evaluate_coordinate(node.position)
        else:
            x, y = self.coord_transformer.tikz_to_svg(0, 0)

        # Store named node position
        if node.name:
            self.named_coordinates[node.name] = (x, y)

        # Convert options to style
        style = self.style_converter.convert_text_style(node.options)

        return f'<text x="{x:.2f}" y="{y:.2f}" style="{style}" text-anchor="middle" dominant-baseline="middle">{node.text}</text>'

    def visit_coordinate_definition(self, coord_def: CoordinateDefinition) -> None:
        """Store named coordinate (doesn't produce SVG output)."""
        if coord_def.position:
            pos = self.evaluate_coordinate(coord_def.position)
            self.named_coordinates[coord_def.name] = pos
        return None

    def visit_scope(self, scope: Scope) -> str:
        """Convert scope to SVG group."""
        elements = []
        for stmt in scope.statements:
            element = self.visit_statement(stmt)
            if element:
                elements.append(element)

        if not elements:
            return ""

        # Apply scope options to group
        style = self.style_converter.convert(scope.options, "draw")
        content = "\n    ".join(elements)

        return f'<g style="{style}">\n    {content}\n  </g>'

    def visit_foreach_loop(self, loop: ForeachLoop) -> str:
        """Convert foreach loop to expanded statements."""
        # For Phase 1, simplified loop expansion
        # Full implementation in Phase 4
        elements = []
        for value in loop.values:
            for stmt in loop.body:
                # TODO: Substitute loop variable with value
                element = self.visit_statement(stmt)
                if element:
                    elements.append(element)

        return "\n  ".join(elements)
