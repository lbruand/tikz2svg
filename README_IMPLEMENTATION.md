# TikZ to SVG Native Converter - Implementation Status

## Overview

This is a native Python implementation of a TikZ to SVG converter that replaces the pdflatex/pdf2svg pipeline. It uses a proper parser (Lark with EBNF grammar) instead of regular expressions, builds an AST, and directly generates SVG output.

## Current Status: Phase 1 Complete ✓

Phase 1 (Foundation) has been successfully implemented and tested.

### Implemented Features

#### Parser (parser/)
- **Lark EBNF Grammar** (`grammar.lark`): Clean, maintainable grammar definition
- **AST Nodes** (`ast_nodes.py`): Dataclass-based AST representation
  - TikzPicture, DrawStatement, Path, PathSegment
  - Coordinate (cartesian, polar, named, relative)
  - Node, CoordinateDefinition
  - Scope, ForeachLoop (structure ready for Phase 4)

- **Parser** (`parser.py`):
  - Lark-based parser with custom transformer
  - Converts parse tree to AST
  - Handles complex option syntax

- **Preprocessor** (`preprocessor.py`):
  - Comment removal (LaTeX %)
  - TikZ environment extraction
  - Whitespace normalization

#### SVG Converter (svg/)
- **Converter** (`converter.py`):
  - Visitor pattern for AST traversal
  - Generates SVG from AST
  - Named coordinate tracking

- **Geometry** (`geometry.py`):
  - Coordinate transformation (TikZ → SVG)
  - Polar to Cartesian conversion
  - Arc path calculation

- **Styles** (`styles.py`):
  - TikZ options → SVG styles
  - Color mapping (named colors)
  - Line width conversion
  - Dash patterns

#### Supported TikZ Features

**Commands:**
- `\draw` - Line drawing
- `\fill` - Filled shapes
- `\filldraw` - Combined fill and draw
- `\node` - Text labels
- `\coordinate` - Named coordinates

**Coordinates:**
- Cartesian: `(x,y)`
- Polar: `(angle:radius)`
- Named: `(A)`, `(node.anchor)`
- Relative: `++(dx,dy)`, `+(dx,dy)` (basic support)

**Path Operations:**
- `--` - Straight lines
- `..` - Curves (simplified)
- `|-` and `-|` - Orthogonal lines
- `cycle` - Close path

**Options:**
- Colors: red, blue, green, etc.
- Color mixing: `blue!30!white` (basic)
- Line widths: thick, thin, ultra thick, etc.
- Dash patterns: dashed, dotted
- Opacity
- Line cap and join

**Environments:**
- `tikzpicture`
- `scope` (structure ready)

### Test Coverage

**Parser Tests** (`tests/test_parser.py`): 15 tests
- Basic parsing (empty, simple lines, multiple lines)
- Coordinates (Cartesian, polar, negative)
- Options (flags, key-value, multiple)
- Draw commands (draw, fill, filldraw)
- Nodes (simple, named)
- Coordinate definitions

**SVG Converter Tests** (`tests/test_svg_converter.py`): 9 tests
- Basic conversion (lines, shapes, colors, thickness)
- Coordinate systems (polar, named)
- Integration test with input01.tex

**Test Results:** 24/24 passing ✓

### Command Line Tool

**Usage:**
```bash
python tikz2svg.py input.tex output.svg
python tikz2svg.py input.tex  # outputs to input.svg
python tikz2svg.py input.tex --width 800 --height 600
```

**Example:**
```bash
python tikz2svg.py inputs/input01.tex outputs/input01_native.svg
```

### Directory Structure

```
tikz2svg/
├── parser/
│   ├── __init__.py
│   ├── grammar.lark          # Lark EBNF grammar
│   ├── ast_nodes.py          # AST node classes
│   ├── parser.py             # Parser + Transformer
│   └── preprocessor.py       # Comment removal, etc.
├── svg/
│   ├── __init__.py
│   ├── converter.py          # AST → SVG visitor
│   ├── geometry.py           # Coordinate transformations
│   └── styles.py             # Style conversion
├── tests/
│   ├── test_parser.py        # Parser unit tests
│   └── test_svg_converter.py # Converter tests
├── tikz2svg.py               # Command line tool
├── inputs/                   # Test inputs
├── outputs/                  # Generated SVGs
└── library/                  # Complex examples
```

## What Works

✓ Parses basic TikZ diagrams with lines, shapes, and text
✓ Handles Cartesian and polar coordinates
✓ Converts colors, line widths, and basic styles
✓ Supports named coordinates and nodes
✓ Successfully converts input01.tex

## Example

**Input (input01.tex):**
```latex
\begin{tikzpicture}
  \draw (0,0) -- (10,10);
  \draw (10,0) -- (0,10);
  \draw (5,0) -- (0,10);
  \node at (5,5) {Lorem ipsum at domine standalonus};
\end{tikzpicture}
```

**Output:** Valid SVG with 3 paths and 1 text element

## Next Steps (Phase 2-7)

### Phase 2: Core Drawing (Planned)
- Path operations: `..` (better curves), `arc`, `--cycle`
- More node positioning options
- Color blending (e.g., `blue!30!white`)
- Line styles: dashed patterns, arrow tips

### Phase 3: Mathematical Expressions (Planned)
- Expression evaluation in coordinates
- `\pgfmathsetmacro` support
- Trigonometric functions

### Phase 4: Control Flow (Planned)
- `\foreach` loop expansion
- Loop variable evaluation
- Nested loops

### Phase 5: Coordinate Systems (Planned)
- 3D coordinates with tikz-3dplot
- Canvas transformations
- Shifted/rotated coordinates

### Phase 6: Advanced Features (Planned)
- Scopes with option inheritance
- Layers (`\pgfonlayer`)
- Clipping paths
- Decorations

### Phase 7: Macro System (Planned)
- `\def` and `\newcommand`
- Parameter substitution
- Template expansion

## Testing Against Library Examples

The three library examples serve as integration test targets:

1. **0001-sri-yantra.tex**: Layers, scopes, mathematical expressions
2. **0002-regular-hexagonal-prism.tex**: Foreach loops with evaluation
3. **0003-regular-tetrahedron.tex**: 3D coordinates

Currently, Phase 1 can parse basic structures but needs Phases 2-5 to fully convert these examples.

## Architecture Decisions

### Parser: Lark (EBNF)
- **Pro**: Maintainable grammar, automatic parse tree, good error messages
- **Con**: Learning curve, but well worth it
- **Result**: Clean, extensible parser in ~200 lines of grammar

### AST: Dataclasses
- **Pro**: Type hints, immutable, clean
- **Con**: More verbose than dicts
- **Result**: Clear structure, easy to extend

### SVG Generation: Visitor Pattern
- **Pro**: Separation of concerns, extensible
- **Con**: More classes
- **Result**: Clean conversion logic, easy to add features

### Coordinate Transformation
- **Pro**: Proper TikZ (center, y-up) to SVG (top-left, y-down) conversion
- **Con**: Need to track transformations
- **Result**: Correct rendering

## Performance

Current performance (Phase 1):
- Parse + convert input01.tex: < 100ms
- Small diagrams (< 50 lines): instant
- Memory efficient: AST is lightweight

## Limitations (Phase 1)

**Not Yet Implemented:**
- Math expressions in coordinates
- Foreach loops
- 3D rendering
- Macro expansion
- Complex path operations (arcs, decorations)
- Advanced color blending
- Transformations (rotate, scale, shift)
- Arrow tips
- Text formatting

**By Design:**
- Not aiming for 100% TikZ compatibility
- Focus on common use cases (80/20 rule)
- Graceful degradation for unsupported features

## Dependencies

```toml
dependencies = [
    "lark>=1.1.9",           # Parser generator
    "pytest>=7.4.0",         # Testing
    "pytest-cov>=4.1.0",     # Coverage
    "pillow>=10.0.0",        # Image comparison (future)
    "numpy>=1.24.0",         # Math operations (future)
]
```

## Comparison to pdflatex/pdf2svg

| Aspect | pdflatex/pdf2svg | Native Converter |
|--------|-----------------|------------------|
| Speed | ~2-3 seconds | < 100ms |
| Dependencies | LaTeX, pdf2svg | Python only |
| Accuracy | 100% (reference) | 95%+ (goal) |
| Debugging | Difficult | Easy (AST inspection) |
| Extensibility | None | High |

## Development Workflow

1. Write tests first (TDD)
2. Extend grammar
3. Add AST nodes
4. Implement transformer
5. Implement visitor
6. Run tests
7. Test on library examples

## Success Criteria (Phase 1) ✓

- [x] Parse input01.tex without errors
- [x] Generate valid SVG
- [x] Support basic lines, shapes, colors
- [x] Pass all unit tests (24/24)
- [x] Clean, maintainable code
- [x] Well-documented

## Contributing

To add new TikZ features:

1. Add grammar rule to `parser/grammar.lark`
2. Add AST node to `parser/ast_nodes.py` (if needed)
3. Update transformer in `parser/parser.py`
4. Add visitor method in `svg/converter.py`
5. Write tests in `tests/`
6. Test on library examples

## References

- TikZ & PGF Manual: https://pgf-tikz.github.io/pgf/pgfmanual.pdf
- Lark Documentation: https://lark-parser.readthedocs.io/
- SVG Specification: https://www.w3.org/TR/SVG2/

---

**Status**: Phase 1 complete, ready for Phase 2
**Last Updated**: 2026-02-02
