"""Convert TikZ AST to SVG."""
from typing import Dict, List, Tuple, Optional
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

        # Process all statements
        for stmt in ast.statements:
            svg_element = self.visit_statement(stmt)
            if svg_element:
                elements.append(svg_element)

        # Build SVG document
        svg_content = '\n  '.join(elements)
        svg_doc = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" height="{self.height}" viewBox="0 0 {self.width} {self.height}">
  {svg_content}
</svg>'''

        return svg_doc

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

        return f'<path d="{path_data}" style="{style}"/>'

    def convert_path(self, path: Path) -> str:
        """Convert TikZ path to SVG path data."""
        if not path.segments:
            return ""

        path_data = []
        current_pos = None

        for i, segment in enumerate(path.segments):
            if segment.operation == 'cycle':
                path_data.append('Z')
                continue

            if segment.destination:
                coord = self.evaluate_coordinate(segment.destination, current_pos)
                x, y = coord

                if segment.operation == 'start':
                    # Starting point - move to start
                    path_data.append(f'M {x:.2f} {y:.2f}')
                elif segment.operation == '--':
                    # Line to
                    path_data.append(f'L {x:.2f} {y:.2f}')
                elif segment.operation == '..':
                    # Curve (simplified as quadratic for now)
                    # In full implementation, would calculate Bezier control points
                    if current_pos:
                        cx = (current_pos[0] + x) / 2
                        cy = (current_pos[1] + y) / 2
                        path_data.append(f'Q {cx:.2f} {cy:.2f} {x:.2f} {y:.2f}')
                    else:
                        path_data.append(f'L {x:.2f} {y:.2f}')
                elif segment.operation in ('|-', '-|'):
                    # Orthogonal lines
                    if current_pos:
                        if segment.operation == '|-':
                            # Horizontal then vertical
                            path_data.append(f'L {x:.2f} {current_pos[1]:.2f}')
                            path_data.append(f'L {x:.2f} {y:.2f}')
                        else:
                            # Vertical then horizontal
                            path_data.append(f'L {current_pos[0]:.2f} {y:.2f}')
                            path_data.append(f'L {x:.2f} {y:.2f}')
                    else:
                        path_data.append(f'L {x:.2f} {y:.2f}')
                else:
                    # Default to line
                    path_data.append(f'L {x:.2f} {y:.2f}')

                current_pos = (x, y)

        if path.closed:
            path_data.append('Z')

        return ' '.join(path_data)

    def evaluate_coordinate(self, coord: Coordinate, current_pos: Optional[Tuple[float, float]] = None) -> Tuple[float, float]:
        """Evaluate a coordinate to (x, y) in SVG space."""
        if coord.system == 'cartesian':
            x, y = coord.values[0], coord.values[1]
            return self.coord_transformer.tikz_to_svg(x, y)

        elif coord.system == 'polar':
            angle, radius = coord.values[0], coord.values[1]
            x, y = self.coord_transformer.polar_to_cartesian(angle, radius)
            return self.coord_transformer.tikz_to_svg(x, y)

        elif coord.system == 'named':
            if coord.name in self.named_coordinates:
                return self.named_coordinates[coord.name]
            else:
                # Unknown coordinate, return origin
                return self.coord_transformer.tikz_to_svg(0, 0)

        elif coord.system == 'relative':
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
        style = self.style_converter.convert(scope.options, 'draw')
        content = '\n    '.join(elements)

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

        return '\n  '.join(elements)
