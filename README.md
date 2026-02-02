# TikZ to SVG Converter & Library Builder

A collection of tools to convert TikZ LaTeX graphics to SVG and build a library of TikZ examples from [TeXample.net](https://texample.net/tikz/examples/all/).

## Tools

### 1. `convert.py` - Single file converter
Converts a single TikZ LaTeX file to SVG.

```bash
# Convert a specific file
python3 convert.py inputs/input01.tex outputs/input01.svg

# Default: converts inputs/input01.tex → outputs/input01.svg
python3 convert.py
```

### 2. `scrape_tikz.py` - Gallery scraper
Downloads TikZ examples from TeXample.net with metadata.

```bash
# Download first 10 examples
python3 scrape_tikz.py --max-examples 10

# Download first 5 pages (60 examples)
python3 scrape_tikz.py --max-pages 5

# Download all examples (420+)
python3 scrape_tikz.py

# Custom output directory
python3 scrape_tikz.py --output my_library --max-examples 20
```

Each example is saved as:
- `XXXX-example-name.tex` - The TikZ source code
- `XXXX-example-name.json` - Metadata (title, author, date, tags, categories, URL)

### 3. `batch_convert.py` - Batch converter
Converts all .tex files in a directory to SVG.

```bash
# Convert all files in library/
python3 batch_convert.py

# Custom directories
python3 batch_convert.py --input library --output library/svg

# Convert specific pattern
python3 batch_convert.py --pattern "0001-*.tex"
```

## Directory Structure

```
tikz2svg/
├── inputs/          # Input TikZ files
├── outputs/         # Converted SVG outputs
├── library/         # Downloaded TikZ examples
│   ├── *.tex        # TikZ source files
│   ├── *.json       # Metadata files
│   └── svg/         # Converted SVG files
├── convert.py       # Single file converter
├── scrape_tikz.py   # Gallery scraper
└── batch_convert.py # Batch converter
```

## Requirements

- Python 3.12+
- pdflatex (from TeX distribution)
- pdf2svg
- Python packages: requests, beautifulsoup4

## Installation

```bash
# Install Python dependencies
uv pip install requests beautifulsoup4

# Install system dependencies (Ubuntu/Debian)
sudo apt-get install texlive-latex-base texlive-latex-extra pdf2svg

# macOS
brew install pdf2svg
brew install --cask mactex
```

## Example Workflow

1. Scrape examples from TeXample.net:
```bash
python3 scrape_tikz.py --max-examples 50
```

2. Convert all to SVG:
```bash
python3 batch_convert.py
```

3. Your SVG files will be in `library/svg/`

## Gallery Sources

The scraper downloads examples from:
- **TeXample.net**: https://texample.net/tikz/examples/all/ (420+ examples)

Other excellent TikZ resources:
- **TikZ.net**: https://tikz.net/
- **TikZ Gallery**: https://tikz.pablopie.xyz/
- **TikZ.dev**: https://tikz.dev/ (official documentation)
- **Overleaf**: https://www.overleaf.com/gallery/tagged/tikz

## License

The conversion scripts are provided as-is. Downloaded TikZ examples maintain their original licenses (typically Creative Commons Attribution-ShareAlike 4.0).