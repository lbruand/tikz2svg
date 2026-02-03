# Converter.py Refactoring Plan

## Current State

**File:** `tikz2svg/svg/converter.py`
**Lines:** 634 lines
**Methods:** 21 methods
**Responsibilities:** Too many (violates Single Responsibility Principle)

## Problem Analysis

The `SVGConverter` class has multiple responsibilities:
1. ✅ Main conversion orchestration
2. ❌ Path rendering (complex, 150+ lines)
3. ❌ Coordinate evaluation
4. ❌ Option processing
5. ❌ Arc geometry calculations
6. ❌ Arrow marker creation
7. ✅ AST visitor pattern implementation

**Red flags:**
- Single class doing path math, coordinate transforms, option evaluation, AND orchestration
- `convert_path()` method alone is 150+ lines
- Hard to test individual components in isolation
- Difficult to extend with new path operations

---

## Recommended Refactoring Strategy

### Split into 4 focused classes:

```
svg/
├── converter.py          # Main orchestrator (200 lines)
├── path_renderer.py      # Path/arc rendering (200 lines)
├── coordinate_resolver.py # Coordinate evaluation (150 lines)
└── option_processor.py   # Option evaluation (100 lines)
```

---

## Detailed Design

### 1. PathRenderer (NEW)

**File:** `tikz2svg/svg/path_renderer.py`
**Lines:** ~200
**Responsibility:** Convert TikZ path operations to SVG path data

```python
class PathRenderer:
    """Renders TikZ paths as SVG path data strings."""

    def __init__(self, coord_resolver, coord_transformer):
        self.coord_resolver = coord_resolver
        self.coord_transformer = coord_transformer

    def render_path(self, path: Path) -> str:
        """Convert Path AST to SVG path data (M, L, C, A, Z commands)."""

    def render_arc(self, arc_spec: dict, current_pos) -> str:
        """Convert TikZ arc to SVG arc command."""

    def render_circle_as_path(self, center, radius) -> list:
        """Convert circle to path commands (M, A, A, Z)."""

    def _render_line(self, dest, current_pos) -> str:
        """Generate L command."""

    def _render_curve(self, dest, controls, current_pos) -> str:
        """Generate C or Q command."""

    def _render_rectangle(self, dest, current_pos) -> list:
        """Generate rectangle path commands."""

    def _render_grid(self, dest, current_pos) -> list:
        """Generate grid path commands."""
```

**Extracted from converter.py:**
- `convert_path()` → `render_path()`
- `convert_arc()` → `render_arc()`
- Path-specific logic (lines 144-300)

---

### 2. CoordinateResolver (NEW)

**File:** `tikz2svg/svg/coordinate_resolver.py`
**Lines:** ~150
**Responsibility:** Evaluate and resolve all coordinate types

```python
class CoordinateResolver:
    """Resolves TikZ coordinates to SVG (x, y) positions."""

    def __init__(self, coord_transformer, evaluator, named_coords):
        self.coord_transformer = coord_transformer
        self.evaluator = evaluator
        self.named_coordinates = named_coords

    def resolve(self, coord: Coordinate, current_pos=None) -> Tuple[float, float]:
        """Main entry point - resolve any coordinate type."""

    def _resolve_cartesian(self, coord) -> Tuple[float, float]:
        """Resolve (x, y) coordinates."""

    def _resolve_polar(self, coord) -> Tuple[float, float]:
        """Resolve (angle:radius) coordinates."""

    def _resolve_named(self, coord) -> Tuple[float, float]:
        """Resolve named coordinates like (A) or (node.north)."""

    def _resolve_relative(self, coord, current_pos) -> Tuple[float, float]:
        """Resolve ++(dx,dy) and +(dx,dy) coordinates."""

    def eval_value(self, value) -> float:
        """Safely evaluate numeric expressions."""

    def store_named(self, name: str, position: Tuple[float, float]):
        """Store a named coordinate for later reference."""
```

**Extracted from converter.py:**
- `evaluate_coordinate()` → `resolve()`
- `_eval_value()` → `eval_value()`
- Named coordinate storage
- Coordinate-specific logic (lines 354-408)

---

### 3. OptionProcessor (NEW)

**File:** `tikz2svg/svg/option_processor.py`
**Lines:** ~100
**Responsibility:** Evaluate and process TikZ options

```python
class OptionProcessor:
    """Processes TikZ options, evaluating expressions and variables."""

    def __init__(self, evaluator):
        self.evaluator = evaluator

    def process(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate all option values that contain expressions."""

    def safe_evaluate(self, value, evaluator=None):
        """Safely evaluate value with fallback to original."""

    def _is_expression(self, value: str) -> bool:
        """Check if value looks like a math expression."""

    def _is_variable(self, value: str) -> bool:
        """Check if value is a variable reference."""
```

**Extracted from converter.py:**
- `_evaluate_options()` → `process()`
- `_safe_evaluate()` → `safe_evaluate()`
- Option-specific logic (lines 435-478)

---

### 4. SVGConverter (REFACTORED)

**File:** `tikz2svg/svg/converter.py`
**Lines:** ~200 (reduced from 634)
**Responsibility:** Orchestrate conversion and implement visitor pattern

```python
class SVGConverter:
    """Main converter orchestrating AST → SVG conversion."""

    def __init__(self, scale=28.35, width=500, height=500):
        # Initialize sub-components
        self.coord_transformer = CoordinateTransformer(scale, width//2, height//2)
        self.style_converter = StyleConverter()

        # Create specialized components
        self.coord_resolver = CoordinateResolver(
            self.coord_transformer,
            self.evaluator,
            named_coords={}
        )
        self.path_renderer = PathRenderer(
            self.coord_resolver,
            self.coord_transformer
        )
        self.option_processor = OptionProcessor(self.evaluator)

    def convert(self, ast: TikzPicture) -> str:
        """Main entry point - convert TikZ AST to SVG."""

    def visit_statement(self, stmt: ASTNode) -> Optional[str]:
        """Dispatch to appropriate visitor method."""

    def visit_draw_statement(self, stmt: DrawStatement) -> str:
        """Convert draw statement to SVG path element."""
        # Delegates to: path_renderer, option_processor, style_converter

    def visit_node(self, node: Node) -> str:
        """Convert node to SVG text element."""

    def visit_coordinate_definition(self, coord_def: CoordinateDefinition):
        """Store named coordinate."""
        # Delegates to: coord_resolver

    def visit_scope(self, scope: Scope) -> str:
        """Handle scope with context management."""

    def visit_foreach_loop(self, loop: ForeachLoop) -> str:
        """Expand and process foreach loop."""

    # Other visitor methods...

    def _check_for_arrows(self, ast: TikzPicture) -> bool:
        """Check if arrows are used in the diagram."""

    def _create_arrow_markers(self) -> str:
        """Generate SVG arrow marker definitions."""
```

**Keeps:**
- Main `convert()` orchestration
- All `visit_*()` methods (visitor pattern)
- Arrow marker handling (small, specific feature)
- Component initialization and coordination

**Delegates to new classes:**
- Path rendering → `PathRenderer`
- Coordinate resolution → `CoordinateResolver`
- Option processing → `OptionProcessor`

---

## Migration Strategy

### Phase 1: Extract CoordinateResolver (Low Risk)
**Effort:** 30 minutes
**Impact:** Clean separation of coordinate logic

1. Create `coordinate_resolver.py`
2. Move `evaluate_coordinate()` and `_eval_value()`
3. Update `SVGConverter` to use `coord_resolver.resolve()`
4. Run tests (should all pass)

### Phase 2: Extract OptionProcessor (Low Risk)
**Effort:** 20 minutes
**Impact:** Isolate option evaluation

1. Create `option_processor.py`
2. Move `_evaluate_options()` and `_safe_evaluate()`
3. Update `SVGConverter` to use `option_processor.process()`
4. Run tests

### Phase 3: Extract PathRenderer (Medium Risk)
**Effort:** 45 minutes
**Impact:** Biggest reduction in complexity

1. Create `path_renderer.py`
2. Move `convert_path()` and `convert_arc()`
3. Extract helper methods for line/curve/rectangle/grid
4. Update `visit_draw_statement()` to use `path_renderer.render_path()`
5. Run tests carefully

### Phase 4: Cleanup & Documentation (Low Risk)
**Effort:** 15 minutes

1. Add comprehensive docstrings to new classes
2. Update imports in `__init__.py`
3. Update documentation
4. Run full test suite + quality checks

**Total Effort:** ~2 hours
**Risk:** Low (incremental with tests after each phase)

---

## Benefits

### Before Refactoring
```
SVGConverter (634 lines)
├── 21 methods
├── Multiple responsibilities
└── Hard to test in isolation
```

### After Refactoring
```
SVGConverter (200 lines)       # Orchestration
├── PathRenderer (200 lines)   # Path rendering
├── CoordinateResolver (150)   # Coordinate logic
└── OptionProcessor (100)      # Option evaluation
```

### Metrics Improvement
- **Lines per file:** 634 → max 200 (68% reduction)
- **Methods per class:** 21 → max 10
- **Responsibilities:** 7 → 1-2 per class
- **Testability:** ⬆️ Can test components independently
- **Maintainability:** ⬆️ Easier to understand and modify
- **Extensibility:** ⬆️ Easy to add new coordinate types, path ops, etc.

---

## Testing Strategy

### After Each Phase
```bash
pytest tests/ -v
black --check tikz2svg/
ruff check tikz2svg/
```

### New Unit Tests
```python
# test_path_renderer.py
def test_render_line():
    renderer = PathRenderer(coord_resolver, transformer)
    result = renderer._render_line(dest=(100, 50), current_pos=(0, 0))
    assert result == "L 100.00 50.00"

# test_coordinate_resolver.py
def test_resolve_polar():
    resolver = CoordinateResolver(transformer, evaluator, {})
    result = resolver._resolve_polar(Coordinate(values=[45, 1]))
    assert result == (approx(0.707), approx(0.707))

# test_option_processor.py
def test_evaluate_expression():
    processor = OptionProcessor(evaluator)
    result = processor.process({"x": "2*3", "y": "static"})
    assert result == {"x": 6, "y": "static"}
```

---

## Alternative Approaches Considered

### ❌ Option A: Keep as single file, just organize better
**Reason rejected:** Doesn't solve the core problem of too many responsibilities

### ❌ Option B: Split into 10+ tiny classes
**Reason rejected:** Over-engineering, harder to navigate

### ✅ Option C: 4 focused classes (chosen)
**Reason:** Balanced - clear separation without over-fragmentation

---

## Implementation Checklist

- [ ] Phase 1: Extract CoordinateResolver
  - [ ] Create file
  - [ ] Move methods
  - [ ] Update imports
  - [ ] Run tests

- [ ] Phase 2: Extract OptionProcessor
  - [ ] Create file
  - [ ] Move methods
  - [ ] Update imports
  - [ ] Run tests

- [ ] Phase 3: Extract PathRenderer
  - [ ] Create file
  - [ ] Move convert_path logic
  - [ ] Move convert_arc logic
  - [ ] Extract helper methods
  - [ ] Update imports
  - [ ] Run tests

- [ ] Phase 4: Cleanup
  - [ ] Add docstrings
  - [ ] Update __init__.py
  - [ ] Update documentation
  - [ ] Final test run
  - [ ] Commit

---

## Rollback Plan

If any phase breaks tests:
1. Git stash changes
2. Investigate issue
3. Fix or revert that phase
4. Continue with remaining phases

Each phase is independent and can be reverted without affecting others.

---

Generated: 2026-02-03
