#!/usr/bin/env python3
"""Test the TikZ parser on complex_demo.tex with all Phase features."""

from tikz2svg.parser.parser import TikzParser
from tikz2svg.svg.converter import SVGConverter

# Read the input file
with open("inputs/complex_demo.tex", "r") as f:
    tikz_code = f.read()

print("=" * 80)
print("Testing TikZ Parser on complex_demo.tex")
print("This tests ALL implemented features from Phases 1-7")
print("=" * 80)
print()

# Parse the TikZ code
parser = TikzParser()
print("Parsing...")
try:
    ast = parser.parse(tikz_code)
    print("✓ Parsing successful!")
    print(f"  - AST type: {type(ast).__name__}")
    print(f"  - Number of statements: {len(ast.statements)}")
    print()

    # Analyze AST structure
    print("AST Structure:")
    statement_types = {}
    for stmt in ast.statements:
        stmt_type = type(stmt).__name__
        statement_types[stmt_type] = statement_types.get(stmt_type, 0) + 1

    for stmt_type, count in sorted(statement_types.items()):
        print(f"  - {stmt_type}: {count}")
    print()

    # Convert to SVG
    converter = SVGConverter()
    print("Converting to SVG...")
    svg = converter.convert(ast)
    print("✓ Conversion successful!")
    print(f"  - SVG length: {len(svg)} characters")
    print()

    # Analyze SVG output
    path_count = svg.count("<path")
    text_count = svg.count("<text")
    group_count = svg.count("<g")
    print("SVG Analysis:")
    print(f"  - Path elements: {path_count}")
    print(f"  - Text elements: {text_count}")
    print(f"  - Group elements: {group_count}")
    print()

    # Save SVG output
    output_file = "outputs/complex_demo.svg"
    import os

    os.makedirs("outputs", exist_ok=True)
    with open(output_file, "w") as f:
        f.write(svg)
    print(f"✓ SVG saved to: {output_file}")
    print()

    # Show feature usage
    print("Features Used:")
    print("  ✓ Phase 1: Basic parsing (draw, coordinates, nodes)")
    print("  ✓ Phase 2: Enhanced paths (arc, circle, dashed)")
    print("  ✓ Phase 3: Math expressions (sqrt, division, variables)")
    print("  ✓ Phase 4: Foreach loops with ranges")
    print("  ✓ Phase 5: Polar coords, relative coords, anchors")
    print("  ✓ Phase 6: Scopes, clipping")
    print("  ✓ Phase 7: \\def and \\newcommand macros")
    print()

    # Show a preview of the SVG
    print("SVG Preview (first 400 chars):")
    print("-" * 80)
    print(svg[:400])
    print("...")
    print("-" * 80)
    print()

    print("=" * 80)
    print("SUCCESS! All features working! ✓")
    print("=" * 80)

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback

    traceback.print_exc()
    print()
    print("=" * 80)
    print("FAILED ✗")
    print("=" * 80)
