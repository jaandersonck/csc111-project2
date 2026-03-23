from __future__ import annotations
from typing import Any


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

    operator: str
    items: list[str | BooleanList]

    def __init__(self, operator: str, items: list[str | BooleanList]) -> None:
        """Initialize a new BooleanList with the given operator and items."""
        self.operator = operator
        self.items = items

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
