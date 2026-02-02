"""TikZ parser using Lark."""

from pathlib import Path

from lark import Lark, Token, Transformer

from .ast_nodes import *
from .preprocessor import TikzPreprocessor


class TikzTransformer(Transformer):
    """Transforms Lark parse tree into TikZ AST."""

    def tikzpicture(self, items):
        """Transform tikzpicture environment."""
        options = {}
        statements = []

        for item in items:
            if isinstance(item, dict) and item.get("_type") == "options":
                options = item["options"]
            elif isinstance(item, ASTNode):
                statements.append(item)

        return TikzPicture(options=options, statements=statements)

    def tikz_options(self, items):
        """Transform tikzpicture options."""
        return {"_type": "options", "options": items[0] if items else {}}

    def statement(self, items):
        """Pass through statement."""
        return items[0]

    def draw_stmt(self, items):
        """Transform draw statement."""
        options = {}
        path = None

        for item in items:
            if isinstance(item, dict):
                options = item
            elif isinstance(item, Path):
                path = item

        return DrawStatement(command="draw", options=options, path=path or Path())

    def fill_stmt(self, items):
        """Transform fill statement."""
        options = {}
        path = None

        for item in items:
            if isinstance(item, dict):
                options = item
            elif isinstance(item, Path):
                path = item

        return DrawStatement(command="fill", options=options, path=path or Path())

    def filldraw_stmt(self, items):
        """Transform filldraw statement."""
        options = {}
        path = None

        for item in items:
            if isinstance(item, dict):
                options = item
            elif isinstance(item, Path):
                path = item

        return DrawStatement(command="filldraw", options=options, path=path or Path())

    def path(self, items):
        """Transform path into segments."""
        segments = []
        current_coord = None
        current_operation = None
        start_coord = None

        # Debug: print items
        # print(f"DEBUG path items: {items}")

        i = 0
        while i < len(items):
            item = items[i]

            # Handle coordinate with modifier (e.g., (0,0) circle (1))
            if isinstance(item, dict) and "coord" in item:
                coord = item["coord"]
                modifier = item.get("modifier")

                if current_coord is None:
                    # First coordinate
                    start_coord = coord
                    segments.append(PathSegment(operation="start", destination=coord))
                else:
                    # Connected coordinate
                    segments.append(
                        PathSegment(operation=current_operation or "--", destination=coord)
                    )

                current_coord = coord
                current_operation = None

                # Add modifier as a separate segment
                if modifier:
                    segments.append(PathSegment(operation=modifier, destination=coord))

            elif isinstance(item, Coordinate):
                if current_coord is None:
                    # First coordinate - this is the starting point
                    start_coord = item
                    # Create a segment to mark the start
                    segments.append(PathSegment(operation="start", destination=item))
                else:
                    # We have a previous coordinate, create a segment
                    segments.append(
                        PathSegment(operation=current_operation or "--", destination=item)
                    )
                current_coord = item
                current_operation = None
            elif isinstance(item, str):
                # This is a path connector
                current_operation = item
            elif isinstance(item, dict) and item.get("_type") == "cycle":
                segments.append(PathSegment(operation="cycle"))

            i += 1

        return Path(segments=segments)

    def path_element(self, items):
        """Transform path element."""
        # print(f"DEBUG path_element items: {items}")
        if not items:
            return None

        # Handle CYCLE token
        from lark import Token
        if isinstance(items[0], Token) and items[0].type == "CYCLE":
            return {"_type": "cycle"}

        # Handle coordinate with optional modifier
        if len(items) > 1 and isinstance(items[1], dict):
            # Has a modifier (circle or arc)
            return {"coord": items[0], "modifier": items[1]}

        return items[0]

    def path_modifier(self, items):
        """Transform path modifier."""
        return items[0] if items else None

    def path_connector(self, items):
        """Return the connector operation."""
        if not items:
            return "--"

        # Handle .. controls .. pattern
        if len(items) > 1:
            for item in items:
                if isinstance(item, dict):
                    return item

        item = items[0]
        # Handle complex operations (arc, circle) that return dicts
        if isinstance(item, dict):
            return item
        return str(item)

    def arc_operation(self, items):
        """Transform arc operation."""
        if items:
            arc_spec = items[0]
            return {"_type": "arc", "spec": arc_spec}
        return {"_type": "arc"}

    def arc_spec(self, items):
        """Transform arc specification."""
        if len(items) == 3:
            # (start:end:radius) format
            return {
                "format": "angles",
                "start_angle": float(items[0]),
                "end_angle": float(items[1]),
                "radius": float(items[2]),
            }
        else:
            # [key=value] format
            spec = {}
            for item in items:
                if isinstance(item, dict):
                    spec.update(item)
            return {"format": "options", **spec}

    def arc_option(self, items):
        """Transform arc option."""
        # Items will be like ["start", "angle", "=", number]
        if len(items) >= 3:
            key = " ".join(str(items[i]) for i in range(len(items) - 1) if str(items[i]) != "=")
            value = float(items[-1])
            return {key.replace(" ", "_"): value}
        return {}

    def circle_operation(self, items):
        """Transform circle operation."""
        if items:
            circle_spec = items[0]
            return {"_type": "circle", "spec": circle_spec}
        return {"_type": "circle"}

    def circle_spec(self, items):
        """Transform circle specification."""
        if items:
            # Extract radius value
            radius = float(items[0])
            unit = items[1] if len(items) > 1 else "cm"
            return {"radius": radius, "unit": str(unit) if unit else "cm"}
        return {"radius": 1.0, "unit": "cm"}

    def unit(self, items):
        """Transform unit specification."""
        return str(items[0]) if items else "cm"

    def controls_clause(self, items):
        """Transform Bezier controls clause."""
        controls = []
        for item in items:
            if isinstance(item, Coordinate):
                controls.append(item)
        return {"_type": "controls", "points": controls}

    def coordinate(self, items):
        """Transform coordinate specification."""
        return items[0]

    def coord_spec(self, items):
        """Pass through coordinate spec."""
        return items[0]

    def cartesian_coord(self, items):
        """Transform Cartesian coordinate."""
        x = float(items[0])
        y = float(items[1])
        return Coordinate(system="cartesian", values=[x, y])

    def polar_coord(self, items):
        """Transform polar coordinate."""
        angle = float(items[0])
        radius = float(items[1])
        return Coordinate(system="polar", values=[angle, radius])

    def named_coord(self, items):
        """Transform named coordinate."""
        name = str(items[0])
        anchor = items[1] if len(items) > 1 else None
        return Coordinate(system="named", name=name, values=[])

    def relative_coord(self, items):
        """Transform relative coordinate."""
        # items[0] is '++' or '+', items[1] is the coordinate
        coord = items[-1]  # The actual coordinate
        coord.system = "relative"
        return coord

    def anchor(self, items):
        """Return anchor name."""
        return str(items[0])

    def node_stmt(self, items):
        """Transform node statement."""
        options = {}
        name = None
        position = None
        text = ""

        for item in items:
            if isinstance(item, dict):
                if "_type" in item:
                    if item["_type"] == "node_name":
                        name = item["name"]
                else:
                    options = item
            elif isinstance(item, str):
                text = item
            elif isinstance(item, Coordinate):
                position = item

        return Node(name=name, position=position, text=text, options=options)

    def node_name(self, items):
        """Extract node name."""
        return {"_type": "node_name", "name": str(items[0])}

    def node_position(self, items):
        """Extract node position."""
        return items[0]  # Should be a Coordinate

    def coordinate_stmt(self, items):
        """Transform coordinate definition."""
        options = {}
        name = ""
        position = None

        for item in items:
            if isinstance(item, dict):
                options = item
            elif isinstance(item, str):
                name = item
            elif isinstance(item, Coordinate):
                position = item

        return CoordinateDefinition(name=name, position=position, options=options)

    def scope(self, items):
        """Transform scope environment."""
        options = {}
        statements = []

        for item in items:
            if isinstance(item, dict):
                options = item
            elif isinstance(item, ASTNode):
                statements.append(item)

        return Scope(options=options, statements=statements)

    def foreach_loop(self, items):
        """Transform foreach loop."""
        variables = []
        values = []
        body = []

        for item in items:
            if isinstance(item, list) and len(item) > 0:
                if isinstance(item[0], str):
                    variables = item
                else:
                    values = item
            elif isinstance(item, ASTNode):
                body.append(item)

        return ForeachLoop(variables=variables, values=values, body=body)

    def foreach_vars(self, items):
        """Extract foreach variables."""
        return [str(item) for item in items]

    def foreach_values(self, items):
        """Extract foreach values."""
        return items[0] if items else []

    def foreach_value_list(self, items):
        """Transform foreach value list."""
        values = []
        for item in items:
            if isinstance(item, (list, tuple)):
                # Range like 0,...,5
                if len(item) == 3:
                    start, step, end = item
                    values.extend(
                        range(int(start), int(end) + 1, int(step) if step != "..." else 1)
                    )
                else:
                    values.append(item)
            else:
                values.append(float(item))
        return values

    def foreach_value(self, items):
        """Transform single foreach value."""
        if len(items) == 1:
            return float(items[0])
        elif len(items) == 3:
            # Range: start, ..., end
            return [float(items[0]), "...", float(items[2])]
        elif len(items) == 2:
            # Pair: value1/value2
            return (float(items[0]), float(items[1]))
        return items

    def macro_def(self, items):
        """Transform macro definition."""
        name = str(items[0])
        body = str(items[1]) if len(items) > 1 else ""
        return MacroDefinition(name=name, body=body)

    def options(self, items):
        """Transform options list."""
        if not items or items[0] is None:
            return {}
        return items[0]

    def option_list(self, items):
        """Transform option list into dictionary."""
        options = {}
        for item in items:
            if isinstance(item, dict):
                options.update(item)
        return options

    def option(self, items):
        """Transform single option."""
        item = items[0]
        if isinstance(item, dict):
            return item
        elif isinstance(item, tuple):
            # key-value tuple
            return {item[0]: item[1]}
        else:
            # flag
            key = self._to_string(item)
            return {key: True}

    def arrow_spec(self, items):
        """Transform arrow specification."""
        if items:
            arrow = str(items[0])
            return {"arrow": arrow}

    def multi_word_key(self, items):
        """Transform multi-word key."""
        return " ".join(str(item) for item in items)

    def key_value(self, items):
        """Transform key-value pair."""
        key = self._to_string(items[0])
        value = items[1]
        return (key, value)

    def flag(self, items):
        """Transform flag."""
        return items  # Already handled in option

    def _to_string(self, item):
        """Convert token or list to string."""
        if isinstance(item, str):
            return item
        elif isinstance(item, Token):
            return str(item.value)
        elif isinstance(item, list):
            return " ".join(
                str(i) if isinstance(i, Token) else str(i.value) if hasattr(i, "value") else str(i)
                for i in item
            )
        return str(item)

    def value(self, items):
        """Extract value."""
        if items:
            item = items[0]
            if isinstance(item, (int, float)):
                return item
            elif isinstance(item, Token):
                return str(item.value)
            elif isinstance(item, str):
                return item
            return str(item)
        return None

    def color(self, items):
        """Transform color specification."""
        if len(items) == 1:
            return str(items[0])
        else:
            # Mixed color like blue!30!white
            return "!".join(str(item) for item in items)

    def number(self, items):
        """Transform number."""
        if items:
            return float(items[0])
        return 0.0

    def math_expr(self, items):
        """Transform math expression (simplified for now)."""
        if len(items) == 1:
            item = items[0]
            if isinstance(item, Token):
                return float(item.value)
            return item
        return items

    def text(self, items):
        """Extract text content."""
        if items:
            return str(items[0])
        return ""

    def quoted_string(self, items):
        """Extract quoted string."""
        if items:
            return str(items[0]).strip('"')
        return ""


class TikzParser:
    """Main parser class for TikZ code."""

    def __init__(self):
        """Initialize parser with grammar."""
        import os

        current_dir = os.path.dirname(os.path.abspath(__file__))
        grammar_path = os.path.join(current_dir, "grammar.lark")
        with open(grammar_path, "r") as f:
            grammar = f.read()

        self.parser = Lark(grammar, parser="lalr", transformer=TikzTransformer())
        self.preprocessor = TikzPreprocessor()

    def parse(self, tikz_code: str) -> TikzPicture:
        """Parse TikZ code into AST."""
        try:
            # Preprocess the code
            tikz_code = self.preprocessor.preprocess(tikz_code)
            ast = self.parser.parse(tikz_code)
            return ast
        except Exception as e:
            raise ValueError(f"Failed to parse TikZ code: {e}")

    def parse_file(self, file_path: str) -> TikzPicture:
        """Parse TikZ code from file."""
        with open(file_path, "r") as f:
            content = f.read()
        return self.parse(content)
