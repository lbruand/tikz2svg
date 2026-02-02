"""Style conversion from TikZ options to SVG styles."""

from typing import Any, Dict


class StyleConverter:
    """Converts TikZ options to SVG styles."""

    # Color name mappings
    COLORS = {
        "red": "#FF0000",
        "green": "#00FF00",
        "blue": "#0000FF",
        "yellow": "#FFFF00",
        "cyan": "#00FFFF",
        "magenta": "#FF00FF",
        "black": "#000000",
        "white": "#FFFFFF",
        "gray": "#808080",
        "darkgray": "#404040",
        "lightgray": "#C0C0C0",
        "brown": "#A52A2A",
        "lime": "#00FF00",
        "olive": "#808000",
        "orange": "#FFA500",
        "pink": "#FFC0CB",
        "purple": "#800080",
        "teal": "#008080",
        "violet": "#EE82EE",
    }

    # Line width mappings (in pixels)
    LINE_WIDTHS = {
        "ultra thin": 0.5,
        "very thin": 0.75,
        "thin": 1.0,
        "semithick": 1.5,
        "thick": 2.0,
        "very thick": 3.0,
        "ultra thick": 4.0,
    }

    def convert(self, options: Dict[str, Any], command: str = "draw") -> str:
        """
        Convert TikZ options to SVG style string.

        Args:
            options: TikZ options dictionary
            command: TikZ command ('draw', 'fill', 'filldraw')

        Returns:
            SVG style string
        """
        styles = []

        # Handle draw/fill/stroke
        if command == "fill":
            styles.append("stroke: none")
            fill_color = self.get_color(options)
            styles.append(f"fill: {fill_color}")
        elif command == "filldraw":
            stroke_color = self.get_color(options, default="black")
            fill_color = self.get_color(options, key="fill", default="black")
            styles.append(f"stroke: {stroke_color}")
            styles.append(f"fill: {fill_color}")
            stroke_width = self.get_line_width(options)
            styles.append(f"stroke-width: {stroke_width}px")
        else:  # draw
            stroke_color = self.get_color(options, default="black")
            styles.append(f"stroke: {stroke_color}")
            styles.append("fill: none")
            stroke_width = self.get_line_width(options)
            styles.append(f"stroke-width: {stroke_width}px")

        # Line dash pattern
        if any(k in options for k in ["dashed", "dotted", "dash pattern"]):
            dash_array = self.get_dash_pattern(options)
            if dash_array:
                styles.append(f"stroke-dasharray: {dash_array}")

        # Opacity
        if "opacity" in options:
            opacity = options["opacity"]
            if isinstance(opacity, (int, float)):
                styles.append(f"opacity: {opacity}")

        # Line cap and join
        if "line cap" in options:
            styles.append(f'stroke-linecap: {options["line cap"]}')
        if "line join" in options:
            styles.append(f'stroke-linejoin: {options["line join"]}')

        return "; ".join(styles)

    def convert_text_style(self, options: Dict[str, Any]) -> str:
        """Convert options for text elements."""
        styles = []

        # Font size
        if "font" in options:
            font = options["font"]
            if "tiny" in str(font):
                styles.append("font-size: 8px")
            elif "small" in str(font):
                styles.append("font-size: 10px")
            elif "large" in str(font):
                styles.append("font-size: 16px")
            elif "huge" in str(font):
                styles.append("font-size: 20px")
            else:
                styles.append("font-size: 12px")
        else:
            styles.append("font-size: 12px")

        # Color
        color = self.get_color(options, default="black")
        styles.append(f"fill: {color}")

        # Font family
        styles.append("font-family: sans-serif")

        return "; ".join(styles)

    def get_color(self, options: Dict[str, Any], key: str = None, default: str = "black") -> str:
        """
        Extract color from options.

        Args:
            options: Options dictionary
            key: Specific key to look for (e.g., 'fill', 'draw')
            default: Default color

        Returns:
            SVG color string
        """
        # Check specific key first
        if key and key in options:
            color_value = options[key]
            return self.parse_color(color_value)

        # Check for color options
        for color_name in self.COLORS.keys():
            if color_name in options and options[color_name]:
                return self.COLORS[color_name]

        # Check for 'color' key
        if "color" in options:
            return self.parse_color(options["color"])

        # Check for 'draw' or 'fill' keys
        if "draw" in options:
            return self.parse_color(options["draw"])
        if "fill" in options and key != "stroke":
            return self.parse_color(options["fill"])

        return self.COLORS.get(default, default)

    def parse_color(self, color_value: Any) -> str:
        """
        Parse a color value (name, hex, or mixed).

        Args:
            color_value: Color value from options

        Returns:
            SVG color string
        """
        if not color_value:
            return "#000000"

        color_str = str(color_value)

        # Check if it's a hex color
        if color_str.startswith("#"):
            return color_str

        # Check if it's a known color name
        if color_str in self.COLORS:
            return self.COLORS[color_str]

        # Check for mixed color (e.g., "blue!30!white")
        if "!" in color_str:
            # Simplified: just use first color
            # Full implementation would blend colors
            parts = color_str.split("!")
            if parts[0] in self.COLORS:
                return self.COLORS[parts[0]]

        # Default to black
        return "#000000"

    def get_line_width(self, options: Dict[str, Any]) -> float:
        """Get line width from options."""
        # Check for named widths
        for width_name, width_value in self.LINE_WIDTHS.items():
            if width_name in options and options[width_name]:
                return width_value

        # Check for 'line width' key
        if "line width" in options:
            # TODO: Parse unit (pt, cm, etc.)
            return float(options["line width"])

        # Default
        return 1.0

    def get_dash_pattern(self, options: Dict[str, Any]) -> str:
        """Get stroke dash pattern from options."""
        if "dashed" in options:
            return "5,5"
        elif "dotted" in options:
            return "2,2"
        elif "dash pattern" in options:
            # TODO: Parse custom dash pattern
            return "5,5"
        return ""
