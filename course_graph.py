from __future__ import annotations
from course_vertex import _CourseVertex


class CourseGraph:
    """A directed graph representing UofT courses and their prerequisite relationships.

    Each vertex represents a course and each directed edge from A to B
    indicates that A is a prerequisite of B.

    Representation Invariants:
        - all(code == self._vertices[code].code for code in self._vertices)
        - all(code in self._vertices for code in self._edges)
        - all(neighbour in self._vertices for neighbours in self._edges.values()
              for neighbour in neighbours)
    """
    # Private Instance Attributes:
    #   - _vertices: maps each course code to its corresponding _CourseVertex object
    #   - _edges: maps each course code to the set of course codes it is a prerequisite of

    _vertices: dict[str, _CourseVertex]
    _edges: dict[str, set[str]]

    def __init__(self) -> None:
        """Initialize an empty CourseGraph with no vertices or edges."""
        self._vertices = {}
        self._edges = {}
