# Bug Fix: Bezier Curve Rendering

## Issue

Bezier curves with control points were rendering as M (move) commands instead of Q (quadratic Bezier) or C (cubic Bezier) commands, causing significant visual defects where curves appeared as invisible gaps.

### Example

TikZ code:
```latex
\draw (0,0) .. controls (1,0) .. (2,0);
```

**Before fix**: Produced `M 250.00 250.00 M 306.70 250.00` (two moves, no curve)
**After fix**: Produces `M 250.00 250.00 Q 278.35 250.00 306.70 250.00` (proper quadratic Bezier)

## Root Cause

In `tikz2svg/parser/parser.py`, the `path()` transformer (lines 72-154) handles path elements and connectors. When processing items:

1. Coordinate items → Create path segments
2. String items → Store as `current_operation` for next coordinate
3. Dict items with `"coord"` → Handle coordinate with modifiers
4. Dict items with `"_type" == "cycle"` → Add cycle segment

**Missing**: No handler for dict items representing complex operations (controls, arc, circle).

When `path_connector` returned `{"_type": "controls", "points": [...]}` for Bezier curves, the dict was skipped, leaving `current_operation = None`. The next coordinate defaulted to operation="move" (line 117 or 142).

## Fix

Added handler for dict-type operations in the `path()` transformer:

```python
elif isinstance(item, dict):
    # This could be a complex operation (controls, arc, circle) or cycle
    if item.get("_type") == "cycle":
        segments.append(PathSegment(operation="cycle"))
    else:
        # Complex operation - store for next coordinate
        current_operation = item
```

**File**: tikz2svg/parser/parser.py:146-152

## Verification

### Test Results

- All 375 tests pass (374 existing + 1 new regression test)
- Spacetime diagram now renders **225 quadratic Bezier curves** correctly
- Visual comparison shows significant improvement

### Before/After Comparison

**File**: spacetime_comparison.html

Open in browser to see side-by-side visual comparison of:
- Reference (pdflatex + pdf2svg)
- tikz2svg output (corrected)

### Spacetime Diagram Metrics

| Metric | Value |
|--------|-------|
| Quadratic Bezier (Q) commands | 225 |
| Cubic Bezier (C) commands | 0 |
| File size | 12,118 bytes (58% smaller than reference) |
| Visual fidelity | High - all curves render correctly |

## Regression Test

Added `test_bezier_curves_not_moves` in `tests/test_spacetime_example.py`:

```python
def test_bezier_curves_not_moves(self, spacetime_code):
    """Regression: ensure Bezier curves render as Q/C commands, not M (move)."""
    parser = TikzParser()
    ast = parser.parse(spacetime_code)
    converter = SVGConverter()
    svg = converter.convert(ast)

    q_count = svg.count(" Q ")
    c_count = svg.count(" C ")

    assert q_count + c_count > 0, "Bezier curves should produce Q or C commands"
    assert q_count > 200, f"Expected >200 Q commands, got {q_count}"
```

## Impact

This fix resolves a critical rendering issue that affected all TikZ diagrams using Bezier curves with control points:
- `.. controls (x1,y1) ..` syntax
- Smooth curves for mathematical diagrams
- Complex paths in scientific illustrations

All such curves now render correctly with proper SVG curve commands.

## Files Changed

1. **tikz2svg/parser/parser.py** - Added dict operation handler
2. **tests/test_spacetime_example.py** - Added regression test
3. **SPACETIME_COMPARISON.md** - Documented the bug and fix
4. **spacetime_comparison.html** - Updated with corrected output
5. **test_spacetime.svg** - Regenerated with fix

## Related Issues

Previously, the spacetime diagram comparison showed tikz2svg "looking bad" compared to pdflatex because:
1. Bezier curves were invisible (M commands instead of Q/C)
2. Visual structure was broken

Both issues are now resolved. The output is visually accurate and efficient.
