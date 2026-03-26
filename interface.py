"""Interactive course pathway navigator.

This module provides a Tkinter-based graphical interface that allows a student
to build a personalized course pathway toward a target course. The student
selects completed courses and a target, then chooses courses layer by layer
from the set of currently eligible and relevant options until the target is
reached.
"""

from course_graph import CourseGraph
from algorithms import eligible_relevant_courses, is_target_reachable
from json_to_graph import load_graph_from_json


def setup_window(graph: CourseGraph) -> None:
    """Initialize the main Tkinter window and all UI components.

    Creates the root window with the following sections:
        - A search/input area for selecting completed courses and the target course
        - A display area showing the currently eligible relevant courses as clickable buttons
        - A sidebar or panel showing the path built so far (courses selected in order)
        - A status label indicating progress toward the target
        - A reset button to start over

    This function starts the Tkinter main loop and should be called once from main.
    """


def update_eligible_display(graph: CourseGraph, completed: set[str], target: str) -> None:
    """Refresh the eligible courses panel to show the current layer of options.

    Clears the previous set of course buttons and generates new ones based on
    the courses returned by eligible_relevant_courses. If the target is already
    in completed, displays a success message instead. If no eligible relevant
    courses remain and the target is not reached, displays a dead-end warning.
    """


def on_course_selected(graph: CourseGraph, completed: set[str], target: str, course: str) -> None:
    """Handle the event when the user clicks on a course button.

    Adds the selected course to the completed set, appends it to the path display,
    and calls update_eligible_display to refresh the next layer of options.
    If the selected course is the target, displays a completion message.
    """


def add_completed_course(graph: CourseGraph, completed: set[str], course_code: str) -> bool:
    """Validate and add a course code to the completed set from the search input.

    Returns True if the course code exists in the graph and was successfully added,
    False otherwise. Updates the completed courses display panel accordingly.
    """


def set_target(graph: CourseGraph, target_entry: str) -> str | None:
    """Validate and set the target course from user input.

    Returns the target course code if it exists in the graph, or None if the
    course code is invalid. Displays an error message to the user if invalid.
    """


def update_path_display(path: list[str]) -> None:
    """Refresh the path panel to show all courses the user has selected so far,
    in the order they were chosen.
    """


def reset(graph: CourseGraph) -> None:
    """Clear all state and return the interface to its initial empty state.

    Resets the completed set, the path list, the target, and all display panels.
    """


def visualize_relevant_subgraph(graph: CourseGraph, completed: set[str],
                                 target: str, current_eligible: set[str]) -> None:
    """Display the relevant prerequisite subgraph leading to target, with courses
    colour-coded by status:
        - completed courses in one colour
        - currently eligible courses in another
        - not yet reachable courses in a third
        - the target course highlighted distinctly

    Uses plotly and networkx to render the graph. Updates each time the user
    selects a course so the student can see their progress visually.
    """


def show_course_info(graph: CourseGraph, course_code: str) -> None:
    """Display detailed information about a course when the user hovers over
    or clicks an info button next to a course option.

    Shows the course name, description, breadth requirement, credit weight,
    and prerequisite tree in a readable format.
    """


def search_courses(graph: CourseGraph, query: str) -> list[str]:
    """Return a list of course codes in the graph whose code or name contains
    the query string (case-insensitive).

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
