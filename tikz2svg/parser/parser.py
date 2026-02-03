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

    def _create_draw_statement(self, command: str, items: list) -> DrawStatement:
        """Helper to create draw-like statements from items.

        Args:
            command: Command type (draw, fill, filldraw, clip)
            items: Parsed items containing options and path

        Returns:
            DrawStatement with extracted options and path
        """
        options = {}
        path = None

        for item in items:
            if isinstance(item, dict):
                options = item
            elif isinstance(item, Path):
                path = item

        return DrawStatement(command=command, options=options, path=path or Path())

    def draw_stmt(self, items):
        """Transform draw statement."""
        return self._create_draw_statement("draw", items)

    def fill_stmt(self, items):
        """Transform fill statement."""
        return self._create_draw_statement("fill", items)

    def filldraw_stmt(self, items):
        """Transform filldraw statement."""
        return self._create_draw_statement("filldraw", items)

    def clip_stmt(self, items):
        """Transform clip statement."""
        return self._create_draw_statement("clip", items)

    def path(self, items):
        """Transform path into segments."""
        segments = []
        current_coord = None
        current_operation = None
        start_coord = None

        # Check for inline foreach and expand if present
        expanded_items = []
        for item in items:
            if isinstance(item, dict) and item.get("_type") == "inline_foreach":
                # Expand the inline foreach loop
                expanded = self._expand_inline_foreach(item)
                expanded_items.extend(expanded)
            else:
                expanded_items.append(item)

        # Process expanded items
        i = 0
        while i < len(expanded_items):
            item = expanded_items[i]

            # Handle coordinate with modifier (e.g., (0,0) circle (1))
            if isinstance(item, dict) and "coord" in item:
                coord = item["coord"]
                modifier = item.get("modifier")
                coord_label = item.get("coord_label")
                node_label = item.get("node_label")

                # Create segment options if there's a coordinate label or node label
                seg_options = {}
                if coord_label:
                    seg_options["coordinate_name"] = coord_label.get("name")
                if node_label:
                    seg_options["node_label"] = node_label

                if current_coord is None:
                    # First coordinate
                    start_coord = coord
                    segments.append(
                        PathSegment(operation="start", destination=coord, options=seg_options)
                    )
                else:
                    # Connected coordinate
                    # Use "move" operation if no connector was specified (for placing nodes)
                    operation = current_operation if current_operation is not None else "move"
                    segments.append(
                        PathSegment(
                            operation=operation,
                            destination=coord,
                            options=seg_options,
                        )
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
                    # Use "move" operation if no connector was specified (for placing nodes)
                    operation = current_operation if current_operation is not None else "move"
                    segments.append(PathSegment(operation=operation, destination=item))
                current_coord = item
                current_operation = None
            elif isinstance(item, str):
                # This is a path connector
                current_operation = item
            elif isinstance(item, dict) and item.get("_type") == "cycle":
                segments.append(PathSegment(operation="cycle"))

            i += 1

        return Path(segments=segments)

    def _expand_inline_foreach(self, foreach_dict):
        """Expand inline foreach loop into path elements.

        Args:
            foreach_dict: Dict with foreach loop information

        Returns:
            List of expanded path elements (connectors and coordinates)
        """
        variables = foreach_dict["variables"]
        values = foreach_dict["values"]
        path_segments = foreach_dict["path_segments"]
        evaluate_clause = foreach_dict.get("evaluate_clause")

        expanded = []

        # For each value in the loop
        for value in values:
            # Create a temporary context for variable substitution
            var_map = {}
            if len(variables) == 1:
                var_map[variables[0]] = value
            elif len(variables) > 1 and isinstance(value, (tuple, list)):
                for i, var in enumerate(variables):
                    if i < len(value):
                        var_map[var] = value[i]

            # Handle evaluate clause if present
            if evaluate_clause:
                # For now, skip evaluate clause in inline foreach
                # (would require math evaluation during parsing)
                pass

            # Expand each path segment with variable substitution
            for seg in path_segments:
                connector = seg["connector"]
                element = seg["element"]

                # Substitute variables in the element
                substituted_element = self._substitute_vars_in_coord(element, var_map)

                expanded.append(connector)
                expanded.append(substituted_element)

        return expanded

    def _substitute_vars_in_coord(self, element, var_map):
        """Substitute variables in a coordinate element.

        Args:
            element: Coordinate or dict with coordinate info
            var_map: Dict mapping variable names to values

        Returns:
            New coordinate with variables substituted
        """
        if isinstance(element, Coordinate):
            # Create a copy with substituted values
            new_values = []
            for val in element.values:
                if isinstance(val, str):
                    # Try to substitute variables in the string
                    substituted = self._substitute_vars_in_expr(val, var_map)
                    new_values.append(substituted)
                else:
                    new_values.append(val)

            return Coordinate(
                system=element.system,
                values=new_values,
                name=element.name,
                modifiers=element.modifiers,
            )
        elif isinstance(element, dict) and "coord" in element:
            # Handle dict format
            coord = element["coord"]
            new_coord = self._substitute_vars_in_coord(coord, var_map)
            return {"coord": new_coord, "modifier": element.get("modifier")}
        else:
            return element

    def _substitute_vars_in_expr(self, expr_str, var_map):
        """Substitute variables in an expression string.

        Args:
            expr_str: Expression string like "\\i*0.5"
            var_map: Dict mapping variable names to values

        Returns:
            Expression string with variables substituted
        """
        import re

        def replace_var(match):
            var_name = match.group(1)
            if var_name in var_map:
                value = var_map[var_name]
                return str(value)
            return match.group(0)

        # Replace variable references like \i, \x, etc.
        result = re.sub(r"\\([a-zA-Z][a-zA-Z0-9]*)", replace_var, expr_str)
        return result

    def path_element(self, items):
        """Transform path element."""
        # print(f"DEBUG path_element items: {items}")
        if not items:
            return None

        # Handle CYCLE token
        from lark import Token

        if isinstance(items[0], Token) and items[0].type == "CYCLE":
            return {"_type": "cycle"}

        # Extract coordinate and optional label/modifier
        coord = items[0]
        coord_label = None
        node_label = None
        modifier = None

        # Check remaining items for labels and modifiers
        for item in items[1:]:
            if isinstance(item, dict):
                if item.get("_type") == "coordinate_label":
                    coord_label = item
                elif item.get("_type") == "node_label":
                    node_label = item
                else:
                    # It's a modifier (circle, arc, etc.)
                    modifier = item

        # Build result based on what we found
        if coord_label or node_label or modifier:
            result = {"coord": coord}
            if coord_label:
                result["coord_label"] = coord_label
            if node_label:
                result["node_label"] = node_label
            if modifier:
                result["modifier"] = modifier
            return result

        return coord

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
            # (start:end:radius) format - keep as strings for math expressions
            return {
                "format": "angles",
                "start_angle": str(items[0]),
                "end_angle": str(items[1]),
                "radius": str(items[2]),
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
            key_parts = [
                self._to_string(items[i])
                for i in range(len(items) - 1)
                if self._to_string(items[i]) != "="
            ]
            key = " ".join(key_parts)
            # Keep value as string for math expressions
            value = self._to_string(items[-1])
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
            # Keep radius as string for math expressions
            radius = self._to_string(items[0])
            unit = self._to_string(items[1]) if len(items) > 1 else "cm"
            return {"radius": radius, "unit": unit}
        return {"radius": "1.0", "unit": "cm"}

    def unit(self, items):
        """Transform unit specification."""
        return self._to_string(items[0]) if items else "cm"

    def controls_clause(self, items):
        """Transform Bezier controls clause."""
        controls = []
        for item in items:
            if isinstance(item, Coordinate):
                controls.append(item)
        return {"_type": "controls", "points": controls}

    def inline_foreach_path(self, items):
        """Transform inline foreach within path.

        Returns a dict with foreach loop information that will be expanded
        during path construction.
        """
        variables = []
        values = []
        path_segments = []
        options = {}
        seen_list = False

        for item in items:
            if isinstance(item, list) and len(item) > 0:
                # First list is variables, second is values
                if not seen_list:
                    variables = item
                    seen_list = True
                else:
                    values = item
            elif isinstance(item, dict):
                if "evaluate" in item:
                    options = item
                elif "_type" in item and item["_type"] == "path_segments":
                    path_segments = item["segments"]

        evaluate_clause = options.get("evaluate") if options else None

        return {
            "_type": "inline_foreach",
            "variables": variables,
            "values": values,
            "path_segments": path_segments,
            "evaluate_clause": evaluate_clause,
        }

    def path_segments(self, items):
        """Transform path segments (connector + element pairs)."""
        segments = []
        current_connector = None

        for item in items:
            if isinstance(item, str):
                # Path connector
                current_connector = item
            elif isinstance(item, Coordinate) or (isinstance(item, dict) and "coord" in item):
                # Path element - pair with connector
                if current_connector:
                    segments.append({"connector": current_connector, "element": item})
                    current_connector = None

        return {"_type": "path_segments", "segments": segments}

    def relative_coordinate(self, items):
        """Transform relative coordinate (++ or +)."""
        from lark import Token

        # items[0] is the operator (++ or +), items[1] is the coordinate
        operator = items[0].value if isinstance(items[0], Token) else str(items[0])
        inner_coord = items[1]

        # Create a relative coordinate that wraps the inner coordinate
        # Store the operator in modifiers and the inner coordinate's values
        if isinstance(inner_coord, Coordinate):
            return Coordinate(
                system="relative",
                values=inner_coord.values,
                modifiers={"operator": operator, "inner_system": inner_coord.system},
            )
        return Coordinate(system="relative", values=[0, 0], modifiers={"operator": operator})

    def coordinate(self, items):
        """Transform coordinate specification."""
        return items[0]

    def coord_spec(self, items):
        """Pass through coordinate spec."""
        return items[0]

    def cartesian_coord(self, items):
        """Transform Cartesian coordinate."""
        # Keep as strings for later evaluation
        x = str(items[0])
        y = str(items[1])
        return Coordinate(system="cartesian", values=[x, y])

    def polar_coord(self, items):
        """Transform polar coordinate."""
        # Keep as strings for later evaluation
        angle = str(items[0])
        radius = str(items[1])
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
        """Return anchor name (can be multi-word like 'north east')."""
        from lark import Token

        # Join multiple CNAMEs with space
        parts = [str(item.value if isinstance(item, Token) else item) for item in items]
        return " ".join(parts)

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

    def coordinate_label(self, items):
        """Extract inline coordinate label.

        Returns a dict marking this as a coordinate definition.
        """
        name = None
        options = {}

        for item in items:
            if isinstance(item, str):
                name = item
            elif isinstance(item, dict):
                options = item

        return {"_type": "coordinate_label", "name": name, "options": options}

    def node_label(self, items):
        """Extract inline node label.

        Returns a dict marking this as a node to be created at the current path position.
        Grammar: "node" options? node_name? "{" text "}"
        """
        options = {}
        name = None
        text = ""

        for item in items:
            if isinstance(item, dict):
                if item.get("_type") == "node_name":
                    name = item.get("name")
                else:
                    # It's options
                    options = item
            elif isinstance(item, str):
                text = item

        return {"_type": "node_label", "name": name, "text": text, "options": options}

    def name_with_vars(self, items):
        """Extract name that may contain variable references."""
        from lark import Token

        if items and isinstance(items[0], Token):
            return str(items[0].value)
        return str(items[0]) if items else ""

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

    def layer_decl(self, items):
        """Transform layer declaration."""
        from lark import Token

        name = str(items[0].value if isinstance(items[0], Token) else items[0])
        return LayerDeclaration(name=name)

    def layer_set(self, items):
        """Transform layer set command."""
        # items[0] is the layer_list
        layers = items[0] if isinstance(items[0], list) else [items[0]]
        return LayerSet(layers=layers)

    def layer_list(self, items):
        """Transform layer list."""
        from lark import Token

        return [str(item.value if isinstance(item, Token) else item) for item in items]

    def layer_env(self, items):
        """Transform pgfonlayer environment."""
        from lark import Token

        name = ""
        statements = []

        for item in items:
            if isinstance(item, Token) and item.type == "CNAME":
                name = str(item.value)
            elif isinstance(item, str) and not name:
                name = item
            elif isinstance(item, ASTNode):
                statements.append(item)

        return Layer(name=name, statements=statements)

    def style_def(self, items):
        """Transform style definition (tikzset)."""
        # items[0] should be style_assignment_list
        styles = items[0] if isinstance(items[0], dict) else {}
        return StyleDefinition(styles=styles)

    def style_assignment_list(self, items):
        """Transform list of style assignments."""
        styles = {}
        for item in items:
            if isinstance(item, dict):
                styles.update(item)
        return styles

    def style_path(self, items):
        """Transform style path (name parts separated by /)."""
        from lark import Token

        name_parts = []
        for item in items:
            if isinstance(item, Token) and item.type == "CNAME":
                name_parts.append(str(item.value))
            elif isinstance(item, str):
                name_parts.append(item)

        return "/".join(name_parts) if name_parts else "default"

    def style_assignment(self, items):
        """Transform single style assignment."""
        # items: [style_path, DOT_STYLE token, option_list]
        style_name = "default"
        options = {}

        for item in items:
            if isinstance(item, str):
                # This is the style_path result
                style_name = item
            elif isinstance(item, dict):
                # This is the option_list
                options = item

        return {style_name: options}

    def foreach_loop(self, items):
        """Transform foreach loop."""
        variables = []
        values = []
        body = []
        options = {}
        seen_list = False

        for item in items:
            if isinstance(item, list) and len(item) > 0:
                # First list is variables, second is values
                if not seen_list:
                    variables = item
                    seen_list = True
                else:
                    values = item
            elif isinstance(item, dict) and "evaluate" not in item:
                # Regular options (not evaluate clause)
                options.update(item)
            elif isinstance(item, dict) and "evaluate" in item:
                # Evaluate clause
                options = item
            elif isinstance(item, ASTNode):
                body.append(item)

        evaluate_clause = options.get("evaluate") if options else None
        return ForeachLoop(
            variables=variables, values=values, evaluate_clause=evaluate_clause, body=body
        )

    def foreach_vars(self, items):
        """Extract foreach variables."""
        return [str(item) for item in items]

    def foreach_values(self, items):
        """Extract foreach values."""
        return items[0] if items else []

    def foreach_options(self, items):
        """Transform foreach options."""
        options = {}
        for item in items:
            if isinstance(item, dict):
                options.update(item)
        return options

    def foreach_option(self, items):
        """Transform foreach option (evaluate clause)."""
        # Items: ["evaluate", "=", var, "as", new_var, "using", expr]
        if len(items) >= 3:
            source_var = str(items[0])  # Variable being evaluated
            target_var = str(items[1])  # New variable name
            expression = str(items[2]) if len(items) > 2 else source_var
            return {
                "evaluate": {
                    "source": source_var,
                    "target": target_var,
                    "expression": expression,
                }
            }
        return {}

    def foreach_item(self, items):
        """Transform a single foreach item (could be DOTDOTDOT or a value)."""
        from lark import Token

        if len(items) == 1 and isinstance(items[0], Token) and items[0].type == "DOTDOTDOT":
            return "..."
        # Otherwise it's a foreach_value, which is already transformed
        return items[0] if items else None

    def foreach_value_list(self, items):
        """Transform foreach value list - handles ranges and simple lists.

        After filtering commas, items can be:
        - [val1, val2, val3] - simple list
        - [val1, '...', val2] - range without step
        - [val1, val2, '...', val3] - range with step
        """
        # items are foreach_item results, commas are already filtered by Lark
        # Look for '...' in the list
        dotdotdot_idx = None
        for i, item in enumerate(items):
            if item == "...":
                dotdotdot_idx = i
                break

        if dotdotdot_idx is not None:
            # This is a range
            if dotdotdot_idx == 1:
                # Simple range: {start, ..., end}
                start = str(items[0])
                end = str(items[2]) if len(items) > 2 else "0"
                step = 1
            elif dotdotdot_idx == 2:
                # Range with step: {start, step_val, ..., end}
                start = str(items[0])
                step_val = str(items[1])
                end = str(items[3]) if len(items) > 3 else "0"

                # Calculate step from start and step_val
                try:
                    start_num = float(start)
                    step_num = float(step_val)
                    step = step_num - start_num
                except Exception:
                    step = 1
            else:
                # Unexpected position, treat as simple list
                return [item for item in items if item != "..."]

            # Expand range
            try:
                start_val = float(start)
                end_val = float(end)
                step = float(step)

                # Generate range values
                values = []
                current = start_val
                if step > 0:
                    while current <= end_val + 1e-10:  # Small epsilon for float comparison
                        values.append(current)
                        current += step
                elif step < 0:
                    while current >= end_val - 1e-10:
                        values.append(current)
                        current += step
                else:
                    values.append(start_val)  # Zero step, just return start
                return values
            except Exception:
                # If evaluation fails, return the range as a dict for later evaluation
                return [{"range": True, "start": start, "end": end, "step": step}]
        else:
            # Simple list: just return the values
            return items

    def foreach_value(self, items):
        """Transform single foreach value."""
        from lark import Token

        if len(items) == 1:
            # Single value
            return str(items[0])
        elif len(items) == 2:
            # Pair: value1/value2
            return (str(items[0]), str(items[1]))
        elif len(items) == 5:
            # Range: start, ..., end (with commas)
            # items[0] = start, items[1] = ',', items[2] = '...', items[3] = ',', items[4] = end
            return {"range": True, "start": str(items[0]), "end": str(items[4]), "step": 1}
        elif len(items) == 3 and isinstance(items[1], Token) and items[1].type == "DOTDOTDOT":
            # Range: start...end (without commas - shouldn't happen with current grammar but keep for safety)
            return {"range": True, "start": str(items[0]), "end": str(items[2]), "step": 1}
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
        """Transform key-value pair, including style assignments."""
        from lark import Token

        key = self._to_string(items[0])

        # Check if DOT_STYLE token is present
        has_dot_style = any(isinstance(item, Token) and item.type == "DOT_STYLE" for item in items)

        if has_dot_style:
            # This is a style assignment: key/.style = value
            # Value is the last item
            value = items[-1]
            # Wrap in a style assignment format
            if isinstance(value, dict):
                # Value is option list - this is a style definition
                return (f"{key}/.style", value)
        else:
            # Regular key-value
            value = items[1]

        return (key, value)

    def flag(self, items):
        """Transform flag."""
        return items  # Already handled in option

    def _to_string(self, item):
        """Convert token, list, or value to string.

        Args:
            item: Token, string, list, or other value

        Returns:
            String representation
        """
        if isinstance(item, str):
            return item
        elif isinstance(item, Token):
            return str(item.value)
        elif isinstance(item, list):
            return " ".join(self._to_string(i) for i in item)
        return str(item)

    def value(self, items):
        """Extract value, optionally with unit."""
        if items:
            # First item is the value
            value_str = self._to_string(items[0])

            # If there's a unit (second item), append it
            if len(items) > 1:
                unit = self._to_string(items[1])
                return value_str + unit

            return value_str
        return None

    def color(self, items):
        """Transform color specification."""
        if len(items) == 1:
            return self._to_string(items[0])
        # Mixed color like blue!30!white
        return "!".join(self._to_string(item) for item in items)

    def number(self, items):
        """Transform number."""
        if items:
            return float(items[0])
        return 0.0

    def math_expr(self, items):
        """Transform math expression into string representation."""
        if not items:
            return "0"

        if len(items) == 1:
            item = items[0]
            if isinstance(item, Token):
                # Could be SIGNED_NUMBER or CNAME
                if item.type == "SIGNED_NUMBER":
                    return item.value
                elif item.type == "CNAME":
                    # Variable reference without backslash - could happen in some contexts
                    return f"\\{item.value}"
            return str(item)

        # Check for variable reference pattern: "\\" CNAME
        if len(items) == 2 and isinstance(items[1], Token) and items[1].type == "CNAME":
            return f"\\{items[1].value}"

        # Multiple items - reconstruct expression
        # Format: expr operator expr, or function(expr), or (expr)
        result = ""
        for item in items:
            if isinstance(item, Token):
                result += str(item.value)
            else:
                result += str(item)

        return result

    def text(self, items):
        """Extract text content."""
        # items[0] will be text_parts result
        if items:
            return items[0]
        return ""

    def text_parts(self, items):
        """Combine text parts including nested braces."""
        result = []
        for item in items:
            if isinstance(item, str):
                result.append(item)
            else:
                # It's from nested_braces, already a string
                result.append(str(item))
        return "".join(result)

    def nested_braces(self, items):
        """Handle nested braces in text."""
        # Reconstruct {content}
        if items:
            content = "".join(str(item) for item in items)
            return "{" + content + "}"
        return "{}"

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
