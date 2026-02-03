#!/usr/bin/env python3
"""
Batch convert all TikZ files in the library to SVG
"""

import sys
from pathlib import Path

from convert import convert_tex_to_svg


def batch_convert(input_dir="library", output_dir="library/svg", pattern="*.tex"):
    """Convert all .tex files in input_dir to SVG"""
    input_path = Path(input_dir)
    output_path = Path(output_dir)

    if not input_path.exists():
        print(f"Error: Input directory not found: {input_path}")
        sys.exit(1)

    # Create output directory
    output_path.mkdir(parents=True, exist_ok=True)

    # Find all .tex files
    tex_files = sorted(input_path.glob(pattern))

    if not tex_files:
        print(f"No .tex files found in {input_path}")
        return

    print(f"Found {len(tex_files)} TikZ files to convert")
    print(f"Input:  {input_path.absolute()}")
    print(f"Output: {output_path.absolute()}")
    print("-" * 60)

    success_count = 0
    failed = []

    for i, tex_file in enumerate(tex_files, 1):
        svg_file = output_path / tex_file.with_suffix(".svg").name
        print(f"[{i}/{len(tex_files)}] {tex_file.name}")

        try:
            convert_tex_to_svg(tex_file, svg_file)
            success_count += 1
        except Exception as e:
            print(f"  ✗ Error: {e}")
            failed.append(tex_file.name)

    print("-" * 60)
    print(f"\n✓ Successfully converted {success_count}/{len(tex_files)} files")

    if failed:
        print(f"\n✗ Failed to convert {len(failed)} files:")
        for name in failed:
            print(f"  - {name}")

    print(f"\nSVG files saved to: {output_path.absolute()}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Batch convert TikZ files to SVG")
    parser.add_argument(
        "--input",
        "-i",
        default="library",
        help="Input directory containing .tex files (default: library)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="library/svg",
        help="Output directory for .svg files (default: library/svg)",
    )
    parser.add_argument(
        "--pattern", "-p", default="*.tex", help="File pattern to match (default: *.tex)"
    )

    args = parser.parse_args()

    batch_convert(args.input, args.output, args.pattern)
