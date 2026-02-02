#!/usr/bin/env python3
"""
Convert TikZ LaTeX files to SVG using pdflatex and pdf2svg
"""
import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path


def convert_tex_to_svg(input_path, output_path):
    """
    Convert a LaTeX file to SVG using pdflatex and pdf2svg

    Args:
        input_path: Path to the input .tex file
        output_path: Path for the output .svg file
    """
    input_path = Path(input_path)
    output_path = Path(output_path)

    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)

    # Create output directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Create a temporary directory for compilation
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Copy the input file to temp directory
        temp_tex = tmpdir / input_path.name
        shutil.copy(input_path, temp_tex)

        # Compile LaTeX to PDF
        print(f"Compiling {input_path.name} to PDF...")
        result = subprocess.run(
            ['pdflatex', '-interaction=nonstopmode', '-shell-escape', str(temp_tex)],
            cwd=tmpdir,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print("Error during pdflatex compilation:")
            print(result.stdout)
            print(result.stderr)
            sys.exit(1)

        # Find the generated PDF
        pdf_file = tmpdir / input_path.with_suffix('.pdf').name

        if not pdf_file.exists():
            print(f"Error: PDF file was not generated: {pdf_file}")
            sys.exit(1)

        # Convert PDF to SVG
        print(f"Converting PDF to SVG...")
        result = subprocess.run(
            ['pdf2svg', str(pdf_file), str(output_path)],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print("Error during pdf2svg conversion:")
            print(result.stdout)
            print(result.stderr)
            sys.exit(1)

    print(f"✓ Successfully created {output_path}")


if __name__ == '__main__':
    # Default: convert input01.tex to output01.svg
    input_file = 'inputs/input01.tex'
    output_file = 'outputs/input01.svg'

    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]

    convert_tex_to_svg(input_file, output_file)