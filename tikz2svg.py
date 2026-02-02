#!/usr/bin/env python3
"""
TikZ to SVG converter - Entry point script.

This is a convenience wrapper that calls the main CLI module.
You can also run: python -m tikz2svg.cli
"""

import sys

from tikz2svg.cli import main

if __name__ == "__main__":
    sys.exit(main())
