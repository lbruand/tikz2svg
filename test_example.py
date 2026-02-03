#!/usr/bin/env python3
"""Test the TikZ parser on input01.tex example."""

from tikz2svg.parser.parser import TikzParser
from tikz2svg.svg.converter import SVGConverter

# Read the input file
with open("inputs/input01.tex", "r") as f:
    tikz_code = f.read()

print("=" * 80)
print("Testing TikZ Parser on input01.tex")
print("=" * 80)
print()

# Parse the TikZ code
parser = TikzParser()
print("Parsing...")
try:
    ast = parser.parse(tikz_code)
    print(f"✓ Parsing successful!")
    print(f"  - AST type: {type(ast).__name__}")
    print(f"  - Number of statements: {len(ast.statements)}")
    print()

    # Print AST structure
    print("AST Structure:")
    for i, stmt in enumerate(ast.statements, 1):
        print(f"  {i}. {type(stmt).__name__}")
        if hasattr(stmt, "command"):
            print(f"     - Command: {stmt.command}")
        if hasattr(stmt, "text"):
            print(f"     - Text: {stmt.text}")
    print()

    # Convert to SVG
    converter = SVGConverter()
    print("Converting to SVG...")
    svg = converter.convert(ast)
    print(f"✓ Conversion successful!")
    print(f"  - SVG length: {len(svg)} characters")
    print()

    # Save SVG output
    output_file = "outputs/input01.svg"
    import os

    os.makedirs("outputs", exist_ok=True)
    with open(output_file, "w") as f:
        f.write(svg)
    print(f"✓ SVG saved to: {output_file}")
    print()

    # Show a preview of the SVG
    print("SVG Preview (first 500 chars):")
    print("-" * 80)
    print(svg[:500])
    if len(svg) > 500:
        print("...")
        print(svg[-200:])
    print("-" * 80)
    print()

    print("=" * 80)
    print("SUCCESS! ✓")
    print("=" * 80)

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback

    traceback.print_exc()
    print()
    print("=" * 80)
    print("FAILED ✗")
    print("=" * 80)
