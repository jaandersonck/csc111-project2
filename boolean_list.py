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
    items: list[CreditCondition | BooleanList] | None

    def __init__(self, operator: str = None, items: list[CreditCondition | BooleanList] = None) -> None:
        """Initialize a new BooleanList with the given operator and items."""
        self.operator = operator
        self.items = items

    def is_satisfied(self, completed: set[str]) -> bool:
        """Return whether this condition is satisfied given a set of completed course codes."""
        raise NotImplementedError
