"""Math rendering using ziamath for LaTeX math mode."""

import re
from typing import Optional, Tuple

try:
    import ziamath as zm

    ZIAMATH_AVAILABLE = True
except ImportError:
    ZIAMATH_AVAILABLE = False


class MathRenderer:
    """Renders LaTeX math mode using ziamath.

    Detects and renders math expressions enclosed in $...$ or \\(...\\).
    """

    def __init__(self, enabled: bool = True):
        """Initialize math renderer.

        Args:
            enabled: Whether to enable math rendering (requires ziamath)
        """
        self.enabled = enabled and ZIAMATH_AVAILABLE

    def has_math(self, text: str) -> bool:
        """Check if text contains math mode.

        Args:
            text: Text to check

        Returns:
            True if text contains $...$ or \\(...\\)
        """
        if not text:
            return False
        return bool(re.search(r"\$[^$]+\$", text))

    def render(self, text: str) -> Tuple[str, Optional[str]]:
        """Render math in text to SVG.

        Args:
            text: Text that may contain math mode ($...$)

        Returns:
            Tuple of (plain_text, svg_content)
            - plain_text: Text with math removed (for fallback)
            - svg_content: SVG string if math was found and rendered, None otherwise
        """
        if not self.enabled or not text:
            return text, None

        # Find math content
        match = re.search(r"\$([^$]+)\$", text)
        if not match:
            return text, None

        # Extract math expression
        math_expr = match.group(1)

        try:
            # Render with ziamath
            latex_obj = zm.Latex(math_expr)
            svg = latex_obj.svg()

            # Extract just the SVG content (remove XML declaration if present)
            svg = svg.strip()
            if svg.startswith("<?xml"):
                svg = svg.split("?>", 1)[1].strip()

            return text, svg

        except Exception:
            # If rendering fails, return plain text
            plain_text = text.replace(f"${math_expr}$", math_expr)
            return plain_text, None

    def extract_plain_text(self, text: str) -> str:
        """Extract plain text by removing math delimiters.

        Args:
            text: Text with math mode

        Returns:
            Text with $ removed but math content preserved
        """
        # Remove dollar signs but keep the math content
        return re.sub(r"\$([^$]+)\$", r"\1", text)
