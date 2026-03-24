from __future__ import annotations
from typing import Any
from dataclasses import dataclass


class CreditCondition:
    """..."""
    amount_credits: float | None
    department: str | None

    def __init__(self, amount_credits: float | None, department: str | None) -> None:
        self.amount_credits = amount_credits
        self.department = department

    def credits_satisfied(self, current_credits: set) -> bool:
        """Return whether the credit condition is satisfied given the current completed courses.

        >>> cc = CreditCondition(1.0, None)
        >>> cc.credits_satisfied({'CSC148H1', 'CSC165H1'})
        True
        >>> cc.credits_satisfied({'CSC148H1'})
        False

        >>> cc = CreditCondition(1.0, 'CSC')
        >>> cc.credits_satisfied({'CSC148H1', 'MAT137Y1'})
        False
        >>> cc.credits_satisfied({'CSC148H1', 'CSC165H1'})
        True
        """

        if self.amount_credits is None or self.amount_credits == 0:
            return True
        elif self.department is None:
            return self.calculate_total_credits(current_credits) >= self.amount_credits
        else:
            return self.calculate_credits_department(current_credits, self.department) >= self.amount_credits

    @staticmethod
    def calculate_total_credits(current_credits: set) -> float:
        """Return the total credits accumulated from the given set of course codes.

        >>> cc = CreditCondition(None, None)
        >>> cc.calculate_total_credits({'CSC148H1', 'MAT137Y1'})
        1.5
        >>> cc.calculate_total_credits(set())
        0.0
        """

        credits_so_far = 0.0
        for credit in current_credits:
            if credit[-2] == 'H':
                credits_so_far += 0.5
            elif credit[-2] == 'Y':
                credits_so_far += 1.0
        return credits_so_far

    @staticmethod
    def calculate_credits_department(current_credits: set, target_departement: str) -> float:
        """Return the total credits from courses in target_department within current_credits.

        >>> CreditCondition.calculate_credits_department({'CSC148H1', 'CSC165H1', 'MAT137Y1'}, 'CSC')
        1.0
        >>> CreditCondition.calculate_credits_department({'CSC148H1', 'MAT137Y1'}, 'MAT')
        1.0
        >>> CreditCondition.calculate_credits_department({'CSC148H1'}, 'MAT')
        0.0
        """

        credits_so_far = 0.0
        for credit in current_credits:
            credit_departement = credit[:3]
            if credit_departement == target_departement:
                if credit[-2] == 'H':
                    credits_so_far += 0.5
                elif credit[-2] == 'Y':
                    credits_so_far += 1.0
        return credits_so_far


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
    items: list[BooleanList | str | CreditCondition] | None

    def __init__(self, operator: str = None, items: list[CourseCondition | BooleanList] = None) -> None:
        """Initialize a new BooleanList with the given operator and items."""
        self.operator = operator
        self.items = items

    @staticmethod
    def evaluate_item(item: str | CreditCondition | BooleanList, completed: set[str]) -> bool:
        """Evaluate statements based on the type of instance.
            Preconditions:
            - isinstance(item, (str, CreditCondition, BooleanList))

            >>> bl = BooleanList('AND', ['CSC148H1'])
            >>> bl.evaluate_item('CSC148H1', {'CSC148H1', 'MAT137Y1'})
            True
            >>> bl.evaluate_item('CSC148H1', {'MAT137Y1'})
            False

            >>> bl.evaluate_item(CreditCondition(1.0, None), {'CSC148H1', 'CSC165H1'})
            True
            >>> bl.evaluate_item(CreditCondition(1.0, None), {'CSC148H1'})
            False

            >>> nested = BooleanList('OR', ['CSC148H1', 'CSC111H1'])
            >>> bl.evaluate_item(nested, {'CSC111H1'})
            True
            >>> bl.evaluate_item(nested, {'MAT137Y1'})
            False
        """

        if isinstance(item, BooleanList):
            return item.is_satisfied(completed)
        elif isinstance(item, str):
            return item in completed
        elif isinstance(item, CreditCondition):
            return item.credits_satisfied(completed)
        else:
            raise ValueError(f'Unknown item type: {type(item)}')

    # Equality for BooleanList for doctests and ease of use
    def __eq__(self, candidate: BooleanList) -> bool:
        """
        >>> BooleanList('AND', []) == BooleanList('OR', [])
        False

        >>> BooleanList('AND', []) == BooleanList('AND', [])
        True

        >>> BooleanList('AND', ['CSC110']) \
        == BooleanList('AND', ['CSC110'])
        True

        >>> BooleanList('AND', ['CSC110']) \
        == BooleanList('AND', ['CSC11'])
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

    # Allow BooleanList to be represented in console
    def __repr__(self) -> str:
        """
        >>> BooleanList('AND', [1,2,3])
        (1 AND 2 AND 3)

        >>> BooleanList('OR', [1,2])
        (1 OR 2)

        >>> BooleanList('AND', [1, 2, BooleanList('OR', [3, 4])])
        (1 AND 2 AND (3 OR 4))
        """
        s = ''
        if self.operator == 'AND':
            p = [item.__repr__() for item in self.items]
            s = ' AND '.join(p)
            s = f'({s})'
        else:
            p = [item.__repr__() for item in self.items]
            s = ' OR '.join(p)
            s = f'({s})'
        return s

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

        if self.operator == 'AND':
            return all(self.evaluate_item(item, completed) for item in self.items)
        else:
            return any(self.evaluate_item(item, completed) for item in self.items)

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
        #########################
        # UNDERSTAND THIS
        #########################
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
