#!/usr/bin/env python3
"""
TikZ to SVG converter - Command line tool.

Usage:
    python tikz2svg.py input.tex output.svg
    python tikz2svg.py input.tex  # outputs to input.svg
"""

import sys
import argparse
from pathlib import Path
from parser.parser import TikzParser
from svg.converter import SVGConverter


def convert_file(input_path: str, output_path: str = None, width: int = 500, height: int = 500):
    """
    Convert a TikZ file to SVG.

    Args:
        input_path: Path to input .tex file
        output_path: Path to output .svg file (optional)
        width: SVG canvas width
        height: SVG canvas height
    """
    # Default output path
    if output_path is None:
        output_path = Path(input_path).with_suffix('.svg')

    print(f"Converting {input_path} to {output_path}...")

    try:
        # Parse TikZ
        parser = TikzParser()
        ast = parser.parse_file(input_path)
        print(f"  ✓ Parsed TikZ (found {len(ast.statements)} statements)")

        # Convert to SVG
        converter = SVGConverter(width=width, height=height)
        svg = converter.convert(ast)
        print(f"  ✓ Generated SVG")

        # Write output
        with open(output_path, 'w') as f:
            f.write(svg)
        print(f"  ✓ Wrote {output_path}")

        print(f"\nSuccess! Converted {input_path} → {output_path}")

    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        return 1

    return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Convert TikZ diagrams to SVG',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tikz2svg.py input.tex output.svg
  python tikz2svg.py input.tex
  python tikz2svg.py input.tex --width 800 --height 600
        """
    )

    parser.add_argument('input', help='Input TikZ file (.tex)')
    parser.add_argument('output', nargs='?', help='Output SVG file (optional)')
    parser.add_argument('--width', type=int, default=500, help='SVG width (default: 500)')
    parser.add_argument('--height', type=int, default=500, help='SVG height (default: 500)')
    parser.add_argument('--scale', type=float, default=28.35, help='Scale factor (default: 28.35)')

    args = parser.parse_args()

    return convert_file(args.input, args.output, args.width, args.height)


if __name__ == '__main__':
    sys.exit(main())
