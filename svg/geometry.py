"""Geometric transformations for TikZ to SVG conversion."""
import math
from typing import Tuple


class CoordinateTransformer:
    """Handles coordinate system transformations."""

    def __init__(self, scale: float = 28.35, offset_x: float = 250, offset_y: float = 250):
        """
        Initialize coordinate transformer.

        Args:
            scale: Scale factor (points to pixels), default 28.35 (1cm at 72dpi)
            offset_x: X offset for center (SVG pixels)
            offset_y: Y offset for center (SVG pixels)
        """
        self.scale = scale
        self.offset_x = offset_x
        self.offset_y = offset_y

    def tikz_to_svg(self, x: float, y: float) -> Tuple[float, float]:
        """
        Convert TikZ coordinates to SVG coordinates.

        TikZ: origin at center, Y-axis points up
        SVG: origin at top-left, Y-axis points down

        Args:
            x: TikZ x coordinate (cm or pt)
            y: TikZ y coordinate (cm or pt)

        Returns:
            (svg_x, svg_y) tuple
        """
        svg_x = (x * self.scale) + self.offset_x
        svg_y = (-y * self.scale) + self.offset_y  # Flip Y axis
        return (svg_x, svg_y)

    def polar_to_cartesian(self, angle: float, radius: float) -> Tuple[float, float]:
        """
        Convert polar coordinates to Cartesian.

        Args:
            angle: Angle in degrees
            radius: Radius

        Returns:
            (x, y) tuple in Cartesian coordinates
        """
        angle_rad = math.radians(angle)
        x = radius * math.cos(angle_rad)
        y = radius * math.sin(angle_rad)
        return (x, y)

    def calculate_arc_path(self, start_x: float, start_y: float,
                          radius: float, start_angle: float, end_angle: float) -> str:
        """
        Calculate SVG arc path data.

        Args:
            start_x, start_y: Starting point
            radius: Arc radius
            start_angle: Start angle in degrees
            end_angle: End angle in degrees

        Returns:
            SVG arc path data string
        """
        # Calculate end point
        end_angle_rad = math.radians(end_angle)
        end_x = start_x + radius * math.cos(end_angle_rad)
        end_y = start_y + radius * math.sin(end_angle_rad)

        # Large arc flag
        large_arc = 1 if abs(end_angle - start_angle) > 180 else 0

        # Sweep flag (clockwise)
        sweep = 1 if end_angle > start_angle else 0

        return f'A {radius} {radius} 0 {large_arc} {sweep} {end_x:.2f} {end_y:.2f}'
