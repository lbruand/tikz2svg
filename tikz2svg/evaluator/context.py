"""Evaluation context for managing variables and scopes."""

from typing import Any, Dict, Optional


class EvaluationContext:
    """Manages variable and coordinate scope during evaluation."""

    def __init__(self, parent: Optional["EvaluationContext"] = None):
        """
        Initialize evaluation context.

        Args:
            parent: Parent context for nested scopes
        """
        self.parent = parent
        self.variables: Dict[str, Any] = {}
        self.coordinates: Dict[str, tuple] = {}

    def set_variable(self, name: str, value: Any) -> None:
        """
        Set a variable value.

        Args:
            name: Variable name (with or without leading backslash)
            value: Variable value
        """
        # Normalize variable name (remove leading backslash if present)
        if name.startswith("\\"):
            name = name[1:]

        self.variables[name] = value

    def get_variable(self, name: str) -> Optional[Any]:
        """
        Get a variable value.

        Args:
            name: Variable name (with or without leading backslash)

        Returns:
            Variable value or None if not found
        """
        # Normalize variable name
        if name.startswith("\\"):
            name = name[1:]

        # Look in current scope
        if name in self.variables:
            return self.variables[name]

        # Look in parent scope
        if self.parent:
            return self.parent.get_variable(name)

        return None

    def has_variable(self, name: str) -> bool:
        """
        Check if variable exists.

        Args:
            name: Variable name

        Returns:
            True if variable exists
        """
        return self.get_variable(name) is not None

    def set_coordinate(self, name: str, position: tuple) -> None:
        """
        Set a named coordinate.

        Args:
            name: Coordinate name
            position: (x, y) tuple
        """
        self.coordinates[name] = position

    def get_coordinate(self, name: str) -> Optional[tuple]:
        """
        Get a named coordinate.

        Args:
            name: Coordinate name

        Returns:
            (x, y) tuple or None if not found
        """
        # Look in current scope
        if name in self.coordinates:
            return self.coordinates[name]

        # Look in parent scope
        if self.parent:
            return self.parent.get_coordinate(name)

        return None

    def create_child_context(self) -> "EvaluationContext":
        """
        Create a child context for nested scopes.

        Returns:
            New child context
        """
        return EvaluationContext(parent=self)

    def get_all_variables(self) -> Dict[str, Any]:
        """
        Get all variables including from parent scopes.

        Returns:
            Dictionary of all variables
        """
        if self.parent:
            # Start with parent variables
            all_vars = self.parent.get_all_variables()
            # Override with local variables
            all_vars.update(self.variables)
            return all_vars
        else:
            return self.variables.copy()
