"""Macro expansion for TikZ/LaTeX macros."""

import re
from typing import Dict, Optional


class MacroExpander:
    """Expands LaTeX macros in TikZ code.

    Supports:
    - \\def\\name{body} - simple substitution
    - \\newcommand{\\name}[N]{body} - parametric macros with #1, #2, etc.
    - Recursive expansion (with depth limit)
    """

    def __init__(self, max_depth: int = 20):
        """Initialize macro expander.

        Args:
            max_depth: Maximum recursion depth for macro expansion
        """
        self.macros: Dict[str, Dict[str, any]] = {}
        self.max_depth = max_depth

    def extract_and_expand(self, text: str) -> str:
        """Extract macro definitions and expand all macro references.

        Args:
            text: TikZ code with macro definitions

        Returns:
            Text with macros expanded and definitions removed
        """
        # Extract macro definitions
        text = self.extract_definitions(text)

        # Expand all macro references
        text = self.expand_all(text)

        return text

    def extract_definitions(self, text: str) -> str:
        """Extract macro definitions from text.

        Removes \\def and \\newcommand statements and stores them.

        Args:
            text: TikZ code

        Returns:
            Text with macro definitions removed
        """
        # Extract \def\name{body}
        def_pattern = r"\\def\\(\w+)\{([^}]*)\}"

        def extract_def(match):
            name = match.group(1)
            body = match.group(2)
            self.macros[name] = {"params": 0, "body": body}
            return ""  # Remove from text

        text = re.sub(def_pattern, extract_def, text)

        # Extract \newcommand{\name}[N]{body}
        # Pattern: \newcommand{\name}[number]{body}
        newcmd_pattern = r"\\newcommand\{\\(\w+)\}\[(\d+)\]\{((?:[^{}]|\{[^{}]*\})*)\}"

        def extract_newcommand(match):
            name = match.group(1)
            params = int(match.group(2))
            body = match.group(3)
            self.macros[name] = {"params": params, "body": body}
            return ""  # Remove from text

        text = re.sub(newcmd_pattern, extract_newcommand, text)

        # Also extract \newcommand{\name}{body} (no parameters)
        newcmd_no_params_pattern = r"\\newcommand\{\\(\w+)\}\{((?:[^{}]|\{[^{}]*\})*)\}"

        def extract_newcommand_no_params(match):
            name = match.group(1)
            body = match.group(2)
            self.macros[name] = {"params": 0, "body": body}
            return ""  # Remove from text

        text = re.sub(newcmd_no_params_pattern, extract_newcommand_no_params, text)

        return text

    def expand_all(self, text: str, depth: int = 0) -> str:
        """Recursively expand all macro references in text.

        Args:
            text: Text containing macro references
            depth: Current recursion depth

        Returns:
            Text with all macros expanded
        """
        if depth >= self.max_depth:
            return text

        original = text

        # Expand each macro
        for name, macro in self.macros.items():
            if macro["params"] == 0:
                # Simple macro: just replace \name with body
                # Use negative lookahead to avoid matching \name{ (which would be a command)
                # Only match \name followed by space, punctuation, or end of string
                # But NOT followed by { or [
                pattern = r"\\" + name + r"(?![{\[])"
                text = re.sub(pattern, macro["body"], text)
            else:
                # Parametric macro: \name{arg1}{arg2}...
                # Build pattern to capture N arguments
                arg_pattern = r"\{([^{}]*)\}"  # Simple version: assumes no nested braces in args
                full_pattern = r"\\" + name + arg_pattern * macro["params"]

                def substitute_params(match, macro_data=macro):
                    """Substitute parameters in macro body."""
                    body = macro_data["body"]
                    # Replace #1, #2, etc. with actual arguments
                    for i in range(1, macro_data["params"] + 1):
                        param_marker = f"#{i}"
                        arg_value = match.group(i)
                        body = body.replace(param_marker, arg_value)
                    return body

                text = re.sub(full_pattern, substitute_params, text)

        # If text changed, recursively expand (for nested macros)
        if text != original:
            text = self.expand_all(text, depth + 1)

        return text

    def add_macro(self, name: str, body: str, params: int = 0):
        """Manually add a macro definition.

        Args:
            name: Macro name (without backslash)
            body: Macro body
            params: Number of parameters (0 for simple macros)
        """
        self.macros[name] = {"params": params, "body": body}

    def get_macro(self, name: str) -> Optional[Dict[str, any]]:
        """Get macro definition.

        Args:
            name: Macro name (without backslash)

        Returns:
            Macro dict with 'params' and 'body', or None if not found
        """
        return self.macros.get(name)
