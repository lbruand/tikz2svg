#!/usr/bin/env python3
"""Test the TikZ parser on the Sri Yantra library example (0001-sri-yantra.tex)."""

from tikz2svg.parser.parser import TikzParser
from tikz2svg.svg.converter import SVGConverter

# Read the input file
with open('library/0001-sri-yantra.tex', 'r') as f:
    tikz_code = f.read()

print("=" * 80)
print("Testing TikZ Parser on Sri Yantra (Complex Library Example)")
print("=" * 80)
print()

print("File Info:")
print(f"  - Lines: {len(tikz_code.splitlines())}")
print(f"  - Characters: {len(tikz_code)}")
print()

print("Features Used in This File:")
print("  - \\pgfdeclarelayer (layer management)")
print("  - \\pgfsetlayers (layer ordering)")
print("  - \\def macros (simple substitution)")
print("  - \\newcommand with parameters")
print("  - \\ifnum conditionals (NOT IMPLEMENTED)")
print("  - \\ifx conditionals (NOT IMPLEMENTED)")
print("  - Recursive macros (PARTIAL)")
print("  - \\foreach with evaluate")
print("  - Bezier curves with controls (PARTIAL)")
print("  - Scopes and pgfonlayer")
print("  - Complex node positioning")
print()

# Parse the TikZ code
parser = TikzParser()
print("Attempting to parse...")
print("-" * 80)
try:
    ast = parser.parse(tikz_code)
    print(f"✓ Parsing successful!")
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
    print(f"✓ Conversion successful!")
    print(f"  - SVG length: {len(svg)} characters")
    print()

    # Analyze SVG output
    path_count = svg.count('<path')
    text_count = svg.count('<text')
    group_count = svg.count('<g')
    circle_count = svg.count('circle')

    print(f"SVG Analysis:")
    print(f"  - Path elements: {path_count}")
    print(f"  - Text elements: {text_count}")
    print(f"  - Group elements: {group_count}")
    print(f"  - Circle operations: {circle_count}")
    print()

    # Save SVG output
    output_file = 'outputs/sri-yantra.svg'
    import os
    os.makedirs('outputs', exist_ok=True)
    with open(output_file, 'w') as f:
        f.write(svg)
    print(f"✓ SVG saved to: {output_file}")
    print()

    # Show a preview
    print("SVG Preview (first 500 chars):")
    print("-" * 80)
    print(svg[:500])
    print("...")
    print("-" * 80)
    print()

    print("=" * 80)
    print("PARTIAL SUCCESS! ✓")
    print("=" * 80)
    print()
    print("Note: Some advanced features may not render correctly:")
    print("  - Conditionals (\\ifnum, \\ifx) are not supported")
    print("  - Recursive macros may not expand fully")
    print("  - Some Bezier curve syntax may be simplified")
    print()

except Exception as e:
    print(f"✗ Error during parsing: {e}")
    print()
    print("This is expected - the file uses advanced features:")
    print("  - Conditionals (\\ifnum, \\ifx)")
    print("  - Recursive macro expansion with \\expandafter")
    print("  - Complex Bezier curve syntax")
    print()
    print("Error details:")
    print("-" * 80)
    import traceback
    traceback.print_exc()
    print("-" * 80)
    print()
    print("=" * 80)
    print("EXPECTED FAILURE - Advanced Features Not Implemented")
    print("=" * 80)
