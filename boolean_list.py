from __future__ import annotations
from typing import Any
from dataclasses import dataclass

@dataclass
class CreditCondition:
    """..."""
    credits: float | None
    department: str | None


@dataclass
class CourseCondition:
    """...

    Representation Invariants:
        - self.kind in {'course', 'credit'}
        - (self.item is a valid course code) or (self.item is a valid credit condition)
        - self.kind == 'course' or not isinstance(self.item, str)
        - self.kind == 'credit' or not isinstance(self.item, CreditCondition)
    """
    kind: str
    item: str | CreditCondition


class BooleanList:
    """A recursive data structure that represents a logical condition over a set of courses.

    Each BooleanList has an operator (either 'AND' or 'OR') and a list of items,
    where each item is either a course code string or a nested BooleanList.

    An AND node is satisfied when all items in its list are satisfied.
    An OR node is satisfied when at least one item in its list is satisfied.

    Representation Invariants:
        - self.operator in {'AND', 'OR'}
        - len(self.items) >= 2
        - each element of self.items is either a non-empty string or a BooleanList
    """
    # Private Instance Attributes:
    #   - operator: Either 'AND' or 'OR', indicating whether all or any
    #               of the items must be satisfied.
    #   - items: A list where each element is either a course code string
    #            or a nested BooleanList representing a sub-condition.

    operator: str | None
    items: list[CourseCondition | BooleanList] | None

    def __init__(self, operator: str = None, items: list[CourseCondition | BooleanList] = None) -> None:
        """Initialize a new BooleanList with the given operator and items."""
        self.operator = operator
        self.items = items

    # Equality for BooleanList for doctests and ease of use
    def __eq__(self, candidate: BooleanList) -> bool:
        """
        >>> BooleanList('AND', []) == BooleanList('OR', [])
        False

        >>> BooleanList('AND', []) == BooleanList('AND', [])
        True

        >>> BooleanList('AND', [CourseCondition('course', 'CSC110')]) \
        == BooleanList('AND', [CourseCondition('course', 'CSC110')])
        True

        >>> BooleanList('AND', [CourseCondition('course', 'CSC110')]) \
        == BooleanList('AND', [CourseCondition('course', 'CSC11')])
        False
        """
        if self.operator != candidate.operator:
            return False
        elif len(self.items) != len(candidate.items):
            return False
        else:
            for i in range(len(self.items)):
                candidate_item = candidate.items[i]
                self_item = self.items[i]

                if not isinstance(candidate_item, type(self_item)):
                    return False
                # this is the recursive call, when comparing two BooleanLists
                if self_item != candidate_item:
                    return False
        return True

    def is_satisfied(self, completed: set[str]) -> bool:
        """Return whether this boolean condition is satisfied given a set of completed course codes.

        If this BooleanList has operator 'AND', all items must be satisfied.
        If this BooleanList has operator 'OR', at least one item must be satisfied.
        Each item is either a course code string, a credits node, or a nested BooleanList,
        all of which are evaluated recursively.

        completed is the set of course codes the student has already finished.

        >>> bl = BooleanList('AND', ['CSC148H1', 'CSC165H1'])
        >>> bl.is_satisfied({'CSC148H1', 'CSC165H1', 'MAT137Y1'})
        True
        >>> bl.is_satisfied({'CSC148H1'})
        False

        >>> bl = BooleanList('OR', ['CSC148H1', 'CSC111H1'])
        >>> bl.is_satisfied({'CSC111H1'})
        True
        >>> bl.is_satisfied({'MAT137Y1'})
        False
        """

        if isinstance(self, str):
            return self in completed
        elif self.operator == 'AND':
            return all(item in completed for item in self.items)
        elif self.operator == 'OR':
            return any(item in completed for item in self.items)

    def arrange(self) -> BooleanList:
        """Return a BooleanList such that each sublist contains non-recursive types first, and
        sub-BooleanLists last.

        >>> bl = BooleanList('AND', [BooleanList('OR', [1, 2]), 1, 2])
        >>> bl.arrange()
        >>> bl == BooleanList('AND', [1, 2, BooleanList('OR', [1,2])])
        True
        """
        arranged, boolean_lists = [], []
        for item in self.items:
            if isinstance(item, BooleanList):
                boolean_lists.append(item.arrange())
            else:
                arranged.append(item)

        arranged.extend(boolean_lists)
        return BooleanList(self.operator, arranged)

    def generate_combinations(self) -> list[list]:
        """Return a list of all combinations that satisfy the condition built by the BooleanList.

        The returned list contains other non-nested lists, where each list represents a distinct
        and valid combination.

        Preconditions:
            - self is a valid BooleanList

        >>> BooleanList('AND', [BooleanList('OR', [1,2]), 3, 4]).generate_combinations()
        [[1, 3, 4], [2, 3, 4]]
        """
        options_at_depth = []
        for item in self.items:
            if isinstance(item, BooleanList):
                options_at_depth.append(item.generate_combinations())
            else:
                options_at_depth.append([[item]])

        # CLAUDE:
        if self.operator == 'AND':
            result = [[]]
            for options in options_at_depth:
                result = [partial + option for partial in result for option in options]
            return result
        else:
            return [path for paths in options_at_depth for path in paths]
