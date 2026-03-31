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
    """Return all courses on any prerequisite path to target, including target itself.

    Stops recursing into a course already in completed.

    Preconditions:
        - target in graph._vertices
        - all(c in graph._vertices for c in completed)

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
        course_vertex = graph.vertices[target]
        if course_vertex.prerequisites is None:
            return {target}

        course_prereq = get_course_codes(course_vertex.prerequisites)
        new_completed = {target}

        for course in course_prereq:
            result = get_relevant_courses(graph, course, completed)
            new_completed = new_completed.union(result)

        return new_completed


def eligible_relevant_courses(graph: CourseGraph, completed: set[str], target: str) -> set[str]:
    """Return courses the student can enrol in now that are relevant to reaching target.

    Target and already-completed courses are excluded from the result.

    Preconditions:
        - target in graph._vertices
        - all(c in graph._vertices for c in completed)

    >>> g = CourseGraph()
    >>> g.add_vertex(_CourseVertex('CSC108H1', 'Intro', None, None, 5, None, None))
    >>> g.add_vertex(_CourseVertex('CSC148H1', 'Intro 2', None, None, 5,
    ...     BooleanList('AND', ['CSC108H1']), None))
    >>> g.add_vertex(_CourseVertex('MAT137Y1', 'Calc', None, None, 5, None, None))
    >>> eligible_relevant_courses(g, set(), 'CSC148H1') == {'CSC108H1'}
    True
    """
    relevant = get_relevant_courses(graph, target, completed)
    eligible = graph.eligible_courses(completed)
    return (eligible & relevant) - {target} - completed


def _has_progress(prereqs: BooleanList, completed: set[str]) -> bool:
    """Return True if at least one sub-item in prereqs is already satisfied.

    AND nodes: True if any direct child is satisfied.
    OR nodes: True if any child has progress (recursive).

    Preconditions:
        - prereqs is a valid BooleanList

    >>> _has_progress(BooleanList('AND', ['CSC148H1', 'MAT137Y1']), {'CSC148H1'})
    True
    >>> _has_progress(BooleanList('AND', ['CSC148H1', 'MAT137Y1']), set())
    False
    >>> _has_progress(BooleanList('OR', ['CSC148H1', 'MAT137Y1']), {'MAT137Y1'})
    True
    """
    if prereqs.items is None:
        return False

    for item in prereqs.items:
        if isinstance(item, str) and item in completed:
            return True
        elif isinstance(item, BooleanList):
            if item.is_satisfied(completed):
                return True
            # For AND nodes, check if any sub item is satisfied (partial progress)
            if prereqs.operator == 'AND' and _has_progress(item, completed):
                return True
        elif isinstance(item, CreditCondition) and item.credits_satisfied(completed):
            return True

    return False


def _or_is_already_satisfied(prereqs: BooleanList, completed: set[str]) -> bool:
    """Return True if any direct child of an OR node is already satisfied.

    Preconditions:
        - prereqs.operator == 'OR'
        - prereqs.items is not None

    >>> _or_is_already_satisfied(BooleanList('OR', ['CSC148H1', 'MAT137Y1']), {'MAT137Y1'})
    True
    >>> _or_is_already_satisfied(BooleanList('OR', ['CSC148H1', 'MAT137Y1']), set())
    False
    """
    for item in prereqs.items:
        if isinstance(item, str) and item in completed:
            return True
        elif isinstance(item, BooleanList) and item.is_satisfied(completed):
            return True
        elif isinstance(item, CreditCondition) and item.credits_satisfied(completed):
            return True
    return False


def _partition_or_children(
        prereqs: BooleanList,
        completed: set[str],
        graph: CourseGraph
) -> tuple[list, list]:
    """Split the children of an OR node into two lists based on whether the
    student has already made progress on that branch.

    'Progress' means at least one sub-item inside a BooleanList branch is already
    satisfied.  Single course-code strings never count as a branch with progress,
    they are placed in the without-progress list so they can be evaluated normally
    for eligibility later.

    Returns:
        (with_progress, without_progress) — two lists whose union covers every
        valid, non-completed child of the OR node.

    Preconditions:
        - prereqs.operator == 'OR'
        - prereqs.items is not None
    """
    with_progress = []
    without_progress = []

    for item in prereqs.items:
        if isinstance(item, str):
            if item in completed or item not in graph.vertices:
                continue

            # Single course codes have no branch progress
            without_progress.append(item)
        elif isinstance(item, BooleanList):
            if _has_progress(item, completed):
                with_progress.append(item)
            else:
                without_progress.append(item)

    return with_progress, without_progress


def _collect_eligible_from_or_children(
        graph: CourseGraph,
        children: list,
        completed: set[str],
        visited: set[str]
) -> tuple[set[str], list]:
    """Scan a list of OR children and separate those that provide eligible courses
    right now from those that do not.

    For each child:
        - str: eligible if the student hasn't visited it yet and graph.is_eligible
          returns True.
        - BooleanList: recurses via _resolve_needed; if that produces any courses,
          those count as eligible results from this child.

    Preconditions:
        - all children are str, BooleanList, or CreditCondition items from an OR node
        - all(c in graph._vertices for c in completed)
    """
    eligible_courses: set[str] = set()
    non_eligible_children = []

    for item in children:
        if isinstance(item, str):
            if item in completed or item not in graph.vertices:
                continue
            if item not in visited and graph.is_eligible(item, completed):
                eligible_courses.add(item)
            else:
                non_eligible_children.append(item)
        elif isinstance(item, BooleanList):
            child_result = _resolve_needed(graph, item, completed, visited)
            if child_result:
                eligible_courses = eligible_courses.union(child_result)
            else:
                non_eligible_children.append(item)

    return eligible_courses, non_eligible_children


def _recurse_into_non_eligible_or(
        graph: CourseGraph,
        non_eligible_children: list,
        completed: set[str],
        visited: set[str]
) -> set[str]:
    """Recurse deeper into OR children that had no immediately eligible courses.

    For each string child, looks up that course's own prerequisite tree
    and calls _resolve_needed on it.

    BooleanList children are intentionally skipped here since they were already
    fully recursed inside _collect_eligible_from_or_children; arriving here
    means they returned empty, so there is nothing further to explore.

    Preconditions:
        - all items in non_eligible_children are str or BooleanList
        - all(c in graph._vertices for c in completed)
    """
    deeper: set[str] = set()

    for item in non_eligible_children:
        if isinstance(item, str):
            if item in visited or item in completed or item not in graph.vertices:
                continue
            visited.add(item)
            inner_vertex = graph.vertices[item]
            if inner_vertex.prerequisites and inner_vertex.prerequisites.items:
                deeper = deeper.union(_resolve_needed(graph, inner_vertex.prerequisites,
                                                      completed, visited))

    return deeper


def _resolve_or(graph: CourseGraph, prereqs: BooleanList,
                completed: set[str], visited: set[str]) -> set[str]:
    """Return actionable courses for an OR node.

    Prefers branches with prior progress; within those, prefers immediately
    eligible courses before recursing deeper into blocked ones.

    Preconditions:
        - prereqs.operator == 'OR'
        - prereqs.items is not None
        - all(c in graph._vertices for c in completed)
    """
    if _or_is_already_satisfied(prereqs, completed):
        return set()

    with_progress, without_progress = _partition_or_children(prereqs, completed, graph)

    # Focus on branches already started; if none, explore everything
    children_to_explore = with_progress if with_progress else prereqs.items

    eligible_courses, non_eligible_children = _collect_eligible_from_or_children(
        graph, children_to_explore, completed, visited
    )

    if eligible_courses:
        return eligible_courses

    return _recurse_into_non_eligible_or(graph, non_eligible_children, completed, visited)


def _resolve_and(graph: CourseGraph, prereqs: BooleanList,
                 completed: set[str], visited: set[str]) -> set[str]:
    """Return actionable courses for an AND node.

    Collects from all unsatisfied children simultaneously. Adds eligible string
    children directly; recurses into ineligible ones. CreditConditions are skipped.

    Preconditions:
        - prereqs.operator == 'AND'
        - prereqs.items is not None
        - all(c in graph._vertices for c in completed)
    """
    result: set[str] = set()

    for item in prereqs.items:
        if isinstance(item, str):
            if item in completed or item in visited or item not in graph.vertices:
                continue
            if graph.is_eligible(item, completed):
                result.add(item)
            else:
                visited.add(item)
                inner_vertex = graph.vertices[item]
                if inner_vertex.prerequisites and inner_vertex.prerequisites.items:
                    result = result.union(_resolve_needed(graph, inner_vertex.prerequisites,
                                                          completed, visited))
        elif isinstance(item, BooleanList):
            if not item.is_satisfied(completed):
                result = result.union(_resolve_needed(graph, item, completed, visited))
        elif isinstance(item, CreditCondition):
            continue

    return result


def _resolve_needed(graph: CourseGraph, prereqs: BooleanList,
                    completed: set[str], visited: set[str]) -> set[str]:
    """Traverse a prerequisite BooleanList tree and return the set of courses the
    student should pick from right now to make progress.

    Dispatches to _resolve_or or _resolve_and based on the node's operator, then
    returns their result.  visited is threaded through all recursive calls to
    prevent infinite loops when prerequisite trees have cycles.

    Preconditions:
        - prereqs is a valid BooleanList
        - all(c in graph._vertices for c in completed)
    """
    if prereqs.items is None:
        return set()

    if prereqs.operator == 'OR':
        return _resolve_or(graph, prereqs, completed, visited)
    else:
        return _resolve_and(graph, prereqs, completed, visited)


def get_next_needed_courses(graph: CourseGraph, target: str, completed: set[str]) -> set[str]:
    """Return the courses the student should take next to make progress toward target.

    Returns target itself if the student is now eligible. Otherwise walks the
    prerequisite tree and returns immediately takeable courses, recursing deeper
    for any that are still blocked.

    Preconditions:
        - target in graph._vertices
        - all(c in graph._vertices for c in completed)

    >>> g = CourseGraph()
    >>> g.add_vertex(_CourseVertex('CSC108H1', 'Intro', None, None, 5, None, None))
    >>> g.add_vertex(_CourseVertex('CSC148H1', 'Intro 2', None, None, 5,
    ...     BooleanList('AND', ['CSC108H1']), None))
    >>> g.add_vertex(_CourseVertex('CSC207H1', 'Software Design', None, None, 5,
    ...     BooleanList('AND', ['CSC148H1']), None))
    >>> get_next_needed_courses(g, 'CSC207H1', set()) == {'CSC108H1'}
    True
    >>> get_next_needed_courses(g, 'CSC207H1', {'CSC108H1'}) == {'CSC148H1'}
    True
    >>> get_next_needed_courses(g, 'CSC207H1', {'CSC108H1', 'CSC148H1'}) == {'CSC207H1'}
    True
    >>> get_next_needed_courses(g, 'CSC108H1', set()) == {'CSC108H1'}
    True
    """
    if target in completed:
        return set()

    if graph.is_eligible(target, completed):
        return {target}

    vertex = graph.vertices[target]
    if vertex.prerequisites is None or vertex.prerequisites.items is None:
        return {target}

    visited = set()
    return _resolve_needed(graph, vertex.prerequisites, completed, visited)


def search_courses(graph: CourseGraph, query: str) -> list[str]:
    """Return a list of course codes in the graph whose code or name contains
    the query string (case-insensitive).

    Results are sorted with exact code prefix matches first, then by course code.
    Used for the search bar when the student is inputting completed courses
    or selecting a target.

    Preconditions:
        - len(query) > 0

    >>> g = CourseGraph()
    >>> g.add_vertex(_CourseVertex('CSC108H1', 'Intro to Programming', None, None, 5, None, None))
    >>> search_courses(g, 'csc108')
    ['CSC108H1']
    >>> search_courses(g, 'intro')
    ['CSC108H1']
    """
    query_lower = query.lower()
    matches = []
    for code, vertex in graph.vertices.items():
        if query_lower in code.lower() or query_lower in vertex.name.lower():
            matches.append(code)

    matches.sort(key=lambda c: (not c.lower().startswith(query_lower), c))
    return matches
