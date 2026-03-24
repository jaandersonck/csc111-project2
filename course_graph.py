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
        self.level = int(code[3]) * 100
        self.department = code[:3]


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
        """Add a course vertex to this graph. Do nothing if a vertex with the same code already exists.

        Preconditions:
            - vertex is not None

        >>> g = CourseGraph()
        >>> v = _CourseVertex('CSC148H1', 'Introduction to Computer Science', None, None, 5, None, None)
        >>> g.add_vertex(v)
        >>> 'CSC148H1' in g._vertices
        True
        """
        if vertex.code not in self._vertices:
            self._vertices[vertex.code] = vertex
            self._edges[vertex.code] = set()

    def add_edge(self, code1: str, code2: str) -> None:
        """Add a directed edge from code1 to code2, indicating that code1 is a prerequisite of code2.

        Raise ValueError if either code1 or code2 does not correspond to a vertex in this graph.

        Preconditions:
            - code1 != code2
            - code1 in self._vertices
            - code2 in self._vertices
            - code2 not in self._edges[code1]  # no duplicate edges

        >>> g = CourseGraph()
        >>> v1 = _CourseVertex('CSC148H1', 'Intro', None, None, 5, None, None)
        >>> v2 = _CourseVertex('CSC207H1', 'Software Design', None, None, 5, None, None)
        >>> g.add_vertex(v1)
        >>> g.add_vertex(v2)
        >>> g.add_edge('CSC148H1', 'CSC207H1')
        >>> 'CSC207H1' in g._edges['CSC148H1']
        True
        """
        if code1 not in self._vertices or code2 not in self._vertices:
            raise ValueError(f'One or both course codes not found in graph: {code1!r}, {code2!r}')
        self._edges[code1].add(code2)

    def get_vertex(self, code: str) -> _CourseVertex:
        """Return the vertex corresponding to the given course code.

        Raise KeyError if no vertex with that code exists in this graph.

        Preconditions:
            - code in self._vertices

        >>> g = CourseGraph()
        >>> v = _CourseVertex('CSC148H1', 'Intro', None, None, 5, None, None)
        >>> g.add_vertex(v)
        >>> g.get_vertex('CSC148H1').code
        'CSC148H1'
        """
        if code not in self._vertices:
            raise ValueError

        return self._vertices[code]

    def is_eligible(self, code: str, completed: set[str]) -> bool:
        """Return whether a student who has completed the given courses is eligible to enrol in code.

        A student is eligible if the course's prereq_tree is None (no prerequisites)
        or if prereq_tree.is_satisfied(completed) returns True.
        A course the student has already completed is not considered eligible.

        Raise KeyError if code does not correspond to a vertex in this graph.

        Preconditions:
            - code in self._vertices
            - all(c in self._vertices for c in completed)

        >>> g = CourseGraph()
        >>> v = _CourseVertex('CSC108H1', 'Intro', None, None, 5, None, None)
        >>> g.add_vertex(v)
        >>> g.is_eligible('CSC108H1', set())
        True
        >>> g.is_eligible('CSC108H1', {'CSC108H1'})
        False
        """
        # Unvalid Course Code
        if code not in self._vertices:
            raise KeyError(f'Course code not found in graph: {code!r}')

        # Student already completed the course
        if code in completed:
            return False

        if self._vertices[code].prerequisites is None:  # Course w/o prerequisites
            return True
        else:  # Course that neeeds to check prerequisites
            return self._vertices[code].prerequisites.is_satisfied(completed)

    def eligible_courses(self, completed: set[str]) -> set[str]:
        """Return the set of all course codes the student is currently eligible to enrol in,
        excluding courses they have already completed.

        Preconditions:
            - all(c in self._vertices for c in completed)

        >>> g = CourseGraph()
        >>> v = _CourseVertex('CSC108H1', 'Intro', None, None, 5, None, None)
        >>> g.add_vertex(v)
        >>> 'CSC108H1' in g.eligible_courses(set())
        True
        >>> 'CSC108H1' in g.eligible_courses({'CSC108H1'})
        False
        """
        return {code for code in self._vertices if self.is_eligible(code, completed)}

    def credit_count(self, completed: set[str], department: str | None = None) -> float:
        """Return the total credits accumulated from the completed courses.

        If department is given, only count credits from courses in that department.
        If a course code in completed is not found in this graph, it is ignored.

        Preconditions:
            - department is None or len(department) > 0

        >>> g = CourseGraph()
        >>> v1 = _CourseVertex('CSC148H1', 'Intro', None, None, 5, None, None)
        >>> v2 = _CourseVertex('CSC207H1', 'Software Design', None, None, 5, None, None)
        >>> v3 = _CourseVertex('MAT137Y1', 'Calculus', None, None, 5, None, None)
        >>> g.add_vertex(v1)
        >>> g.add_vertex(v2)
        >>> g.add_vertex(v3)
        >>> g.credit_count({'CSC148H1', 'CSC207H1', 'MAT137Y1'})
        2.0
        >>> g.credit_count({'CSC148H1', 'CSC207H1', 'MAT137Y1'}, department='CSC')
        1.0
        >>> g.credit_count({'CSC148H1', 'FAKE999H1'})
        0.5
        """
        if department is None:
            return sum(self._vertices[course].credits
                       for course in completed
                       if course in self._vertices)
        else:
            return sum(self._vertices[course].credits
                       for course in completed
                       if course in self._vertices
                       and self._vertices[course].department == department)

    def find_paths(self, completed: set[str], target: str) -> list[list[str]]:
        """Return all valid course sequences the student could take to become eligible for target.

        Each path is a list of course codes in the order they should be taken,
        starting from the first course the student needs to take and ending with target.
        Courses in completed are not included in the returned paths.
        Returns an empty list if target is already in completed or is unreachable.

        Preconditions:
            - target in self._vertices
            - all(c in self._vertices for c in completed)
            - target not in completed

        >>> g = CourseGraph()
        >>> v1 = _CourseVertex('CSC108H1', 'Intro', None, None, 5, None, None)
        >>> v2 = _CourseVertex('CSC148H1', 'Intro 2', None, None, 5, None, None)
        >>> g.add_vertex(v1)
        >>> g.add_vertex(v2)
        >>> g.add_edge('CSC108H1', 'CSC148H1')
        >>> g.find_paths(set(), 'CSC148H1')
        [['CSC108H1', 'CSC148H1']]
        """

    def _find_paths_helper(self, completed: set[str], target: str, visited: set[str]) -> list[list[str]]:
        """Return all valid course sequences from the current state to target, avoiding visited courses.

        This is a helper method for find_paths. It recursively explores all eligible
        courses from the current completed set, adding each to the path and simulating
        the student taking it before continuing the search.

        visited tracks which courses have already been explored in the current branch
        of the search to prevent infinite loops in the graph traversal.

        Preconditions:
            - target in self._vertices
            - all(c in self._vertices for c in completed)
            - all(c in self._vertices for c in visited)
            - target not in completed

        >>> g = CourseGraph()
        >>> v1 = _CourseVertex('CSC108H1', 'Intro', None, None, 5, None, None)
        >>> v2 = _CourseVertex('CSC148H1', 'Intro 2', None, None, 5, None, None)
        >>> g.add_vertex(v1)
        >>> g.add_vertex(v2)
        >>> g.add_edge('CSC108H1', 'CSC148H1')
        >>> g._find_paths_helper(set(), 'CSC148H1', set())
        [['CSC108H1', 'CSC148H1']]
        """
