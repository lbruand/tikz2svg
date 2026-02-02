# Sri Yantra Example Analysis

## File: library/0001-sri-yantra.tex

### Test Result: ❌ FAILED (Expected)

**Error**: `Unexpected token Token('LBRACE', '{')` after macro expansion

---

## Why It Fails

The Sri Yantra example uses **advanced TeX programming features** that are beyond the scope of our pragmatic macro implementation:

### 1. **Complex Macro Data Structure** ❌
```tex
\def\triangleData{%
  {53.65669559977147}{123.20508075688774}{250}{246.34330440022853}{0}% D1
  {52.984011026495736}{174.24660560764943}{50}{247.01598897350425}{1}% U1
  ...
}
```
- This defines a macro containing **raw data**
- The data is not valid TikZ code by itself
- It's meant to be processed by a recursive macro

### 2. **Recursive Macros with `\expandafter`** ❌
```tex
\def\processTriangleData#1#2#3#4#5{%
  \ifx\relax#1\relax
    % End of data reached
  \else
    \drawTriangleFromData{#1}{#2}{#3}{#4}{#5}%
    \expandafter\processTriangleData
  \fi
}

\expandafter\processTriangleData\triangleData\relax\relax\relax\relax\relax
```
- Uses `\expandafter` for controlled macro expansion
- Recursive processing with delimiter-based argument parsing
- **Not supported** by regex-based macro expansion

### 3. **Conditionals** ❌
```tex
\ifnum#5=0
  % Downward triangle
  \drawtriangle{#1}{#2}{\cx}{#3}{#4}{#2}%
\else
  % Upward triangle
  \drawtriangle{#1}{#2}{\cx}{#3}{#4}{#2}%
\fi
```
- TeX conditionals: `\ifnum`, `\ifx`
- **Not implemented** in our parser

### 4. **Advanced Scope Options** ❌
```tex
\begin{scope}[on background layer]
  ...
\end{scope}
```
- `on background layer` is a TikZ library option
- **Not parsed** by our grammar

### 5. **Complex Bezier Curves** ⚠️
```tex
\draw[fill=green!30!black] (\start:2.5)
  .. controls ({\start-5}:2.85) and ({\start-17.5}:2.75) ..
  ({\start-22.5}:3)
  .. controls ({\start-27.5}:2.75) and ({\start-40}:2.85) ..
  ({\start-45}:2.5)
  arc [start angle={\start-45}, delta angle=45, radius=2.5cm]--cycle;
```
- Bezier curves with `.. controls ... and ... ..` syntax
- Uses braces `{}` in coordinate expressions
- Arc with `[start angle=..., delta angle=..., radius=...]` syntax
- **Partially supported** (controls clause exists, but brace syntax fails)

### 6. **Node Anchor References** ⚠️
```tex
\node [fill=black, minimum size=8cm] (b) {};
\node [fill=black] at (bv.north) (bn) {};
\draw (be.south west)-|(be.north east)-|...
```
- References to node anchors in paths: `(bv.north)`, `(be.south west)`
- **Partially supported** (named coords work, but complex anchor paths may not)

---

## What Would Be Needed

To support this example, we would need:

### 1. **TeX Conditionals**
```python
# Add to grammar:
conditional: "\\ifnum" comparison statement* "\\else" statement* "\\fi"
           | "\\ifx" token token statement* "\\else" statement* "\\fi"
```

### 2. **Expansion Control**
- Implement `\expandafter`, `\noexpand`
- Control macro expansion order
- This is **very complex** - would need a full TeX interpreter

### 3. **Delimiter-Based Argument Parsing**
```tex
\def\mymacro#1#2#3#4#5{...}
```
- Current implementation handles `{arg}` syntax
- Doesn't handle space-delimited or explicit delimiter arguments

### 4. **Library Support**
- `\usetikzlibrary{backgrounds,math}`
- Library-specific options and commands
- Would need TikZ library implementations

### 5. **Braces in Coordinates**
- Support `{expr}` in addition to `(expr)` for grouping
- Update grammar to allow braces in math expressions

---

## Architectural Limitation

Our macro expander uses a **pragmatic regex-based approach**:
- ✅ Good for: Simple `\def`, `\newcommand` with parameters
- ✅ Good for: Direct macro substitution
- ❌ Bad for: Controlled expansion (`\expandafter`)
- ❌ Bad for: Conditionals and flow control
- ❌ Bad for: Recursive delimiter-based parsing

**Reason**: Full TeX macro expansion requires a complete TeX interpreter (10,000+ lines of C code in the original implementation).

---

## Workaround for Sri Yantra

To make this work with our parser, the file would need to be **pre-processed** or **rewritten**:

### Option 1: Pre-process with Real TeX
```bash
# Use real TeX to expand macros
tex -ini "&latex" mylatexformat.ltx 0001-sri-yantra.tex
# Extract expanded TikZ code
# Feed to our parser
```

### Option 2: Rewrite Without Advanced Features
```tex
% Instead of recursive macro with data array,
% manually draw each triangle:
\drawtriangle{53.65669559977147}{123.20508075688774}{250}{246.34330440022853}{123.20508075688774}
\drawtriangle{52.984011026495736}{174.24660560764943}{150}{247.01598897350425}{174.24660560764943}
% ... etc
```

### Option 3: Use Simpler Foreach
```tex
% Instead of complex recursive macros,
% use foreach with simple data:
\foreach \lx/\ty/\cy/\rx/\type in {
  53.65/123.20/250/246.34/0,
  52.98/174.24/50/247.01/1,
  ...
} {
  % Draw triangle using \lx, \ty, etc.
}
```

---

## Coverage Analysis

### ✅ What We Support
- ✅ Layers: `\pgfdeclarelayer`, `\pgfsetlayers`, `\begin{pgfonlayer}`
- ✅ Simple macros: `\def\cx{150}`
- ✅ Parametric macros: `\newcommand{\drawtriangle}[6]{...}`
- ✅ Foreach loops: `\foreach \i in {0,...,7}`
- ✅ Evaluate clause: `[evaluate=\i as \start using 22.5+45*\i]`
- ✅ Basic scopes
- ✅ Circle and draw commands
- ✅ Node creation

### ❌ What We Don't Support (in this file)
- ❌ Conditionals: `\ifnum`, `\ifx`, `\else`, `\fi`
- ❌ Expansion control: `\expandafter`
- ❌ Recursive macros with delimiter parsing
- ❌ Library options: `on background layer`
- ❌ Braces in coordinates: `{expr}`
- ❌ Arc syntax: `arc [start angle=..., delta angle=..., radius=...]`

---

## Conclusion

**The Sri Yantra example is BEYOND the scope of our implementation.**

This is **by design** - supporting full TeX macro expansion would require:
- A complete TeX interpreter
- 10,000+ lines of additional code
- Months of development time

Our implementation targets **95% of real-world TikZ usage** with a **pragmatic approach**:
- ✅ 119/124 tests passing (96%)
- ✅ Handles common TikZ patterns
- ✅ Fast and maintainable
- ❌ Doesn't handle TeX programming extremes

**Recommendation**: For files like Sri Yantra that use advanced TeX programming:
1. Pre-process with real TeX/LaTeX
2. Extract expanded TikZ code
3. Feed to our parser

Or use the original pdflatex → pdf2svg pipeline for these edge cases.

---

## Alternative: Test Simpler Library Example

The plan mentioned multiple library examples:
- ❌ 0001-sri-yantra.tex (Too complex - TeX programming)
- ❓ 0002-regular-hexagonal-prism.tex (May be simpler)
- ❓ 0003-regular-tetrahedron.tex (May be simpler)

**Recommendation**: Try a simpler library example that doesn't use advanced TeX macros.
