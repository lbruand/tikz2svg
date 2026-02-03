# Code Duplication Analysis Report

## Summary

Found significant code duplication in the tikz2svg codebase. Total estimated duplicate lines: **~80-100 lines** that could be reduced to **~20-30 lines** with proper refactoring.

## High Priority Duplications

### 1. Statement Transformers (parser.py:35-85) ⚠️ HIGH IMPACT

**Location:** `tikz2svg/parser/parser.py`
**Duplicate Lines:** ~50 lines
**Potential Reduction:** ~40 lines

Four nearly identical transformer methods:
- `draw_stmt()`
- `fill_stmt()`
- `filldraw_stmt()`
- `clip_stmt()`

**Current Code:**
```python
def draw_stmt(self, items):
    """Transform draw statement."""
    options = {}
    path = None

    for item in items:
        if isinstance(item, dict):
            options = item
        elif isinstance(item, Path):
            path = item

    return DrawStatement(command="draw", options=options, path=path or Path())

def fill_stmt(self, items):
    """Transform fill statement."""
    options = {}
    path = None

    for item in items:
        if isinstance(item, dict):
            options = item
        elif isinstance(item, Path):
            path = item

    return DrawStatement(command="fill", options=options, path=path or Path())

# ... filldraw_stmt and clip_stmt are identical except for command name
```

**Recommended Fix:**
```python
def _create_draw_statement(self, command: str, items: list) -> DrawStatement:
    """Helper to create draw-like statements from items."""
    options = {}
    path = None

    for item in items:
        if isinstance(item, dict):
            options = item
        elif isinstance(item, Path):
            path = item

    return DrawStatement(command=command, options=options, path=path or Path())

def draw_stmt(self, items):
    """Transform draw statement."""
    return self._create_draw_statement("draw", items)

def fill_stmt(self, items):
    """Transform fill statement."""
    return self._create_draw_statement("fill", items)

def filldraw_stmt(self, items):
    """Transform filldraw statement."""
    return self._create_draw_statement("filldraw", items)

def clip_stmt(self, items):
    """Transform clip statement."""
    return self._create_draw_statement("clip", items)
```

**Benefits:**
- Reduces 50 lines to ~25 lines
- Single source of truth for statement parsing logic
- Easier to maintain and extend

---

### 2. String Value Evaluation (converter.py:530-548) ⚠️ MEDIUM IMPACT

**Location:** `tikz2svg/svg/converter.py`
**Duplicate Lines:** ~15 lines
**Potential Reduction:** ~10 lines

Repeated pattern for evaluating string values with fallback:

**Current Code:**
```python
# Pattern 1 (line 530-537)
if isinstance(value, str):
    try:
        value_eval = parent_evaluator.evaluate(value)
    except Exception:
        value_eval = value
else:
    value_eval = value
self.context.set_variable(var_name, value_eval)

# Pattern 2 (line 542-548)
if isinstance(val, str):
    try:
        val = parent_evaluator.evaluate(val)
    except Exception:
        pass
    self.context.set_variable(var_name, val)
```

**Recommended Fix:**
```python
def _evaluate_or_passthrough(self, value: Any, evaluator: MathEvaluator) -> Any:
    """Evaluate string value or pass through non-strings."""
    if isinstance(value, str):
        try:
            return evaluator.evaluate(value)
        except Exception:
            return value
    return value

# Then use:
value_eval = self._evaluate_or_passthrough(value, parent_evaluator)
self.context.set_variable(var_name, value_eval)

# And:
val = self._evaluate_or_passthrough(value[i], parent_evaluator)
self.context.set_variable(var_name, val)
```

---

### 3. String Conversion Pattern (parser.py) ⚠️ LOW-MEDIUM IMPACT

**Location:** `tikz2svg/parser/parser.py`
**Duplicate Lines:** ~10 lines scattered
**Potential Reduction:** ~5 lines

The `_to_string()` helper exists (line 676-684) but isn't used consistently:

**Issues:**
- Line 184: `return str(item)` - should use `_to_string`
- Line 215: Manual string join - could use helper
- Line 232, 239: Direct `str()` conversion
- Lines 254, 278: Conditional string conversion

**Recommended Fix:**
Use `_to_string()` consistently throughout, or extend it to handle more cases:

```python
def _to_string(self, item):
    """Convert token, list, or value to string."""
    if isinstance(item, str):
        return item
    elif isinstance(item, Token):
        return str(item.value)
    elif isinstance(item, list):
        return " ".join(self._to_string(i) for i in item)
    else:
        return str(item)
```

---

### 4. Exception Handling Pattern ⚠️ LOW IMPACT

**Location:** Multiple files
**Duplicate Lines:** ~10-15 lines

Similar try-except patterns for safe evaluation:

**Pattern:**
```python
try:
    result = evaluate_something(value)
except Exception:
    result = fallback_value
```

**Found in:**
- `parser.py:556-559` - Range evaluation
- `parser.py:585-587` - Range expansion
- `converter.py:530-534` - Value evaluation
- `converter.py:544-547` - List value evaluation

**Recommendation:**
Consider a decorator or context manager for safe evaluation:

```python
def safe_eval(value, evaluator, default=None):
    """Safely evaluate value with fallback."""
    try:
        return evaluator.evaluate(value)
    except Exception:
        return default if default is not None else value

# Usage:
result = safe_eval(expression, self.evaluator, default=0)
```

---

## Medium Priority Duplications

### 5. Option Processing Pattern

Similar patterns for processing options dictionaries across multiple methods in both `parser.py` and `converter.py`.

**Locations:**
- `parser.py`: node_stmt, coordinate_stmt
- `converter.py`: Various convert_* methods

**Pattern:**
```python
for item in items:
    if isinstance(item, dict):
        options = item
    elif isinstance(item, SomeType):
        variable = item
```

Could be abstracted to:
```python
def _extract_items(self, items, type_map):
    """Extract items by type into result dict."""
    results = {key: None for key in type_map.keys()}
    for item in items:
        for key, item_type in type_map.items():
            if isinstance(item, item_type):
                results[key] = item
                break
    return results

# Usage:
extracted = self._extract_items(items, {
    'options': dict,
    'path': Path,
    'coordinate': Coordinate
})
```

---

## Refactoring Recommendations

### Priority 1: Statement Transformers
**Effort:** 30 minutes
**Impact:** High (reduces 50 lines to 25)
**Risk:** Low (straightforward extraction)

### Priority 2: Value Evaluation Helper
**Effort:** 20 minutes
**Impact:** Medium (improves consistency)
**Risk:** Low (simple helper method)

### Priority 3: Consistent String Conversion
**Effort:** 15 minutes
**Impact:** Medium (cleaner code)
**Risk:** Very Low (existing helper)

### Priority 4: Generic Item Extraction
**Effort:** 45 minutes
**Impact:** Medium (applicable to many methods)
**Risk:** Medium (needs careful testing)

---

## Metrics

**Current State:**
- Total lines in parser.py: 802
- Total lines in converter.py: 626
- Estimated duplicate lines: 80-100
- Duplication percentage: ~6-8%

**After Refactoring:**
- Estimated reduction: 50-70 lines
- Improved maintainability
- Reduced bug surface area
- Easier to extend

---

## Testing Strategy

For each refactoring:
1. Extract helper method
2. Run full test suite (should remain at 122/124 passing)
3. Run quality checks (Black, Ruff, isort)
4. Commit with clear description

---

## Non-Issues (Acceptable "Duplication")

The following are NOT considered problematic duplication:

1. **Transformer method signatures** - Each transformer needs its own method per Lark convention
2. **AST node creation** - Different node types naturally have different fields
3. **Type checking patterns** - `isinstance()` checks are idiomatic Python
4. **Import statements** - Standard practice

---

Generated: 2026-02-03
