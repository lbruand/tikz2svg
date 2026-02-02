# TikZ to SVG Converter

A high-performance native Python TikZ to SVG converter that replaces the pdflatex/pdf2svg pipeline with a pure Python solution.

[![CI](https://github.com/lbruand/tikz2svg/actions/workflows/ci.yml/badge.svg)](https://github.com/lbruand/tikz2svg/actions/workflows/ci.yml)
[![Code Quality](https://github.com/lbruand/tikz2svg/actions/workflows/quality.yml/badge.svg)](https://github.com/lbruand/tikz2svg/actions/workflows/quality.yml)
[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
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

## Supported Features (Phase 1)

### Commands
- `\draw` - Line drawing
- `\fill` - Filled shapes
- `\filldraw` - Combined fill and draw
- `\node` - Text labels
- `\coordinate` - Named coordinates

### Coordinates
- Cartesian: `(x,y)`
- Polar: `(angle:radius)`
- Named: `(A)`, `(B)`
- Relative: `++(dx,dy)`

### Path Operations
- `--` - Straight lines
- `..` - Curves (simplified)
- `|-` and `-|` - Orthogonal lines
- `cycle` - Close path

### Styling
- Colors: red, blue, green, etc.
- Line widths: thick, thin, ultra thick, etc.
- Dash patterns: dashed, dotted
- Opacity support

## Example

**Input (TikZ):**
```latex
\begin{tikzpicture}
  \draw[red,thick] (0,0) -- (2,2);
  \fill[blue] (3,0) -- (4,0) -- (3.5,1) -- cycle;
  \node at (1,1) {Hello};
\end{tikzpicture}
```

**Output:** Valid SVG with proper paths, colors, and text

## Architecture

```
tikz2svg/
├── tikz2svg/           # Main package
│   ├── parser/         # TikZ parser (Lark + EBNF)
│   │   ├── grammar.lark
│   │   ├── ast_nodes.py
│   │   ├── parser.py
│   │   └── preprocessor.py
│   ├── svg/            # SVG converter
│   │   ├── converter.py
│   │   ├── geometry.py
│   │   └── styles.py
│   └── cli.py          # Command-line interface
├── tests/              # Test suite
└── pyproject.toml      # Package configuration
```

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
24 tests, 24 passed (100%)
Coverage: 67%
```

## Performance Benchmark

| Tool | Time | Notes |
|------|------|-------|
| **tikz2svg** | **< 100ms** | Native Python |
| pdflatex + pdf2svg | ~2-3s | Requires LaTeX |

## Roadmap

- **Phase 1** (✓ Complete): Basic parser and converter
- **Phase 2**: Enhanced path operations, arcs, arrows
- **Phase 3**: Math expressions in coordinates
- **Phase 4**: `\foreach` loops
- **Phase 5**: 3D coordinates
- **Phase 6**: Scopes, layers, clipping
- **Phase 7**: Macro expansion

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

MIT License - see LICENSE file for details

## Credits

- Built with [Lark](https://github.com/lark-parser/lark) parser
- Inspired by the TikZ & PGF LaTeX package

## Links

- GitHub: https://github.com/lbruand/tikz2svg
- TikZ Manual: https://pgf-tikz.github.io/pgf/pgfmanual.pdf
- Issues: https://github.com/lbruand/tikz2svg/issues
