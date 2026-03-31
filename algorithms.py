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
    """Return the set of courses that the student is both currently eligible to take
    and that are relevant to reaching the target course.

    This is the intersection of all courses the student can currently enrol in
    (based on their completed courses) and all courses that lie on some
    prerequisite path leading to target. The target itself is excluded from
    the result (it is handled separately by the interface).

    Preconditions:
        - target in graph._vertices
        - all(c in graph._vertices for c in completed)

    >>> from course_graph import CourseGraph, _CourseVertex
    >>> from boolean_list import BooleanList
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
    """Return whether the student has made any progress toward satisfying this
    BooleanList node — meaning at least one sub-item is fully satisfied.

    For AND nodes: True if at least one child is satisfied.
    For OR nodes: True if at least one child has progress (recursive).

    This is used to detect which branch of a top-level OR the student has
    started working on, so we can prioritize that branch.

    Preconditions:
        - prereqs is a valid BooleanList
    """
    if prereqs.items is None:
        return False

    for item in prereqs.items:
        if isinstance(item, str) and item in completed:
            return True
        elif isinstance(item, BooleanList):
            if item.is_satisfied(completed):
                return True
            # For AND nodes, check if any sub-item is satisfied (partial progress)
            if prereqs.operator == 'AND' and _has_progress(item, completed):
                return True
        elif isinstance(item, CreditCondition) and item.credits_satisfied(completed):
            return True

    return False


def _resolve_needed(graph: CourseGraph, prereqs: BooleanList,
                    completed: set[str], visited: set[str]) -> set[str]:
    """Walk a prerequisite BooleanList tree and return the set of courses the student
    should pick from right now to make progress.

    This function combines tree-pruning and eligibility-checking in one pass:

    For AND nodes: collects actionable courses from ALL unsatisfied children.
    For OR nodes:
        - If any child is already satisfied → returns empty (requirement met).
        - Otherwise, collects eligible courses from all children.
        - If some children yield eligible courses and others don't, only returns
          the eligible ones (no need to recurse deeper into harder alternatives
          when easier options exist).
        - Only recurses into non-eligible children if NO child has eligible courses.

    For each leaf course code found:
        - If the student is eligible → includes it directly.
        - If not eligible → recurses into that course's own prereq tree.

    visited prevents infinite loops when prerequisite trees have cycles.

    Preconditions:
        - prereqs is a valid BooleanList
        - all(c in graph._vertices for c in completed)
    """
    if prereqs.items is None:
        return set()

    if prereqs.operator == 'OR':
        # If ANY child is already satisfied, the whole OR is done
        for item in prereqs.items:
            if isinstance(item, str) and item in completed:
                return set()
            elif isinstance(item, BooleanList) and item.is_satisfied(completed):
                return set()
            elif isinstance(item, CreditCondition) and item.credits_satisfied(completed):
                return set()

        # Nothing satisfied — check if user has made progress on any branch
        # If so, only show courses from the branch(es) with progress
        children_with_progress = []
        children_without_progress = []

        for item in prereqs.items:
            if isinstance(item, str):
                # A single course option — no "progress" concept, just eligible or not
                if item in completed:
                    continue
                if item not in graph.vertices:
                    continue
                # Treat as no-progress child (it's a single course, not a branch)
                children_without_progress.append(item)
            elif isinstance(item, BooleanList):
                if _has_progress(item, completed):
                    children_with_progress.append(item)
                else:
                    children_without_progress.append(item)

        # If some branches have progress, only explore those
        children_to_explore = children_with_progress if children_with_progress else prereqs.items

        # Collect eligible courses from the branches we're exploring
        eligible_from_children = set()
        non_eligible_children = []

        for item in children_to_explore:
            if isinstance(item, str):
                if item in completed:
                    continue
                if item not in graph.vertices:
                    continue
                if item not in visited and graph.is_eligible(item, completed):
                    eligible_from_children.add(item)
                else:
                    non_eligible_children.append(item)
            elif isinstance(item, BooleanList):
                child_result = _resolve_needed(graph, item, completed, visited)
                if child_result:
                    eligible_from_children |= child_result
                else:
                    non_eligible_children.append(item)

        # If we found eligible courses, return those — don't dig into harder paths
        if eligible_from_children:
            return eligible_from_children

        # No eligible courses found — recurse deeper into non-eligible children
        deeper = set()
        for item in non_eligible_children:
            if isinstance(item, str):
                if item in visited or item in completed or item not in graph.vertices:
                    continue
                visited.add(item)
                inner_vertex = graph.vertices[item]
                if inner_vertex.prerequisites and inner_vertex.prerequisites.items:
                    deeper |= _resolve_needed(graph, inner_vertex.prerequisites,
                                              completed, visited)
            # BooleanList children were already recursed into above
        return deeper

    else:  # AND
        # Collect actionable courses from all unsatisfied children
        result = set()
        for item in prereqs.items:
            if isinstance(item, str):
                if item in completed:
                    continue
                if item in visited or item not in graph.vertices:
                    continue
                if graph.is_eligible(item, completed):
                    result.add(item)
                else:
                    # Recurse into this course's prereqs
                    visited.add(item)
                    inner_vertex = graph.vertices[item]
                    if inner_vertex.prerequisites and inner_vertex.prerequisites.items:
                        result |= _resolve_needed(graph, inner_vertex.prerequisites,
                                                  completed, visited)
            elif isinstance(item, BooleanList):
                if not item.is_satisfied(completed):
                    result |= _resolve_needed(graph, item, completed, visited)
            elif isinstance(item, CreditCondition):
                continue
        return result


def get_next_needed_courses(graph: CourseGraph, target: str, completed: set[str]) -> set[str]:
    """Return the set of courses the student should consider taking next to make
    progress toward the target course.

    Walks the target's prerequisite tree, prunes satisfied branches, and for
    each remaining needed course:
        - if the student is eligible to take it now, includes it in the result
        - if the student is NOT eligible (its own prereqs aren't met), recurses
          into that course's prereq tree instead to find deeper prerequisites
        - within OR groups, prefers showing eligible courses over recursing into
          harder alternatives (e.g. if STA237H1 is eligible, don't also show
          the deep prereq chains of STA255H1)

    Also includes the target itself if the student is now eligible for it.

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

    >>> from course_graph import CourseGraph, _CourseVertex
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
