# Claude Code Guidelines

This document contains coding style preferences and guidelines for working on the tikz2svg codebase.

## Code Style Preferences

### Control Flow

#### ❌ Avoid: `continue` Statements

Do not use `continue` in loops. Instead, use if/elif chains or boolean flags.

**Bad:**
```python
for item in items:
    if not condition:
        continue
    process(item)
```

**Good:**
```python
for item in items:
    if condition:
        process(item)
```

#### ❌ Avoid: Early Returns

Avoid early returns in the middle of functions. Prefer a single return at the end, or use conditional expressions.

**Bad:**
```python
def find_color(options):
    for color in COLORS:
        if color in options:
            return COLORS[color]
    return default
```

**Good:**
```python
def find_color(options):
    return next(
        (COLORS[color] for color in COLORS if color in options),
        default
    )
```

### Functional Programming

#### ✅ Prefer: List/Dict/Set Comprehensions

Use comprehensions instead of for loops when building collections.

**Bad:**
```python
results = []
for item in items:
    if condition(item):
        results.append(transform(item))
```

**Good:**
```python
results = [transform(item) for item in items if condition(item)]
```

#### ✅ Prefer: Generator Expressions

Use generator expressions with built-in functions like `any()`, `all()`, `sum()`, `max()`, etc.

**Bad:**
```python
found = False
for item in items:
    if check(item):
        found = True
        break
return found
```

**Good:**
```python
return any(check(item) for item in items)
```

#### ✅ Prefer: Functional Patterns

Use functional programming patterns where practical:
- `map()`, `filter()` for transformations
- `any()`, `all()` for boolean checks
- `next()` with generators for finding items
- Walrus operator (`:=`) for comprehensions with filtering

**Examples:**
```python
# Filtering and transforming
elements = [element for stmt in statements if (element := process(stmt))]

# Boolean checks
has_arrows = any(isinstance(s, DrawStatement) and "arrow" in s.options for s in statements)

# Finding items
first_match = next((item for item in items if condition(item)), default)
```

### When Loops Are Acceptable

Traditional for loops are acceptable when:

1. **Complex state management** - Tracking multiple variables across iterations
2. **Context management** - Using try/finally or with statements
3. **Side effects required** - I/O operations, external state updates
4. **Exception handling** - Multiple try/except blocks needed
5. **Readability** - Comprehension would be too complex to understand

**Example where loop is better:**
```python
# Complex stateful processing - loop is clearer
for segment in path.segments:
    if segment.operation == "move":
        current_pos = resolve(segment.destination)
    elif segment.operation == "line":
        path_data.append(f"L {current_pos[0]} {current_pos[1]}")
        current_pos = update_position(current_pos, segment)
```

## Architecture

### Current Structure

```
tikz2svg/
├── parser/          # TikZ parsing (Lark grammar-based)
├── evaluator/       # Expression and macro evaluation
└── svg/            # SVG generation
    ├── converter.py           # Main orchestrator (visitor pattern)
    ├── path_renderer.py       # Path rendering logic
    ├── coordinate_resolver.py # Coordinate system handling
    └── option_processor.py    # Option evaluation
```

### Design Principles

1. **Single Responsibility** - Each class has one clear purpose
2. **Separation of Concerns** - Parsing, evaluation, and rendering are separate
3. **Dependency Injection** - Components receive dependencies via constructor
4. **Visitor Pattern** - AST traversal uses visitor pattern
5. **No God Classes** - Refactored from 634-line converter to 4 focused classes

## Testing Philosophy

### Test Coverage Goals

- **Unit tests** for all refactored classes
- **Coverage target**: 95%+ for core logic
- **Test each component** in isolation where possible

### Current Coverage

| Component | Coverage | Status |
|-----------|----------|--------|
| PathRenderer | 97% | ✅ Excellent |
| CoordinateResolver | 100% | ✅ Perfect |
| OptionProcessor | 100% | ✅ Perfect |
| Overall svg/ | 83% | ✅ Good |

## Refactoring History

### Major Refactorings

1. **Code Duplication Elimination** - Removed ~95 lines of duplicates
2. **Continue Statement Removal** - Converted all to if/elif chains
3. **Converter Class Split** - 634 lines → 4 focused classes (291 lines each)
4. **Unit Test Addition** - Added 63 unit tests for refactored classes
5. **Loop to Comprehension** - Converted 5 simple loops to comprehensions

### Before/After Metrics

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| converter.py size | 634 lines | 291 lines | -54% |
| Methods per class | 21 | ~10 | -52% |
| Test coverage | 69% | 83% | +14% |
| Total tests | 122 | 185 | +63 |

## Common Patterns

### Processing Collections

```python
# Filter and transform with walrus operator
results = [
    transformed
    for item in items
    if (transformed := transform(item))
]

# Extend with generator
collection.extend(
    process(item)
    for item in items
    if condition(item)
)
```

### Coordinate Resolution

```python
# Always use CoordinateResolver
pos = self.coord_resolver.resolve(coordinate, current_pos)

# Evaluate numeric values
value = self.coord_resolver.eval_value(expression)
```

### Option Processing

```python
# Always use OptionProcessor for option evaluation
processed_options = self.option_processor.process(raw_options)

# Safe evaluation with fallback
value = self.option_processor.safe_evaluate(expr, evaluator)
```

### Path Rendering

```python
# Always use PathRenderer for path generation
path_data = self.path_renderer.render_path(path_ast)

# Render arcs
arc_command = self.path_renderer.render_arc(arc_spec, current_pos)
```

## Git Commit Style

### Commit Message Format

```
Short description (imperative mood)

- Detailed bullet points of changes
- Coverage improvements
- Metrics

All tests pass (X/Y). Code quality checks pass.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

### Commit Frequency

- Commit after each logical change
- Run tests before each commit
- Run quality checks (black, ruff) before committing
- Keep commits focused on one concern

## Code Quality Tools

### Required Checks

```bash
# Format code
black tikz2svg/

# Lint code
ruff check tikz2svg/

# Run tests
pytest --tb=short -q

# Check coverage
pytest --cov=tikz2svg/svg --cov-report=term
```

All must pass before committing.

## Future Improvements

### Potential Enhancements

- Increase styles.py coverage (currently 51%)
- Add visual regression tests for complex examples
- Implement more TikZ features (decorations, plots, etc.)
- Optimize performance for large diagrams
- Add caching for repeated coordinate calculations

### Known Limitations

- Not all TikZ features supported (focus on common 50 commands)
- 3D rendering uses pre-calculated projections
- Macro expansion is template-based, not full TeX
- Some curve accuracy differences from pdflatex output acceptable

## Documentation

### Key Documents

- `CONVERTER_REFACTORING_PLAN.md` - Details of converter split
- `UNIT_TESTING_SUMMARY.md` - Test coverage improvements
- `REFACTORING_SUMMARY.md` - Code duplication elimination
- `CODE_DUPLICATION_REPORT.md` - Initial duplication analysis

### Reading Order for New Contributors

1. This document (CLAUDE.md) - Style and preferences
2. README.md - Project overview and usage
3. CONVERTER_REFACTORING_PLAN.md - Architecture decisions
4. Source code in order: parser → evaluator → svg

## Philosophy

> "Code should be written for humans first, machines second."

- Prefer clarity over cleverness
- Prefer functional over imperative when equally clear
- Prefer composition over inheritance
- Prefer explicit over implicit
- Prefer simple over complex

## Questions?

When in doubt:
1. Check existing code patterns
2. Refer to this document
3. Run tests to validate
4. Keep it simple and readable

---

**Last Updated:** 2026-02-03
**Maintainer:** lucas (with Claude Code assistance)
