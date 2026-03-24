from __future__ import annotations
from course_graph import CourseGraph, _CourseVertex
from boolean_list import BooleanList, CreditCondition


def get_course_codes(prereq_tree: BooleanList) -> set[str]:
    """Return all course code strings mentioned anywhere in the given BooleanList tree.

    CreditCondition nodes are ignored since they are not specific courses.

    Preconditions:
        - prereq_tree is not None

    >>> bl = BooleanList('AND', ['CSC148H1', 'CSC165H1'])
    >>> get_course_codes(bl) == {'CSC148H1', 'CSC165H1'}
    True

    >>> bl = BooleanList('OR', ['CSC148H1', BooleanList('AND', ['MAT137Y1', 'CSC165H1'])])
    >>> get_course_codes(bl) == {'CSC148H1', 'MAT137Y1', 'CSC165H1'}
    True

    >>> bl = BooleanList('AND', [CreditCondition(1.0, 'CSC'), 'CSC148H1'])
    >>> get_course_codes(bl) == {'CSC148H1'}
    True
    """
    if prereq_tree.items is None:
        return set()

    codes_so_far = set()
    for item in prereq_tree.items:
        if isinstance(item,  str):
            codes_so_far.add(item)
        elif isinstance(item, BooleanList):
            codes_result = get_course_codes(item)
            codes_so_far = codes_so_far.union(codes_result)
        elif isinstance(item, CreditCondition):
            continue
    return codes_so_far


def get_relevant_courses(graph: CourseGraph, target: str, completed: set[str]) -> set[str]:
    """Return all courses needed to reach target that are not already in completed.

    Walks backwards through the prerequisite graph starting from target,
    collecting all courses that appear in any prerequisite tree along the way.
    Stops recursing into a course if it is already in completed.
    Always includes target itself in the returned set.

    Preconditions:
        - target in graph._vertices
        - all(c in graph._vertices for c in completed)

    >>> from course_graph import CourseGraph, _CourseVertex
    >>> from boolean_list import BooleanList
    >>> g = CourseGraph()
    >>> g.add_vertex(_CourseVertex('CSC108H1', 'Intro', None, None, 5, None, None))
    >>> g.add_vertex(_CourseVertex('CSC148H1', 'Intro 2', None, None, 5,
    ...     BooleanList('AND', ['CSC108H1']), None))
    >>> g.add_vertex(_CourseVertex('CSC207H1', 'Software Design', None, None, 5,
    ...     BooleanList('AND', ['CSC148H1']), None))
    >>> get_relevant_courses(g, 'CSC207H1', set()) == {'CSC108H1', 'CSC148H1', 'CSC207H1'}
    True
    >>> get_relevant_courses(g, 'CSC207H1', {'CSC148H1'}) == {'CSC148H1', 'CSC207H1'}
    True
    >>> get_relevant_courses(g, 'CSC108H1', set()) == {'CSC108H1'}
    True
    """

    if target in completed:
        return set()
    else:
        course_vertex = graph._vertices[target]
        if course_vertex.prerequisites is None:
            return {target}

        course_prereq = get_course_codes(course_vertex.prerequisites)
        new_completed = {target}

        for course in course_prereq:
            result = get_relevant_courses(graph, course, completed)
            new_completed = new_completed.union(result)

        return new_completed


def find_paths_helper(graph: CourseGraph,
                      completed: set[str],
                      targets: set[str],
                      relevant: set[str],
                      current_path: list[str]) -> list[list[str]]:
    """Return all valid course sequences from the current state that satisfy all targets.

    This is the recursive DFS helper for find_paths. At each step it finds all
    currently eligible courses within the relevant subgraph, simulates taking
    each one, and recurses until all targets are in completed.

    completed is treated as immutable — a new set is created at each recursive
    call rather than mutating the original, so different DFS branches stay
    fully independent of each other.

    Preconditions:
        - all(t in graph._vertices for t in targets)
        - all(c in graph._vertices for c in completed)
        - all(r in graph._vertices for r in relevant)
        - all(c in relevant or c in completed for c in current_path)
    """
    raise NotImplementedError


def find_paths(graph: CourseGraph,
               completed: set[str],
               targets: set[str],
               max_results: int = 10) -> list[list[str]]:
    """Return up to max_results valid course sequences that satisfy all targets.

    Each path is a list of course codes in the order the student should take them,
    not including any courses already in completed.
    Paths are sorted by length, shortest first.
    Returns an empty list if all targets are already satisfied or are unreachable.

    Preconditions:
        - all(t in graph._vertices for t in targets)
        - all(c in graph._vertices for c in completed)
        - max_results >= 1

    >>> from course_graph import CourseGraph, _CourseVertex
    >>> from boolean_list import BooleanList
    >>> g = CourseGraph()
    >>> g.add_vertex(_CourseVertex('CSC108H1', 'Intro', None, None, 5, None, None))
    >>> g.add_vertex(_CourseVertex('CSC148H1', 'Intro 2', None, None, 5,
    ...     BooleanList('AND', ['CSC108H1']), None))
    >>> g.add_vertex(_CourseVertex('CSC207H1', 'Software Design', None, None, 5,
    ...     BooleanList('AND', ['CSC148H1']), None))
    >>> paths = find_paths(g, set(), {'CSC207H1'})
    >>> paths[0]
    ['CSC108H1', 'CSC148H1', 'CSC207H1']
    """
    raise NotImplementedError
