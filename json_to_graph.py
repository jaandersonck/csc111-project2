""""""
from course_graph import CourseGraph, _CourseVertex
from boolean_list import BooleanList, CourseCondition, CreditCondition
import json


def _traverse_tree(tree: dict | list) -> BooleanList | CreditCondition | list:
    """..."""
    if isinstance(tree, dict):
        # looks like
        # {
        #     "operator": "OR",
        #     "items": [
        #         "STA302H1",
        #         "STA302H5"
        #     ]
        # }
        assert (all(key in {'operator', 'items'} for key in tree.keys()) or
                all(key in {'credits', 'department'} for key in tree.keys()))

        if all(key in {'operator', 'items'} for key in tree.keys()):
            # BOOLEANLIST TO BE READ
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
        elif all(key in {'credits', 'department'} for key in tree.keys()):
            # CREDITCONDITION TO BE READ
            credit_condition = CreditCondition(None, None)
            for key in tree:
                value: str | float = tree[key]

                if key == 'credits':
                    assert isinstance(value, float)
                    credit_condition.credits = value
                else:
                    # Department can be empty
                    assert isinstance(value, str) or value is None
                    credit_condition.department = value
            return credit_condition

    elif isinstance(tree, list):
        # looks like
        #     [
        #         "STA302H1",
        #         "STA302H5"
        #     ]
        # or contains dicts that are either (BOOLEAN LIST or CREDIT CONDITION)

        if all(isinstance(item, str) for item in tree):
            return tree
        else:
            lst = []
            for item in tree:
                assert isinstance(item, dict) or isinstance(item, str)

                if isinstance(item, str):
                    lst.append(CourseCondition('course', item))
                else:
                    # handle the dict case
                    res = _traverse_tree(item)
                    if isinstance(res, BooleanList):
                        lst.append(res)
                    elif isinstance(res, CreditCondition):
                        lst.append(CourseCondition('credit', res))
            return lst
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
    with open(file, 'r') as f:
        data = json.load(f)
        for course in data.values():
            prerequisites = parse_prerequisite_list(course['prereq_tree'])
            vert = _CourseVertex(course['code'], course['name'], course['hours'],
                                 course['description'], course['breadth'], prerequisites, course['exclusions'])
            graph.add_vertex(vert)
    return graph


if __name__ == "__main__":
    g = load_graph_from_json('data/courses_final.json')
