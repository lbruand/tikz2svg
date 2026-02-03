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

        # Font size - TikZ default is ~10pt which is approximately 10px
        if "font" in options:
            font = options["font"]
            if "tiny" in str(font):
                styles.append("font-size: 7px")
            elif "small" in str(font):
                styles.append("font-size: 9px")
            elif "large" in str(font):
                styles.append("font-size: 14px")
            elif "huge" in str(font):
                styles.append("font-size: 18px")
            else:
                styles.append("font-size: 10px")
        else:
            styles.append("font-size: 10px")

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

        # Check for mixed color (e.g., "blue!30!white" or "red!50")
        if "!" in color_str:
            return self.blend_colors(color_str)

        # Default to black
        return "#000000"

    def blend_colors(self, color_spec: str) -> str:
        """
        Blend colors according to TikZ specification.

        Examples:
            "blue!30!white" -> 30% blue, 70% white
            "red!50" -> 50% red, 50% white (default)
            "green!20!yellow!80" -> complex blend

        Args:
            color_spec: Color specification with ! separators

        Returns:
            Blended color as hex string
        """
        parts = color_spec.split("!")

        # Simple case: color!percentage
        if len(parts) == 2:
            color1 = parts[0]
            try:
                percentage = float(parts[1])
                # Blend with white
                return self.mix_two_colors(color1, "white", percentage / 100.0)
            except ValueError:
                # parts[1] is another color, equal blend
                color2 = parts[1]
                return self.mix_two_colors(color1, color2, 0.5)

        # Complex case: color!percentage!color
        if len(parts) >= 3:
            color1 = parts[0]
            try:
                percentage = float(parts[1]) / 100.0
            except ValueError:
                percentage = 0.5
            color2 = parts[2]
            return self.mix_two_colors(color1, color2, percentage)

        # Fallback
        if parts[0] in self.COLORS:
            return self.COLORS[parts[0]]
        return "#000000"

    def mix_two_colors(self, color1: str, color2: str, ratio: float) -> str:
        """
        Mix two colors with given ratio.

        Args:
            color1: First color name or hex
            color2: Second color name or hex
            ratio: Ratio of color1 (0.0 to 1.0)

        Returns:
            Mixed color as hex string
        """
        # Get RGB values for both colors
        rgb1 = self.color_to_rgb(color1)
        rgb2 = self.color_to_rgb(color2)

        # Mix
        r = int(rgb1[0] * ratio + rgb2[0] * (1 - ratio))
        g = int(rgb1[1] * ratio + rgb2[1] * (1 - ratio))
        b = int(rgb1[2] * ratio + rgb2[2] * (1 - ratio))

        # Clamp values
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))

        return f"#{r:02X}{g:02X}{b:02X}"

    def color_to_rgb(self, color: str) -> tuple:
        """
        Convert color name or hex to RGB tuple.

        Args:
            color: Color name or hex string

        Returns:
            (r, g, b) tuple
        """
        # Check if it's a named color
        if color in self.COLORS:
            hex_color = self.COLORS[color]
        elif color.startswith("#"):
            hex_color = color
        else:
            hex_color = "#000000"

        # Parse hex
        hex_color = hex_color.lstrip("#")
        if len(hex_color) == 6:
            return (
                int(hex_color[0:2], 16),
                int(hex_color[2:4], 16),
                int(hex_color[4:6], 16),
            )
        return (0, 0, 0)

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
