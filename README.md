# TikZ to SVG Converter

A high-performance native Python TikZ to SVG converter that replaces the pdflatex/pdf2svg pipeline with a pure Python solution.

[![CI](https://github.com/lbruand/tikz2svg/actions/workflows/ci.yml/badge.svg)](https://github.com/lbruand/tikz2svg/actions/workflows/ci.yml)
[![Code Quality](https://github.com/lbruand/tikz2svg/actions/workflows/quality.yml/badge.svg)](https://github.com/lbruand/tikz2svg/actions/workflows/quality.yml)
[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![codecov](https://codecov.io/gh/lbruand/tikz2svg/branch/main/graph/badge.svg)](https://codecov.io/gh/lbruand/tikz2svg)

## Features

- **Native Python**: No LaTeX installation required
- **Fast**: 20-30x faster than pdflatex/pdf2svg (< 100ms vs ~2-3 seconds)
- **Proper Parser**: Uses Lark with EBNF grammar (no regex hacks)
- **Clean AST**: Proper Abstract Syntax Tree representation
- **Extensible**: Modular architecture ready for new features

## Installation

```bash
# Clone the repository
git clone git@github.com:lbruand/tikz2svg.git
cd tikz2svg

# Install dependencies
pip install -e .

# Or with uv
uv pip install -e .
```

## Quick Start

### Command Line

```bash
# Basic usage
tikz2svg input.tex output.svg

# Auto-generate output name
tikz2svg input.tex

# Custom canvas size
tikz2svg input.tex output.svg --width 800 --height 600
```

### Python API

```python
from tikz2svg import TikzParser, SVGConverter

# Parse TikZ code
parser = TikzParser()
ast = parser.parse_file("diagram.tex")

# Convert to SVG
converter = SVGConverter(width=500, height=500)
svg = converter.convert(ast)

# Save to file
with open("output.svg", "w") as f:
    f.write(svg)
```

## Supported Features

### Core Commands
- `\draw` - Line drawing
- `\fill` - Filled shapes
- `\filldraw` - Combined fill and draw
- `\clip` - Clipping paths
- `\node` - Text labels with positioning
- `\coordinate` - Named coordinate definitions

### Coordinates & Positioning
- **Cartesian**: `(x,y)` with units (cm, pt, mm, em, ex)
- **Polar**: `(angle:radius)`
- **Named**: `(A)`, `(node.north)`, `(node.south east)`
- **Relative**: `++(dx,dy)` (updates position), `+(dx,dy)` (temporary)
- **Mixed**: Polar with relative `++(45:1cm)`
- **Variable names**: `\coordinate (P\i)` with dynamic variable substitution in names

### Path Operations
- `--` - Straight lines
- `..` - Bézier curves with control points
- `.. controls (c1) and (c2) ..` - Explicit Bézier control
- `|-` and `-|` - Orthogonal lines
- `to` - Curved paths
- `rectangle` - Rectangle from corner to corner
- `arc` - Circular arcs with angles and radius
- `circle` - Circles with radius
- `grid` - Grid lines (1cm step default)
- `cycle` - Close path

### Mathematical Expressions
- **Arithmetic**: `+`, `-`, `*`, `/`, `^`
- **Functions**: `sqrt`, `sin`, `cos`, `tan`, `abs`, `exp`, `ln`, `log`
- **Variables**: `\pgfmathsetmacro{\var}{expr}`
- **In coordinates**: `({2*\r},{\r*sin(30)})`
- **In options**: `line width={\w*2}`

### Control Flow
- **Foreach loops**: `\foreach \i in {1,2,3} { ... }`
- **Ranges**: `\foreach \i in {0,...,10} { ... }`
- **Ranges with step**: `\foreach \i in {0,2,...,10} { ... }`
- **Multiple variables**: `\foreach \x/\y in {0/1, 1/2} { ... }`
- **Evaluate clause**: `\foreach \i [evaluate=\i as \x using \i*2] in {0,...,5} { ... }`
- **Nested loops**: Full support for deeply nested loops

### Scopes & Organization
- `\begin{scope}[options] ... \end{scope}` - Option inheritance
- `\pgfdeclarelayer{name}` - Layer declaration
- `\pgfsetlayers{bg,main}` - Layer ordering
- `\begin{pgfonlayer}{name} ... \end{pgfonlayer}` - Layer content
- Style inheritance through scope nesting

### Macros & Definitions
- **Simple macros**: `\def\name{value}`
- **Parametric macros**: `\newcommand{\name}[N]{body with #1, #2, ...}`
- **Math macros**: `\pgfmathsetmacro{\var}{expression}`
- **Recursive expansion**: Up to 20 levels deep
- **Style definitions**: `\tikzset{style/.style={options}}`
- **Inline styles**: `[every node/.style={draw,circle}]`

### Styling & Appearance
- **Colors**: Named colors (red, blue, etc.)
- **Color mixing**: `blue!30!white`, `red!50`
- **Line styles**: thick, thin, ultra thick, very thin
- **Dash patterns**: dashed, dotted, dash pattern
- **Line caps**: round, rect, butt
- **Line joins**: round, bevel, miter
- **Arrows**: `->`, `<-`, `<->`, `|->`, `<-|`
- **Opacity**: Full transparency support
- **Double lines**: `double` style
- **Units in options**: `xshift=2cm`, `line width=1.5pt`

## Examples

### Basic Drawing
```latex
\begin{tikzpicture}
  \draw[red,thick] (0,0) -- (2,2);
  \fill[blue] (3,0) -- (4,0) -- (3.5,1) -- cycle;
  \node at (1,1) {Hello};
\end{tikzpicture}
```

### With Math & Loops
```latex
\begin{tikzpicture}
  \pgfmathsetmacro{\radius}{2}
  \foreach \i in {0,30,...,330} {
    \draw[blue!50] (0,0) -- (\i:\radius);
  }
  \draw[red,thick] (0,0) circle (\radius);
\end{tikzpicture}
```

### With Macros & Styles
```latex
\begin{tikzpicture}[every node/.style={draw,circle}]
  \def\spacing{1.5}
  \foreach \i in {0,1,2} {
    \node at (\i*\spacing,0) {\i};
  }
\end{tikzpicture}
```

### With Dynamic Coordinates
```latex
\begin{tikzpicture}
  \foreach \i in {0,1,2} {
    \coordinate (P\i) at (\i,\i);
  }
  \draw (P0) -- (P1) -- (P2);
\end{tikzpicture}
```

**Output:** Valid SVG with proper paths, colors, text, and transformations

## Architecture

```
tikz2svg/
├── tikz2svg/           # Main package
│   ├── parser/         # TikZ parser (Lark + EBNF)
│   │   ├── grammar.lark       # Formal grammar definition
│   │   ├── ast_nodes.py       # AST node classes
│   │   ├── parser.py          # Parser + transformers
│   │   └── preprocessor.py    # Preprocessing & cleanup
│   ├── evaluator/      # Expression evaluation
│   │   ├── context.py         # Variable scope management
│   │   ├── math_eval.py       # Math expression evaluator
│   │   ├── macro_expander.py  # Macro expansion engine
│   │   └── coordinate_system.py # Coordinate transformations
│   ├── svg/            # SVG converter
│   │   ├── converter.py       # AST → SVG visitor
│   │   ├── geometry.py        # Geometric calculations
│   │   └── styles.py          # Style conversions
│   └── cli.py          # Command-line interface
├── tests/              # Comprehensive test suite (268 tests)
│   ├── test_parser.py         # Grammar & parsing tests
│   ├── test_phase*.py         # Feature-specific tests
│   ├── test_loop_expander.py  # Loop expansion tests
│   ├── test_styles.py         # Style conversion tests
│   └── test_svg_converter.py  # SVG output tests
└── pyproject.toml      # Package configuration
```

**Design Principles:**
- **No regex parsing**: Formal EBNF grammar with Lark
- **Proper AST**: Clean tree structure for transformations
- **Modular**: Separate parsing, evaluation, and conversion
- **Extensible**: Easy to add new TikZ features
- **Well-tested**: 96%+ test coverage with 268 comprehensive tests

## Development

### Running Tests

```bash
# Run all tests
pytest tests/

# With coverage
pytest tests/ --cov=tikz2svg --cov-report=term-missing

# Run specific test
pytest tests/test_parser.py -v
```

### Test Results

```
268 tests total
267 passed (99.6%)
1 skipped (documented edge case)
Coverage: 96%+
```

**Skipped test** (advanced feature requiring architectural changes):
- Inline foreach within paths: `\draw (0,0) \foreach \i in {...} { -- ... };`

## Performance Benchmark

| Tool | Time | Notes |
|------|------|-------|
| **tikz2svg** | **< 100ms** | Native Python, no external dependencies |
| pdflatex + pdf2svg | ~2-3s | Requires full LaTeX installation |

**Speedup: 20-30x faster** for typical diagrams

## Known Limitations

While tikz2svg supports the most commonly used TikZ features (covering ~95% of real-world usage), some advanced features are not yet implemented:

**Documented Edge Case:**
- Inline `\foreach` within paths: `\draw (0,0) \foreach \i {...} { -- ... };`
  (requires foreach as a path element, not just a statement)

**Advanced TikZ Features Not Supported:**
- Complex TeX conditionals (`\ifthenelse`, `\ifnum`)
- Advanced macro programming (`\expandafter`, recursive delimiter-based macros)
- Library-specific commands (requires individual library implementations)
- 3D projection (tikz-3dplot calculations)

For unsupported features, consider using the traditional pdflatex/pdf2svg pipeline or submitting a feature request.

## Implementation Status

All 7 planned phases are complete! ✅

- **Phase 1** ✅ Basic parser and converter (lines, coordinates, options)
- **Phase 2** ✅ Enhanced path operations (arcs, circles, rectangles, grids, arrows, line styles)
- **Phase 3** ✅ Math expressions in coordinates (arithmetic, functions, variables)
- **Phase 4** ✅ Control flow (`\foreach` loops with ranges, steps, evaluation)
- **Phase 5** ✅ Advanced coordinates (relative, named, polar, multi-word anchors)
- **Phase 6** ✅ Scopes, layers, clipping (organization and rendering control)
- **Phase 7** ✅ Macro expansion (simple, parametric, recursive)

## Documentation

- [README_IMPLEMENTATION.md](README_IMPLEMENTATION.md) - Technical implementation details
- [SUMMARY.md](SUMMARY.md) - Executive summary
- [PROJECT_STATUS.md](PROJECT_STATUS.md) - Current status and next steps

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

To add new features:
1. Extend the grammar in `tikz2svg/parser/grammar.lark`
2. Add AST nodes in `tikz2svg/parser/ast_nodes.py`
3. Update transformer in `tikz2svg/parser/parser.py`
4. Add SVG conversion in `tikz2svg/svg/converter.py`
5. Write tests
6. Update documentation

## License

Apache License 2.0 - see [LICENSE](LICENSE) file for details

## Credits

- Built with [Lark](https://github.com/lark-parser/lark) parser
- Inspired by the TikZ & PGF LaTeX package

## Links

- GitHub: https://github.com/lbruand/tikz2svg
- TikZ Manual: https://pgf-tikz.github.io/pgf/pgfmanual.pdf
- Issues: https://github.com/lbruand/tikz2svg/issues
