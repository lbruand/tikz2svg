"""
TikZ to SVG Converter - Native Python implementation.

A high-performance TikZ parser and SVG converter that replaces the pdflatex/pdf2svg
pipeline with a pure Python solution using Lark parser and proper AST representation.
"""

__version__ = "0.1.0"
__author__ = "Lucas Bruand"

from .parser.parser import TikzParser
from .svg.converter import SVGConverter

__all__ = ["TikzParser", "SVGConverter", "__version__"]
