"""Convert TikZ AST to SVG."""

from typing import Tuple

from ..evaluator.context import EvaluationContext
from ..evaluator.math_eval import MathEvaluator
from ..parser.ast_nodes import *
from .coordinate_resolver import CoordinateResolver
from .geometry import CoordinateTransformer
from .loop_expander import ForeachLoopExpander
from .math_renderer import MathRenderer
from .option_processor import OptionProcessor
from .path_renderer import PathRenderer
from .string_evaluator import StringEvaluator
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

        # String evaluation
        self.string_evaluator = StringEvaluator(self.context)

        # Math rendering
        self.math_renderer = MathRenderer()

        # Coordinate resolution
        self.named_coordinates: Dict[str, Tuple[float, float]] = {}
        self.coord_resolver = CoordinateResolver(
            self.coord_transformer, self.evaluator, self.named_coordinates
        )

        # Option processing
        self.option_processor = OptionProcessor(self.evaluator)

        # Path rendering
        self.path_renderer = PathRenderer(self.coord_resolver, self.coord_transformer)

        # Loop expansion
        self.loop_expander = ForeachLoopExpander(self.option_processor)

    def convert(self, ast: TikzPicture) -> str:
        """Convert TikZ AST to SVG string."""
        elements = []

        # Check if we need arrow markers
        has_arrows = self._check_for_arrows(ast)

        # Add marker definitions if needed
        if has_arrows:
            elements.append(self._create_arrow_markers())

        # Process all statements
        elements.extend(
            svg_element for stmt in ast.statements if (svg_element := self.visit_statement(stmt))
        )

        # Build SVG document
        svg_content = "\n  ".join(elements)
        svg_doc = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" height="{self.height}" viewBox="0 0 {self.width} {self.height}">
  {svg_content}
</svg>"""

        return svg_doc

    def _process_inline_coordinates(self, path: Path) -> None:
        """Process inline coordinate labels in path segments.

        Stores named coordinates defined inline like: (x,y) coordinate(name)

        Args:
            path: Path object containing segments
        """
        for segment in path.segments:
            # Check if this segment has a coordinate name
            coord_name = segment.options.get("coordinate_name")
            if coord_name and segment.destination:
                # Resolve the coordinate position
                pos = self.coord_resolver.resolve(segment.destination)
                # Evaluate variables in coordinate name
                evaluated_name = self.string_evaluator.evaluate(coord_name)
                # Store it
                self.named_coordinates[evaluated_name] = pos

    def _process_inline_nodes(self, path: Path, parent_options: Dict[str, Any] = None) -> list:
        """Process inline node labels in path segments.

        Creates SVG elements for nodes defined inline like: (x,y) node[options] (name) {text}

        Args:
            path: Path object containing segments
            parent_options: Options from parent draw statement (for color inheritance)

        Returns:
            List of SVG strings for the inline nodes
        """
        from ..parser.ast_nodes import Node

        if parent_options is None:
            parent_options = {}

        node_svgs = []
        for segment in path.segments:
            # Check if this segment has a node label
            node_label = segment.options.get("node_label")
            if node_label and segment.destination:
                # Merge parent options with node options (node options take precedence)
                # This allows nodes to inherit color from the draw statement
                merged_options = {**parent_options, **node_label.get("options", {})}

                # Create a Node object from the label
                node = Node(
                    name=node_label.get("name"),
                    position=segment.destination,
                    text=node_label.get("text", ""),
                    options=merged_options,
                )
                # Render the node
                node_svg = self.visit_node(node)
                if node_svg:
                    node_svgs.append(node_svg)

        return node_svgs

    def _check_for_arrows(self, ast: TikzPicture) -> bool:
        """Check if any statements use arrows."""
        return any(
            isinstance(stmt, DrawStatement) and "arrow" in stmt.options for stmt in ast.statements
        )

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
        # Process inline coordinate labels before rendering path
        self._process_inline_coordinates(stmt.path)

        path_data = self.path_renderer.render_path(stmt.path)

        # Evaluate options with variables
        evaluated_options = self.option_processor.process(stmt.options)
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

        result = f'<path d="{path_data}" style="{style}"{marker_start}{marker_end}/>'

        # Process inline node labels and add them to the result
        # Pass parent options so nodes can inherit color
        inline_nodes = self._process_inline_nodes(stmt.path, stmt.options)
        if inline_nodes:
            result = result + "\n  " + "\n  ".join(inline_nodes)

        return result

    def _get_text_anchor_attrs(self, options: Dict[str, Any]) -> tuple:
        """Convert TikZ text anchors to SVG text-anchor and dominant-baseline.

        Returns:
            tuple: (text-anchor, dominant-baseline, dx, dy) for positioning
        """
        # Default: centered
        text_anchor = "middle"
        baseline = "middle"
        dx = 0
        dy = 0

        # TikZ anchors: left, right, above, below, etc.
        if options.get("right"):
            text_anchor = "start"  # Text starts at position (flows right)
            dx = 3  # Small offset from point
        elif options.get("left"):
            text_anchor = "end"  # Text ends at position (flows left)
            dx = -3
        elif options.get("above"):
            baseline = "auto"  # Text baseline at position
            dy = -3  # Move up
        elif options.get("below"):
            baseline = "hanging"  # Text hangs below position
            dy = 3
        elif options.get("above right"):
            text_anchor = "start"
            baseline = "auto"
            dx = 3
            dy = -3
        elif options.get("above left"):
            text_anchor = "end"
            baseline = "auto"
            dx = -3
            dy = -3
        elif options.get("below right"):
            text_anchor = "start"
            baseline = "hanging"
            dx = 3
            dy = 3
        elif options.get("below left"):
            text_anchor = "end"
            baseline = "hanging"
            dx = -3
            dy = 3

        return text_anchor, baseline, dx, dy

    def visit_node(self, node: Node) -> str:
        """Convert node to SVG text element."""
        if node.position:
            x, y = self.coord_resolver.resolve(node.position)
        else:
            x, y = self.coord_transformer.tikz_to_svg(0, 0)

        # Store named node position
        if node.name:
            # Evaluate variables in node name (e.g., P\i -> P0)
            evaluated_name = self.string_evaluator.evaluate(node.name)
            self.named_coordinates[evaluated_name] = (x, y)

        # Convert options to style
        style = self.style_converter.convert_text_style(node.options)

        # Get text positioning attributes from anchor options
        text_anchor, baseline, dx, dy = self._get_text_anchor_attrs(node.options)

        # Check for math mode and render if present
        if self.math_renderer.has_math(node.text):
            plain_text, math_svg = self.math_renderer.render(node.text)
            if math_svg:
                # For math SVG, we need to handle anchors differently
                # The math SVG has its own viewBox, so we need to translate based on anchor
                # Extract width and height from the math SVG to calculate anchor offset
                import re
                width_match = re.search(r'width="([\d.]+)"', math_svg)
                height_match = re.search(r'height="([\d.]+)"', math_svg)

                math_width = float(width_match.group(1)) if width_match else 0
                math_height = float(height_match.group(1)) if height_match else 0

                # Scale down to approximately match 10px text height
                scale = 0.45
                scaled_width = math_width * scale
                scaled_height = math_height * scale

                # Adjust position based on anchor
                math_x = x
                math_y = y

                # Horizontal anchoring
                if text_anchor == "end":  # left anchor
                    math_x -= scaled_width
                elif text_anchor == "middle":
                    math_x -= scaled_width / 2
                # "start" (right anchor) - no adjustment, math starts at x

                # Vertical anchoring - math SVG baseline is typically at the bottom
                # Adjust to center the math vertically around the point
                if baseline == "auto":  # above
                    math_y -= scaled_height
                elif baseline == "middle":
                    math_y -= scaled_height / 2
                # "hanging" (below) - no adjustment

                return f'<g transform="translate({math_x:.2f},{math_y:.2f}) scale({scale})">{math_svg}</g>'
            else:
                # Fallback to plain text if rendering failed
                return f'<text x="{x+dx:.2f}" y="{y+dy:.2f}" style="{style}" text-anchor="{text_anchor}" dominant-baseline="{baseline}">{plain_text}</text>'
        else:
            # No math mode, use regular text with anchor offsets
            return f'<text x="{x+dx:.2f}" y="{y+dy:.2f}" style="{style}" text-anchor="{text_anchor}" dominant-baseline="{baseline}">{node.text}</text>'

    def visit_coordinate_definition(self, coord_def: CoordinateDefinition) -> None:
        """Store named coordinate (doesn't produce SVG output)."""
        if coord_def.position:
            pos = self.coord_resolver.resolve(coord_def.position)
            # Evaluate variables in coordinate name (e.g., P\i -> P0)
            evaluated_name = self.string_evaluator.evaluate(coord_def.name)
            self.named_coordinates[evaluated_name] = pos
        return None

    def visit_scope(self, scope: Scope) -> str:
        """Convert scope to SVG group."""
        elements = [element for stmt in scope.statements if (element := self.visit_statement(stmt))]

        if elements:
            # Apply scope options to group
            style = self.style_converter.convert(scope.options, "draw")
            content = "\n    ".join(elements)
            result = f'<g style="{style}">\n    {content}\n  </g>'
        else:
            result = ""

        return result

    def visit_foreach_loop(self, loop: ForeachLoop) -> str:
        """
        Convert foreach loop to expanded statements.

        Handles:
        - Simple iteration over values
        - Multiple variables (paired values)
        - Evaluate clause for computed variables
        - Nested loops with proper scoping
        """
        elements = self.loop_expander.expand(loop, self)
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
        elements = [element for stmt in layer.statements if (element := self.visit_statement(stmt))]

        if elements:
            content = "\n    ".join(elements)
            result = f'<g data-layer="{layer.name}">\n    {content}\n  </g>'
        else:
            result = ""

        return result

    def visit_style_definition(self, style_def) -> None:
        """Process style definition (doesn't produce SVG output)."""
        # Could store styles for later reference, but for now just acknowledge it
        return None
