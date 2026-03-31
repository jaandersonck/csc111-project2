"""CSC111 Winter 2026 Project 2: Course Graph

Module Description
==================

This module contains the components of the CourseGraph used throughout the application, including
_CourseVertex and CourseGraph.

Copyright and Usage Information
===============================

This file is Copyright (c) 2026.
"""
from __future__ import annotations
import networkx as nx
from boolean_list import BooleanList


class _CourseVertex:
    """A vertex in a CourseGraph, representing a single UofT course.

    Instance Attributes:
        - code: the course code, e.g. 'CSC111H1'
        - name: the full course name
        - hours: the weekly contact hours string, e.g. '36L/12T'
        - description: the course description from the A&S calendar
        - breadth: the breadth requirement category number, or None if not applicable
        - prerequisites: the prerequisite condition as a BooleanList, or None if there are none
        - exclusions: a list of course codes that cannot be taken alongside this course, or None

    Computed Properties (derived from code):
        - credits: the credit weight, either 0.5 for H courses or 1.0 for Y courses
        - level: the course level, one of 100, 200, 300, or 400
        - department: the department code prefix, e.g. 'CSC'

    Representation Invariants:
        - self.credits() in {0.5, 1.0}
        - self.level() in {100, 200, 300, 400}
        - len(self.code) > 0
    """
    code: str
    name: str
    hours: str | None
    description: str | None
    breadth: int | None
    prerequisites: BooleanList | None
    exclusions: list[str] | None
    # credits, level, department are computed properties derived from code

    def __init__(self, code: str, name: str,
                 prerequisites: BooleanList | None = None) -> None:
        """Initialize a new vertex with the given course code, name, and prerequisites.

        hours, description, breadth, and exclusions default to None and can be set directly.

        Preconditions:
            - len(code) > 0

        >>> v = _CourseVertex('CSC148H1', 'Intro to Computer Science')
        >>> v.code
        'CSC148H1'
        >>> v.credits()
        0.5
        """
        self.code = code
        self.name = name
        self.prerequisites = prerequisites
        self.hours = None
        self.description = None
        self.breadth = None
        self.exclusions = None

    def credits(self) -> float:
        """Return the credit weight: 1.0 for Y courses, 0.5 for all others."""
        return 1.0 if self.code.endswith('Y1') else 0.5

    def level(self) -> int:
        """Return the course level as a multiple of 100 (e.g. 100, 200, 300, 400)."""
        return int(self.code[3]) * 100

    def department(self) -> str:
        """Return the three-letter department prefix from the course code."""
        return self.code[:3]


class CourseGraph:
    """A directed graph representing UofT courses and their prerequisite relationships.

    Each vertex represents a course and each directed edge from A to B
    indicates that A is a prerequisite of B.

    Representation Invariants:
        - all(code == self.vertices[code].code for code in self.vertices)
        - all(code in self.vertices for code in self._edges)
        - all(neighbour in self.vertices for neighbours in self._edges.values()
              for neighbour in neighbours)
    """
    # Private Instance Attributes:
    #   - vertices: maps each course code to its corresponding _CourseVertex object
    #   - _edges: maps each course code to the set of course codes it is a prerequisite of

    vertices: dict[str, _CourseVertex]
    _edges: dict[str, set[str]]

    def __init__(self) -> None:
        """Initialize an empty CourseGraph with no vertices or edges."""
        self.vertices = {}
        self._edges = {}

    def add_vertex(self, vertex: _CourseVertex) -> None:
        """Add a course vertex to this graph. Do nothing if a vertex with the same code already exists.

        Preconditions:
            - vertex is not None

        >>> g = CourseGraph()
        >>> v = _CourseVertex('CSC148H1', 'Introduction to Computer Science')
        >>> g.add_vertex(v)
        >>> 'CSC148H1' in g.vertices
        True
        """
        if vertex.code not in self.vertices:
            self.vertices[vertex.code] = vertex
            self._edges[vertex.code] = set()

    def add_edge(self, code1: str, code2: str) -> None:
        """Add a directed edge from code1 to code2, indicating that code1 is a prerequisite of code2.

        Raise ValueError if either code1 or code2 does not correspond to a vertex in this graph.

        Preconditions:
            - code1 != code2
            - code1 in self.vertices
            - code2 in self.vertices
            - code2 not in self._edges[code1]

        >>> g = CourseGraph()
        >>> v1 = _CourseVertex('CSC148H1', 'Intro')
        >>> v2 = _CourseVertex('CSC207H1', 'Software Design')
        >>> g.add_vertex(v1)
        >>> g.add_vertex(v2)
        >>> g.add_edge('CSC148H1', 'CSC207H1')
        >>> 'CSC207H1' in g._edges['CSC148H1']
        True
        """
        if code1 not in self.vertices or code2 not in self.vertices:
            raise ValueError(f'One or both course codes not found in graph: {code1!r}, {code2!r}')
        self._edges[code1].add(code2)

    def get_vertex(self, code: str) -> _CourseVertex:
        """Return the vertex corresponding to the given course code.

        Raise KeyError if no vertex with that code exists in this graph.

        Preconditions:
            - code in self.vertices

        >>> g = CourseGraph()
        >>> v = _CourseVertex('CSC148H1', 'Intro')
        >>> g.add_vertex(v)
        >>> g.get_vertex('CSC148H1').code
        'CSC148H1'
        """
        if code not in self.vertices:
            raise KeyError(f'Course code not found in graph: {code!r}')
        return self.vertices[code]

    def is_eligible(self, code: str, completed: set[str]) -> bool:
        """Return whether a student who has completed the given courses is eligible to enrol in code.

        A student is eligible if the course's prerequisites is None (no prerequisites)
        or if prerequisites.is_satisfied(completed) returns True.
        A course the student has already completed is not considered eligible.

        Raise KeyError if code does not correspond to a vertex in this graph.

        Preconditions:
            - code in self.vertices
            - all(c in self.vertices for c in completed)

        >>> g = CourseGraph()
        >>> v = _CourseVertex('CSC108H1', 'Intro')
        >>> g.add_vertex(v)
        >>> g.is_eligible('CSC108H1', set())
        True
        >>> g.is_eligible('CSC108H1', {'CSC108H1'})
        False
        """
        if code not in self.vertices:
            raise KeyError(f'Course code not found in graph: {code!r}')

        if code in completed:
            return False

        prereqs = self.vertices[code].prerequisites
        if prereqs is None:
            return True
        return prereqs.is_satisfied(completed)

    def eligible_courses(self, completed: set[str]) -> set[str]:
        """Return the set of all course codes the student is currently eligible to enrol in,
        excluding courses they have already completed.

        Preconditions:
            - all(c in self.vertices for c in completed)

        >>> g = CourseGraph()
        >>> v = _CourseVertex('CSC108H1', 'Intro')
        >>> g.add_vertex(v)
        >>> 'CSC108H1' in g.eligible_courses(set())
        True
        >>> 'CSC108H1' in g.eligible_courses({'CSC108H1'})
        False
        """
        return {code for code in self.vertices if self.is_eligible(code, completed)}

    def credit_count(self, completed: set[str], department: str | None = None) -> float:
        """Return the total credits accumulated from the completed courses.

        If department is given, only count credits from courses in that department.
        If a course code in completed is not found in this graph, it is ignored.

        Preconditions:
            - department is None or len(department) > 0

        >>> g = CourseGraph()
        >>> v1 = _CourseVertex('CSC148H1', 'Intro')
        >>> v2 = _CourseVertex('CSC207H1', 'Software Design')
        >>> v3 = _CourseVertex('MAT137Y1', 'Calculus')
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
            return sum(self.vertices[course].credits()
                       for course in completed
                       if course in self.vertices)
        else:
            return sum(self.vertices[course].credits()
                       for course in completed
                       if course in self.vertices
                       and self.vertices[course].department() == department)

    def to_networkx(self) -> nx.DiGraph:
        """Convert this CourseGraph to a NetworkX DiGraph."""
        digraph_nx = nx.DiGraph()
        for code, course in self.vertices.items():
            digraph_nx.add_node(code)
            if course.prerequisites:
                for prereq in course.prerequisites.get_all_courses():
                    # Only add edge if both courses are in this graph
                    if prereq in self.vertices:
                        digraph_nx.add_edge(prereq, code)

        return digraph_nx


if __name__ == '__main__':
    import doctest
    doctest.testmod()
    # import python_ta
    # python_ta.check_all(config={
    #     'extra-imports': ['boolean_list', 'networkx'],
    #     'allowed-io': [],
    #     'max-line-length': 120
    # })
