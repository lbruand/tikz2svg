"""AST node classes for TikZ representation."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ASTNode:
    """Base class for all AST nodes."""

    pass


@dataclass
class TikzPicture(ASTNode):
    """Root node representing a tikzpicture environment."""

    options: Dict[str, Any] = field(default_factory=dict)
    statements: List[ASTNode] = field(default_factory=list)


@dataclass
class Coordinate(ASTNode):
    """Represents a coordinate in any system."""

    system: str  # 'cartesian', 'polar', 'named', '3d', 'relative'
    values: List[float] = field(default_factory=list)
    name: Optional[str] = None
    modifiers: Dict[str, Any] = field(default_factory=dict)  # shift, rotate, etc.


@dataclass
class PathSegment(ASTNode):
    """A single segment in a path."""

    operation: str  # '--', '..', 'arc', 'circle', 'rectangle', etc.
    destination: Optional[Coordinate] = None
    control_points: List[Coordinate] = field(default_factory=list)
    options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Path(ASTNode):
    """A complete path with multiple segments."""

    segments: List[PathSegment] = field(default_factory=list)
    closed: bool = False


@dataclass
class DrawStatement(ASTNode):
    """A \\draw, \\fill, or \\filldraw command."""

    command: str  # 'draw', 'fill', 'filldraw', 'clip'
    options: Dict[str, Any] = field(default_factory=dict)
    path: Path = field(default_factory=Path)


@dataclass
class Node(ASTNode):
    """A \\node command."""

    name: Optional[str] = None
    position: Optional[Coordinate] = None
    text: str = ""
    options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CoordinateDefinition(ASTNode):
    """A \\coordinate command defining a named point."""

    name: str = ""
    position: Optional[Coordinate] = None
    options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Scope(ASTNode):
    """A scope environment with inherited options."""

    options: Dict[str, Any] = field(default_factory=dict)
    statements: List[ASTNode] = field(default_factory=list)


@dataclass
class ForeachLoop(ASTNode):
    """A \\foreach loop."""

    variables: List[str] = field(default_factory=list)
    values: List[Any] = field(default_factory=list)
    evaluate_clause: Optional[str] = None
    body: List[ASTNode] = field(default_factory=list)


@dataclass
class MacroDefinition(ASTNode):
    """A macro definition (\\def, \\newcommand, \\pgfmathsetmacro)."""

    name: str = ""
    parameters: int = 0
    body: str = ""
    macro_type: str = "def"  # 'def', 'newcommand', 'pgfmathsetmacro'


@dataclass
class Layer(ASTNode):
    """A pgfonlayer environment."""

    name: str = ""
    statements: List[ASTNode] = field(default_factory=list)
