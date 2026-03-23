from boolean_list import BooleanList


class _CourseVertex:
    """A vertex in a CourseGraph, representing a single UofT course.

    Instance Attributes:
        - code: the course code, e.g. 'CSC111H1'
        - name: the full course name
        - hours: the weekly contact hours string, e.g. '36L/12T'
        - description: the course description from the A&S calendar
        - breadth: the breadth requirement category number, or None if not applicable
        - credits: the credit weight, either 0.5 for H courses or 1.0 for Y courses
        - level: the course level, one of 100, 200, 300, or 400
        - department: the department code prefix, e.g. 'CSC'
        - prerequisites: the prerequisite condition as a BooleanList, or None if there are none
        - exclusions: a list of course codes that cannot be taken alongside this course, or None

    Representation Invariants:
        - self.credits in {0.5, 1.0}
        - self.level in {100, 200, 300, 400}
        - len(self.code) > 0
    """
    code: str
    name: str
    hours: str | None
    description: str | None
    breadth: int | None
    credits: float
    level: int
    department: str
    prerequisites: BooleanList | None
    exclusions: list[str] | None

    def __init__(self,
                 code: str,
                 name: str,
                 hours: str | None,
                 description: str | None,
                 breadth: int | None,
                 prerequisites: BooleanList | None,
                 exclusions: list[str] | None) -> None:
        """Initialize a new vertex with the given course details."""
        self.code = code
        self.name = name
        self.hours = hours
        self.description = description
        self.breadth = breadth
        self.prerequisites = prerequisites
        self.exclusions = exclusions
        self.credits = 1.0 if code.endswith('Y1') else 0.5
        self.level = int(next(c for c in code if c.isdigit())) * 100
        self.department = ''.join(c for c in code if c.isalpha())[:-1]
