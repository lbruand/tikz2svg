"""Convert TikZ AST to SVG."""

from typing import Dict, Optional, Tuple

from ..evaluator.context import EvaluationContext
from ..evaluator.math_eval import MathEvaluator
from ..parser.ast_nodes import *
from .coordinate_resolver import CoordinateResolver
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

        # Math evaluation
        self.context = EvaluationContext()
        self.evaluator = MathEvaluator(self.context)

        # Coordinate resolution
        self.named_coordinates: Dict[str, Tuple[float, float]] = {}
        self.coord_resolver = CoordinateResolver(
            self.coord_transformer, self.evaluator, self.named_coordinates
        )

    def _safe_evaluate(self, value, evaluator: Optional[MathEvaluator] = None):
        """Safely evaluate a value with fallback.

        Args:
            value: Value to evaluate (string expression or literal)
            evaluator: MathEvaluator to use (defaults to self.evaluator)

        Returns:
            Evaluated result, or original value if evaluation fails
        """
        if not isinstance(value, str):
            return value

        eval_instance = evaluator or self.evaluator
        try:
            return eval_instance.evaluate(value)
        except Exception:
            return value

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
        elif isinstance(stmt, MacroDefinition):
            return self.visit_macro_definition(stmt)
        elif isinstance(stmt, Layer):
            return self.visit_layer(stmt)
        elif isinstance(stmt, LayerDeclaration):
            return self.visit_layer_declaration(stmt)
        elif isinstance(stmt, LayerSet):
            return self.visit_layer_set(stmt)
        elif isinstance(stmt, StyleDefinition):
            return self.visit_style_definition(stmt)
        return None

    def visit_draw_statement(self, stmt: DrawStatement) -> str:
        """Convert draw statement to SVG path."""
        path_data = self.convert_path(stmt.path)

        # Evaluate options with variables
        evaluated_options = self._evaluate_options(stmt.options)
        style = self.style_converter.convert(evaluated_options, stmt.command)

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

            elif isinstance(op, dict):
                # Handle dict-based operations (arc, circle, controls)
                op_type = op.get("_type")

                if op_type == "arc":
                    arc_cmd = self.convert_arc(op.get("spec", {}), current_pos)
                    if arc_cmd:
                        path_data.append(arc_cmd)
                        # Update current_pos based on arc end point

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
                    cx, cy = center
                    path_data.append(f"M {cx - radius:.2f} {cy}")
                    path_data.append(f"A {radius:.2f} {radius:.2f} 0 1 0 {cx + radius:.2f} {cy}")
                    path_data.append(f"A {radius:.2f} {radius:.2f} 0 1 0 {cx - radius:.2f} {cy}")
                    current_pos = center

                elif op_type == "controls":
                    # Bezier curve with explicit control points
                    if segment.destination and current_pos:
                        dest = self.coord_resolver.resolve(segment.destination, current_pos)
                        controls = op.get("points", [])
                        if len(controls) == 2:
                            # Cubic Bezier
                            c1 = self.coord_resolver.resolve(controls[0], current_pos)
                            c2 = self.coord_resolver.resolve(controls[1], current_pos)
                            path_data.append(
                                f"C {c1[0]:.2f} {c1[1]:.2f} {c2[0]:.2f} {c2[1]:.2f} {dest[0]:.2f} {dest[1]:.2f}"
                            )
                            current_pos = dest
                        elif len(controls) == 1:
                            # Quadratic Bezier
                            c1 = self.coord_resolver.resolve(controls[0], current_pos)
                            path_data.append(
                                f"Q {c1[0]:.2f} {c1[1]:.2f} {dest[0]:.2f} {dest[1]:.2f}"
                            )
                            current_pos = dest

            elif segment.destination:
                # Handle standard operations with destination
                coord = self.coord_resolver.resolve(segment.destination, current_pos)
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
                elif op == "grid":
                    # Grid from current_pos to destination
                    # Draw horizontal and vertical lines
                    if current_pos:
                        x1, y1 = current_pos
                        x2, y2 = x, y

                        # Default step is 1cm = 28.35pt in TikZ coordinates
                        # In SVG space, that's scale * 28.35
                        step = self.coord_transformer.scale * 28.35

                        # Draw vertical lines
                        x_start = min(x1, x2)
                        x_end = max(x1, x2)
                        y_start = min(y1, y2)
                        y_end = max(y1, y2)

                        current_x = x_start
                        while current_x <= x_end + 0.01:
                            path_data.append(f"M {current_x:.2f} {y_start:.2f}")
                            path_data.append(f"L {current_x:.2f} {y_end:.2f}")
                            current_x += step

                        # Draw horizontal lines
                        current_y = y_start
                        while current_y <= y_end + 0.01:
                            path_data.append(f"M {x_start:.2f} {current_y:.2f}")
                            path_data.append(f"L {x_end:.2f} {current_y:.2f}")
                            current_y += step
                else:
                    # Default to line
                    path_data.append(f"L {x:.2f} {y:.2f}")

                # Update current position
                # For relative coordinates with '+' operator, don't update position
                # For '++' or absolute coordinates, do update
                if segment.destination.system == "relative":
                    operator = segment.destination.modifiers.get("operator", "++")
                    if operator == "++":
                        current_pos = (x, y)
                    # else: operator is '+', keep current_pos unchanged
                else:
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
            start_angle = self.coord_resolver.eval_value(arc_spec.get("start_angle", 0))
            end_angle = self.coord_resolver.eval_value(arc_spec.get("end_angle", 90))
            radius = (
                self.coord_resolver.eval_value(arc_spec.get("radius", 1.0))
                * self.coord_transformer.scale
            )

            # Similar calculation as above
            import math

            end_rad = math.radians(end_angle)
            end_x = current_pos[0] + radius * math.cos(end_rad)
            end_y = current_pos[1] - radius * math.sin(end_rad)

            large_arc = 1 if abs(end_angle - start_angle) > 180 else 0
            sweep = 1

            return f"A {radius:.2f} {radius:.2f} 0 {large_arc} {sweep} {end_x:.2f} {end_y:.2f}"

    def _evaluate_options(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate expressions in options dictionary.

        Args:
            options: Options dictionary with possible expressions

        Returns:
            Options with evaluated values
        """
        from lark import Token

        evaluated = {}
        for key, value in options.items():
            # If value is a Token, convert to string first
            if isinstance(value, Token):
                value = str(value.value)

            eval_succeeded = False

            # Try to evaluate if it looks like an expression
            if isinstance(value, str):
                # Check if it's a variable reference (single word that might be a variable)
                if value.isalpha() and value not in ["true", "false", "none"]:
                    # Try as variable first
                    try:
                        evaluated[key] = self.evaluator.evaluate(f"\\{value}")
                        eval_succeeded = True
                    except Exception:
                        pass

                # Try to evaluate if it has operators or backslash (only if not already evaluated)
                if not eval_succeeded and (
                    "\\" in value or any(op in value for op in ["+", "-", "*", "/", "("])
                ):
                    try:
                        evaluated[key] = self.evaluator.evaluate(value)
                        eval_succeeded = True
                    except Exception:
                        pass

            # Keep as-is if no evaluation succeeded
            if not eval_succeeded:
                evaluated[key] = value

        return evaluated

    def visit_node(self, node: Node) -> str:
        """Convert node to SVG text element."""
        if node.position:
            x, y = self.coord_resolver.resolve(node.position)
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
            pos = self.coord_resolver.resolve(coord_def.position)
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
        """
        Convert foreach loop to expanded statements.

        Handles:
        - Simple iteration over values
        - Multiple variables (paired values)
        - Evaluate clause for computed variables
        - Nested loops with proper scoping
        """
        elements = []

        # Prepare loop values
        num_vars = len(loop.variables)

        for value in loop.values:
            # Create child context for this iteration
            parent_context = self.context
            parent_evaluator = self.evaluator
            self.context = self.context.create_child_context()
            self.evaluator = MathEvaluator(self.context)

            try:
                # Set loop variable(s)
                if num_vars == 1:
                    # Single variable
                    var_name = loop.variables[0]
                    value_eval = self._safe_evaluate(value, parent_evaluator)
                    self.context.set_variable(var_name, value_eval)
                elif num_vars > 1 and isinstance(value, (tuple, list)):
                    # Multiple variables with paired values
                    for i, var_name in enumerate(loop.variables):
                        if i < len(value):
                            val = self._safe_evaluate(value[i], parent_evaluator)
                            self.context.set_variable(var_name, val)

                # Handle evaluate clause
                if loop.evaluate_clause:
                    eval_info = loop.evaluate_clause
                    target_var = eval_info["target"]
                    expression = eval_info["expression"]

                    # Evaluate the expression with current loop variable value
                    try:
                        result = self.evaluator.evaluate(expression)
                        self.context.set_variable(target_var, result)
                    except Exception:
                        pass

                # Visit body statements
                for stmt in loop.body:
                    element = self.visit_statement(stmt)
                    if element:
                        elements.append(element)

            finally:
                # Restore parent context
                self.context = parent_context
                self.evaluator = parent_evaluator

        return "\n  ".join(elements)

    def visit_macro_definition(self, macro: MacroDefinition) -> None:
        """
        Process macro definition.

        Stores variable in evaluation context.
        Does not produce SVG output.

        Args:
            macro: MacroDefinition node
        """
        # Evaluate the body expression
        try:
            value = self.evaluator.evaluate(macro.body)
            # Store in context
            self.context.set_variable(macro.name, value)
        except Exception:
            # If evaluation fails, store as-is
            self.context.set_variable(macro.name, macro.body)

        return None

    def visit_layer_declaration(self, layer_decl) -> None:
        """Process layer declaration (doesn't produce SVG output)."""
        # Could store layer info for ordering, but for now just acknowledge it
        return None

    def visit_layer_set(self, layer_set) -> None:
        """Process layer ordering (doesn't produce SVG output)."""
        # Could store layer ordering, but for now just acknowledge it
        return None

    def visit_layer(self, layer) -> str:
        """Convert layer environment to SVG group."""
        # For now, treat layers like scopes - just group the elements
        # In a full implementation, we'd reorder elements based on layer ordering
        elements = []
        for stmt in layer.statements:
            element = self.visit_statement(stmt)
            if element:
                elements.append(element)

        if not elements:
            return ""

        content = "\n    ".join(elements)
        return f'<g data-layer="{layer.name}">\n    {content}\n  </g>'

    def visit_style_definition(self, style_def) -> None:
        """Process style definition (doesn't produce SVG output)."""
        # Could store styles for later reference, but for now just acknowledge it
        return None
