"""Functions for moving between json and CourseGraph/_CourseVertex."""
import json
from course_graph import CourseGraph, _CourseVertex
from boolean_list import BooleanList, CreditCondition


def _dict_to_boolean_list(tree: dict) -> BooleanList:
    """Return a BooleanList from a given dict, formatted for BooleanList.

    Preconditions:
        - len(tree) == 2
        - all(key in {'operator', 'items'} for key in tree.keys())
        - isinstance(tree['operator'], str) or tree['operator'] is None
        - isinstance(tree['items'], list) or tree['items'] is None
    """
    boolean_node = BooleanList()
    for key in tree:
        value: str | list[str | dict] = tree[key]

        if key == 'operator':
            assert value in {'AND', 'OR'}
            boolean_node.operator = value
        else:
            assert isinstance(value, list)
            boolean_node.items = _traverse_tree(value)
    return boolean_node


def _dict_to_credit_condition(tree: dict) -> CreditCondition:
    """Return a CreditCondition from a given dict, formatted for CreditCondition.

    Preconditions:
        - len(tree) == 2
        - all(key in {'credits', 'department'} for key in tree.keys())
        - isinstance(tree['credits'], float) or tree['credits'] is None
        - isinstance(tree['department'], str) or tree['department'] is None
    """
    credit_condition = CreditCondition(None, None)
    for key in tree:
        value: str | float = tree[key]

        if key == 'credits':
            assert isinstance(value, float)
            credit_condition.amount_credits = value
        else:
            # Department can be empty
            assert isinstance(value, str) or value is None
            credit_condition.department = value
    return credit_condition


def _raw_list_to_formatted(tree: list) -> list[BooleanList]:
    """Return a list that is a valid candidate for BooleanList.items, that is, take a raw
    list and convert all values to be one of {CourseCondition, BooleanList}.

    Preconditions:
        - all(isinstance(item, dict) or isinstance(item, str) for item in tree)
        - for all items in tree that are dict, they are formatted appropriately to be
        either BooleanList or CreditCondition
    """
    lst = []
    for item in tree:
        assert isinstance(item, (dict, str))

        if isinstance(item, str):
            lst.append(item)
        else:
            # Handle the dict case
            result = _traverse_tree(item)
            if isinstance(result, BooleanList):
                # Per the defintion, BooleanList can contain other BooleanList
                lst.append(result)
            elif isinstance(result, CreditCondition):
                lst.append(result)
    return lst


def _traverse_tree(tree: dict | list) -> BooleanList | CreditCondition | list:
    """Return a BooleanList representation of the provided tree, given that the initial value
    of tree always represents a BooleanList.

    Preconditions:
        - on the base function call, tree is a dict representing a BooleanList
        - each dict represents a BooleanList or a CreditCondition based on their
        respective definitions
        - each dict representing a BooleanList contains items representing the
        following types: {str, BooleanList, CreditCondition}, or is empty.

    >>> bd = {'operator': 'AND', 'items': ['CSC110']}
    >>> _traverse_tree(bd) == BooleanList('AND', ['CSC110'])
    True
    """
    if isinstance(tree, dict):
        # assert (all(key in {'operator', 'items'} for key in tree.keys()) or
        #         all(key in {'credits', 'department'} for key in tree.keys()))
        # tree represents either a BooleanList or a CreditCondition
        if all(key in {'operator', 'items'} for key in tree.keys()):
            # Effective base-case
            return _dict_to_boolean_list(tree)
        elif all(key in {'credits', 'department'} for key in tree.keys()):
            return _dict_to_credit_condition(tree)
    elif isinstance(tree, list):
        # tree is a list containing str, booleanlistdict or creditconditiondict
        return _raw_list_to_formatted(tree)

    # Return an empty BooleanList otherwise
    return BooleanList()


def parse_prerequisite_list(tree: dict) -> BooleanList:
    """Parse the given prerequisite tree, returning a BooleanList.

    Preconditions:
        - prerequisite tree is valid according to project standards
    """
    prerequisite_list: BooleanList = _traverse_tree(tree)
    return prerequisite_list


def load_graph_from_json(file: str) -> CourseGraph:
    """Load each course from a valid json file into a CourseGraph consisting of distinct _CourseVertex.
    Return the resulting CourseGraph.

    Preconditions:
        - file exists and is valid json and is formatted according to project standards
    """
    graph = CourseGraph()
    with open(file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        for course in data.values():
            prerequisites = parse_prerequisite_list(course['prereq_tree'])
            vert = _CourseVertex(course['code'], course['name'], prerequisites)
            vert.hours = course['hours']
            vert.description = course['description']
            vert.breadth = course['breadth']
            vert.exclusions = course['exclusions']
            graph.add_vertex(vert)

    return graph


if __name__ == '__main__':
    import doctest
    doctest.testmod()
    # import python_ta
    # python_ta.check_all(config={
    #     'extra-imports': ['course_graph', 'boolean_list', 'json'],
    #     'allowed-io': ['load_graph_from_json'],
    #     'max-line-length': 120
    # })
