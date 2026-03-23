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

    def add_vertex(self, vertex: _CourseVertex) -> None:
        """Add a course vertex to this graph."""
        raise NotImplementedError

    def add_edge(self, code1: str, code2: str) -> None:
        """Add a directed edge from code1 to code2, indicating code1 is a prerequisite of code2."""
        raise NotImplementedError

    def get_vertex(self, code: str) -> _CourseVertex:
        """Return the vertex corresponding to the given course code."""
        raise NotImplementedError

    def is_eligible(self, code: str, completed: set[str]) -> bool:
        """Return whether the student is eligible to enrol in the given course."""
        raise NotImplementedError

    def eligible_courses(self, completed: set[str]) -> set[str]:
        """Return the set of all course codes the student is currently eligible to enrol in."""
        raise NotImplementedError

    def credit_count(self, completed: set[str], department: str | None = None) -> float:
        """Return the total credits accumulated from completed courses.

        If department is given, only count credits from that department.
        """
        raise NotImplementedError

    def find_paths(self, completed: set[str], target: str) -> list[list[str]]:
        """Return all valid course sequences the student could take to become eligible for target."""
        raise NotImplementedError
