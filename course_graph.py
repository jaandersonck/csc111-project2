from __future__ import annotations
from boolean_list import BooleanList


class _CourseVertex:
    """A vertex in a CourseGraph, representing a single UofT course.

    Instance Attributes:
        - code: the course code, e.g. 'CSC111H1'
        - name: the full course name
        - hours: the weekly contact hours string, e.g. '36L/12T'
        - description: the course description from the A&S calendar
        - breadth: the breadth requirement category number, or None if not applicable
        - credits: the credit weight, either 0.5 for H courses or 1.0 for Y courses
        - level: the course level, one of 100, 200, 300, or 400
        - department: the department code prefix, e.g. 'CSC'
        - prerequisites: the prerequisite condition as a BooleanList, or None if there are none
        - exclusions: a list of course codes that cannot be taken alongside this course, or None

    Representation Invariants:
        - self.credits in {0.5, 1.0}
        - self.level in {100, 200, 300, 400}
        - len(self.code) > 0
    """
    code: str
    name: str
    hours: str | None
    description: str | None
    breadth: int | None
    credits: float
    level: int
    department: str
    prerequisites: BooleanList | None
    exclusions: list[str] | None

    def __init__(self,
                 code: str,
                 name: str,
                 hours: str | None,
                 description: str | None,
                 breadth: int | None,
                 prerequisites: BooleanList | None,
                 exclusions: list[str] | None) -> None:
        """Initialize a new vertex with the given course details."""
        self.code = code
        self.name = name
        self.hours = hours
        self.description = description
        self.breadth = breadth
        self.prerequisites = prerequisites
        self.exclusions = exclusions
        self.credits = 1.0 if code.endswith('Y1') else 0.5
        self.level = int(next(c for c in code if c.isdigit())) * 100
        self.department = ''.join(c for c in code if c.isalpha())


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
        # REPLACE THIS IMPLEMENTATION WITH UPSTREAM
        self._vertices[vertex.code] = vertex

    def add_edge(self, code1: str, code2: str) -> None:
        """Add a directed edge from code1 to code2, indicating code1 is a prerequisite of code2."""
        raise NotImplementedError

    def get_vertex(self, code: str) -> _CourseVertex:
        """Return the vertex corresponding to the given course code."""
        if code in self._vertices:
            return self._vertices[code]
        else:
            raise ValueError

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
