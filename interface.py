"""CSC111 Winter 2026 Project 2: Course Pathway Navigator (Interface)

Module Description
==================

This module contains the Tkinter interface for the course pathway navigator.
It lets a student input their completed courses and a target course, then
guides them through selecting prerequisite courses layer by layer until the
target is reachable.

Copyright and Usage Information
===============================

This file is Copyright (c) 2026.
"""
from __future__ import annotations
import tkinter as tk
from tkinter import messagebox

from course_graph import CourseGraph
from boolean_list import BooleanList, CreditCondition
from algorithms import get_next_needed_courses, search_courses, get_course_codes
from json_to_graph import load_graph_from_json
from visualizations import visualize_course_graph


# COLORS
BACKGROUND = '#0d1117'
PANEL = '#161b22'
CARD = '#21262d'
CARD_HOVER = '#30363d'
BLUE = '#1f6feb'
GREEN = '#3fb950'
YELLOW = '#d29922'
RED = '#f85149'
WHITE = '#e6edf3'
GREY = '#8b949e'
DARK_GREY = '#484f58'
BORDER_COLOUR = '#30363d'


class CourseNavigator:
    """A Tkinter application that guides a student through picking courses
    layer by layer until they reach a target course.

    Instance Attributes:
        - graph: the course prerequisite graph
        - completed: set of course codes the student has completed
        - target: the target course code the student wants to reach
        - path: ordered list of courses selected during navigation
        - phase: either 'setup' or 'navigate'
    """
    graph: CourseGraph
    completed: set[str]
    target: str | None
    path: list[str]
    phase: str

    def __init__(self, graph: CourseGraph) -> None:
        """Initialize the navigator with the given course graph."""
        self.graph = graph
        self.completed = set()
        self.target = None
        self.path = []
        self.phase = 'setup'

        # Create the window
        self.root = tk.Tk()
        self.root.title('Course Pathway Navigator')
        self.root.geometry('1100x720')
        self.root.configure(bg=BACKGROUND)
        self.root.minsize(900, 550)

        # Build layout and show setup screen
        self._build_layout()
        self._show_setup()
        self.root.mainloop()

    def _build_layout(self) -> None:
        """Create the header bar and the three main panels (left, centre, right)."""
        # Header
        header = tk.Frame(self.root, bg=PANEL, height=48)
        header.pack(fill='x')
        header.pack_propagate(False)

        tk.Label(header, text='Course Pathway Navigator',
                 font=('Helvetica', 16, 'bold'), bg=PANEL, fg=WHITE).pack(side='left', padx=16)

        self.status_label = tk.Label(header, text='', font=('Helvetica', 10),
                                     bg=PANEL, fg=GREY)
        self.status_label.pack(side='right', padx=16)

        # Thin line under header
        tk.Frame(self.root, bg=BLUE, height=1).pack(fill='x')

        # Main area
        main_frame = tk.Frame(self.root, bg=BACKGROUND)
        main_frame.pack(fill='both', expand=True)

        self.left_panel = tk.Frame(main_frame, bg=PANEL, width=260)
        self.left_panel.pack(side='left', fill='y')
        self.left_panel.pack_propagate(False)

        self.centre_panel = tk.Frame(main_frame, bg=BACKGROUND)
        self.centre_panel.pack(side='left', fill='both', expand=True)

        self.right_panel = tk.Frame(main_frame, bg=PANEL, width=280)
        self.right_panel.pack(side='right', fill='y')
        self.right_panel.pack_propagate(False)

    # ***************Setup phase******************

    def _show_setup(self) -> None:
        """Show the setup screen where user adds completed courses and picks a target."""
        self.phase = 'setup'
        self.status_label.config(text='Setup')
        self._clear_all_panels()

        # --- Left panel: list of completed courses ---
        tk.Label(self.left_panel, text='COMPLETED COURSES', font=('Helvetica', 9),
                 bg=PANEL, fg=DARK_GREY).pack(pady=(14, 2), padx=14, anchor='w')
        tk.Frame(self.left_panel, bg=BORDER_COLOUR, height=1).pack(fill='x', padx=14, pady=(0, 8))

        self.completed_listbox = tk.Listbox(
            self.left_panel, bg=CARD, fg=WHITE, font=('Courier', 10),
            selectbackground=BLUE, selectforeground=WHITE,
            borderwidth=0, highlightthickness=0, relief='flat'
        )
        self.completed_listbox.pack(fill='both', expand=True, padx=12, pady=(0, 8))

        # Remove button
        remove_btn = tk.Label(self.left_panel, text='  Remove selected  ',
                              font=('Helvetica', 10), bg=RED, fg=WHITE,
                              cursor='hand2', pady=6)
        remove_btn.pack(padx=14, pady=3, fill='x')
        remove_btn.bind('<Button-1>', lambda e: self._remove_completed_course())

        # --- Centre panel: the two search bars and start button ---
        centre_frame = tk.Frame(self.centre_panel, bg=BACKGROUND)
        centre_frame.pack(expand=True)

        # Section: add completed courses
        tk.Label(centre_frame, text='Add completed courses',
                 font=('Helvetica', 12, 'bold'), bg=BACKGROUND, fg=WHITE).pack(pady=(0, 4))
        tk.Label(centre_frame, text='Search by code or name',
                 font=('Helvetica', 9), bg=BACKGROUND, fg=DARK_GREY).pack()

        completed_search_row = tk.Frame(centre_frame, bg=BACKGROUND)
        completed_search_row.pack(pady=(6, 0))

        self.search_var = tk.StringVar()
        self.search_var.trace_add('write', self._on_completed_search_typed)

        completed_search_entry = tk.Entry(
            completed_search_row, textvariable=self.search_var,
            font=('Helvetica', 11), width=28,
            bg=CARD, fg=WHITE, insertbackground=WHITE,
            borderwidth=0, highlightthickness=1,
            highlightcolor=BLUE, highlightbackground=BORDER_COLOUR
        )
        completed_search_entry.pack(side='left', ipady=5, padx=(0, 6))

        add_btn = tk.Label(completed_search_row, text='  Add  ',
                           font=('Helvetica', 10), bg=GREEN, fg=WHITE,
                           cursor='hand2', pady=6, padx=10)
        add_btn.pack(side='left')
        add_btn.bind('<Button-1>', lambda e: self._add_completed_from_entry())

        # Dropdown for completed course search results
        self.completed_search_dropdown = tk.Frame(centre_frame, bg=CARD)
        self.completed_search_dropdown.pack(fill='x', padx=60, pady=(0, 4))

        # Divider line
        tk.Frame(centre_frame, bg=BORDER_COLOUR, height=1).pack(fill='x', padx=50, pady=16)

        # Section: set target course
        tk.Label(centre_frame, text='Set target course',
                 font=('Helvetica', 12, 'bold'), bg=BACKGROUND, fg=WHITE).pack(pady=(0, 4))
        tk.Label(centre_frame, text='The course you want to reach',
                 font=('Helvetica', 9), bg=BACKGROUND, fg=DARK_GREY).pack()

        target_search_row = tk.Frame(centre_frame, bg=BACKGROUND)
        target_search_row.pack(pady=(6, 0))

        self.target_var = tk.StringVar()
        self.target_var.trace_add('write', self._on_target_search_typed)

        target_search_entry = tk.Entry(
            target_search_row, textvariable=self.target_var,
            font=('Helvetica', 11), width=28,
            bg=CARD, fg=WHITE, insertbackground=WHITE,
            borderwidth=0, highlightthickness=1,
            highlightcolor=YELLOW, highlightbackground=BORDER_COLOUR
        )
        target_search_entry.pack(side='left', ipady=5, padx=(0, 6))

        # Dropdown for target search results
        self.target_search_dropdown = tk.Frame(centre_frame, bg=CARD)
        self.target_search_dropdown.pack(fill='x', padx=60, pady=(0, 4))

        # Divider line
        tk.Frame(centre_frame, bg=BORDER_COLOUR, height=1).pack(fill='x', padx=50, pady=16)

        # Start button
        start_btn = tk.Label(centre_frame, text='  Start navigating  ->  ',
                             font=('Helvetica', 10), bg=BLUE, fg=WHITE,
                             cursor='hand2', pady=6, padx=10)
        start_btn.pack()
        start_btn.bind('<Button-1>', lambda e: self._start_navigation())

        # --- Right panel: instructions ---
        tk.Label(self.right_panel, text='HOW IT WORKS', font=('Helvetica', 9),
                 bg=PANEL, fg=DARK_GREY).pack(pady=(14, 2), padx=14, anchor='w')
        tk.Frame(self.right_panel, bg=BORDER_COLOUR, height=1).pack(fill='x', padx=14, pady=(0, 8))

        instructions = [
            '1  Add courses you\'ve already completed.',
            '2  Type the course you want to reach.',
            '3  Click Start.',
            '4  Pick courses from the options shown.',
            '5  Repeat until you reach your target.',
        ]
        for instruction_text in instructions:
            tk.Label(self.right_panel, text=instruction_text, font=('Helvetica', 10),
                     bg=PANEL, fg=GREY, wraplength=240, justify='left',
                     anchor='w').pack(padx=14, pady=2, anchor='w')

    # ******************Navigation phase***************

    def _start_navigation(self) -> None:
        """Validate the target input and switch to navigation mode."""
        target_code = self.target_var.get().strip().upper()

        if target_code == '':
            messagebox.showwarning('Missing target', 'Enter a target course code.')
            return

        if target_code not in self.graph._vertices:
            messagebox.showerror('Invalid course', f'"{target_code}" not found.')
            return

        if target_code in self.completed:
            messagebox.showinfo('Already done', f'You already completed {target_code}.')
            return

        self.target = target_code
        self.path = []
        self.phase = 'navigate'
        self.status_label.config(text='Target: ' + self.target)

        # Rebuild all panels for navigation mode
        self._clear_all_panels()
        self._build_navigation_left_panel()
        self._build_navigation_right_panel()
        self._refresh_course_options()

    def _build_navigation_left_panel(self) -> None:
        """Build the left sidebar that shows the target and the path so far."""
        # Target label
        tk.Label(self.left_panel, text='TARGET', font=('Helvetica', 9),
                 bg=PANEL, fg=DARK_GREY).pack(pady=(14, 0), padx=14, anchor='w')
        tk.Label(self.left_panel, text=self.target, font=('Courier', 11),
                 bg=PANEL, fg=YELLOW).pack(padx=14, anchor='w')

        # Divider
        tk.Frame(self.left_panel, bg=BORDER_COLOUR, height=1).pack(fill='x', padx=14, pady=10)

        # Path section
        tk.Label(self.left_panel, text='YOUR PATH', font=('Helvetica', 9),
                 bg=PANEL, fg=DARK_GREY).pack(padx=14, anchor='w')

        self.path_frame = tk.Frame(self.left_panel, bg=PANEL)
        self.path_frame.pack(fill='both', expand=True, padx=14, pady=(4, 0))
        self._refresh_path_display()

        # Divider
        tk.Frame(self.left_panel, bg=BORDER_COLOUR, height=1).pack(fill='x', padx=14, pady=8)

        # Completed count
        self.completed_count_label = tk.Label(
            self.left_panel, text=str(len(self.completed)) + ' completed',
            font=('Helvetica', 9), bg=PANEL, fg=DARK_GREY
        )
        self.completed_count_label.pack(padx=14, anchor='w', pady=(0, 8))

        # Undo button
        undo_btn = tk.Label(self.left_panel, text='  Undo last  ',
                            font=('Helvetica', 10), bg=CARD, fg=GREY,
                            cursor='hand2', pady=6)
        undo_btn.pack(padx=14, pady=3, fill='x')
        undo_btn.bind('<Button-1>', lambda _: self._undo_last())
        undo_btn.bind('<Enter>', lambda _: undo_btn.config(bg=CARD_HOVER))
        undo_btn.bind('<Leave>', lambda _: undo_btn.config(bg=CARD))

        # Reset button
        reset_btn = tk.Label(self.left_panel, text='  Start over  ',
                             font=('Helvetica', 10), bg=RED, fg=WHITE,
                             cursor='hand2', pady=6)
        reset_btn.pack(padx=14, pady=3, fill='x')
        reset_btn.bind('<Button-1>', lambda _: self._reset())

        # Visualize button
        visualize_btn = tk.Label(self.left_panel, text='  Visualize Graph  ',
                                 font=('Helvetica', 10), bg=BLUE, fg=WHITE,
                                 cursor='hand2', pady=6)
        visualize_btn.pack(padx=14, pady=3, fill='x')
        visualize_btn.bind('<Button-1>', lambda _: visualize_course_graph(self.graph))

    def _build_navigation_right_panel(self) -> None:
        """Build the right panel that shows course info on hover."""
        tk.Label(self.right_panel, text='COURSE INFO', font=('Helvetica', 9),
                 bg=PANEL, fg=DARK_GREY).pack(pady=(14, 2), padx=14, anchor='w')
        tk.Frame(self.right_panel, bg=BORDER_COLOUR, height=1).pack(fill='x', padx=14, pady=(0, 8))

        self.info_text = tk.Text(
            self.right_panel, bg=PANEL, fg=WHITE, font=('Helvetica', 10),
            wrap='word', borderwidth=0, highlightthickness=0, padx=14, pady=4
        )
        self.info_text.pack(fill='both', expand=True)
        self.info_text.config(state='disabled')

        # Show target info by default
        self._display_course_info(self.target)

    def _refresh_course_options(self) -> None:
        """Clear and redraw the centre panel with the courses the student can pick from."""
        # Clear old widgets
        for widget in self.centre_panel.winfo_children():
            widget.destroy()

        # Check if we reached the target
        if self.target in self.completed:
            self._show_success_screen()
            return

        # Get courses the student should pick from right now
        options = get_next_needed_courses(self.graph, self.target, self.completed)

        if len(options) == 0:
            self._show_dead_end_screen()
            return

        # Header text
        tk.Label(self.centre_panel, text='Choose your next course',
                 font=('Helvetica', 12, 'bold'), bg=BACKGROUND, fg=WHITE).pack(pady=(16, 2))

        option_count = len(options)
        if option_count == 1:
            count_text = '1 option'
        else:
            count_text = str(option_count) + ' options'

        tk.Label(self.centre_panel, text=count_text,
                 font=('Helvetica', 9), bg=BACKGROUND, fg=DARK_GREY).pack(pady=(0, 12))

        # Scrollable area for the course cards
        canvas = tk.Canvas(self.centre_panel, bg=BACKGROUND, highlightthickness=0)
        scrollbar = tk.Scrollbar(self.centre_panel, orient='vertical', command=canvas.yview)
        inner_frame = tk.Frame(canvas, bg=BACKGROUND)

        inner_frame.bind('<Configure>',
                         lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        window_id = canvas.create_window((0, 0), window=inner_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)

        # Make inner frame fill the canvas width
        canvas.bind('<Configure>',
                    lambda e: canvas.itemconfig(window_id, width=e.width))

        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Mouse wheel scrolling
        canvas.bind_all('<MouseWheel>',
                        lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), 'units'))

        # Sort options: target first, then by department and level
        sorted_options = sorted(options, key=lambda code: (
            code != self.target,
            self.graph._vertices[code].department,
            self.graph._vertices[code].level,
            code
        ))

        # Draw each course card, grouped by department
        current_department = None

        for course_code in sorted_options:
            vertex = self.graph._vertices[course_code]
            is_target_course = (course_code == self.target)

            # Draw a department divider when the department changes
            if not is_target_course and vertex.department != current_department:
                current_department = vertex.department
                divider_frame = tk.Frame(inner_frame, bg=BACKGROUND)
                divider_frame.pack(fill='x', padx=24, pady=(10, 4))

                tk.Frame(divider_frame, bg=BORDER_COLOUR, height=1).pack(
                    side='left', fill='x', expand=True)
                tk.Label(divider_frame, text='  ' + current_department + '  ',
                         font=('Helvetica', 9), bg=BACKGROUND, fg=DARK_GREY).pack(side='left')
                tk.Frame(divider_frame, bg=BORDER_COLOUR, height=1).pack(
                    side='left', fill='x', expand=True)

            # Set up colours and text for this card
            if is_target_course:
                card_bg = YELLOW
                card_hover_bg = '#b8860b'
                card_text = '  *  ' + course_code + '  -  ' + vertex.name + '   TARGET'
            else:
                card_bg = CARD
                card_hover_bg = CARD_HOVER
                card_text = '  ' + course_code + '  -  ' + vertex.name

            # Create the card label
            card = tk.Label(inner_frame, text=card_text, font=('Helvetica', 11),
                            bg=card_bg, fg=WHITE, anchor='w', cursor='hand2',
                            padx=10, pady=9)
            card.pack(fill='x', padx=16, pady=2)

            # Bind click and hover events
            card.bind('<Button-1>',
                      lambda e, code=course_code: self._select_course(code))
            card.bind('<Enter>',
                      lambda e, code=course_code, label=card, hover=card_hover_bg: (
                          label.config(bg=hover), self._display_course_info(code)))
            card.bind('<Leave>',
                      lambda e, label=card, original_bg=card_bg: label.config(bg=original_bg))

    def _select_course(self, course_code: str) -> None:
        """Handle the user clicking on a course card. Add it to completed and path,
        then refresh the options.
        """
        self.completed.add(course_code)
        self.path.append(course_code)

        course = self.graph._vertices[course_code]
        for prereq in get_course_codes(course.prerequisites):
            self.graph.add_edge(prereq, course_code)
        self._refresh_path_display()
        self.completed_count_label.config(text=str(len(self.completed)) + ' completed')
        self._refresh_course_options()

    # ********************Success and dead end screens***************

    def _show_success_screen(self) -> None:
        """Show a message when the student has reached their target."""
        container = tk.Frame(self.centre_panel, bg=BACKGROUND)
        container.pack(expand=True)

        tk.Label(container, text='Done!', font=('Helvetica', 48),
                 bg=BACKGROUND, fg=GREEN).pack(pady=(0, 8))
        tk.Label(container, text='Target reached', font=('Helvetica', 16, 'bold'),
                 bg=BACKGROUND, fg=GREEN).pack()

        # Show the full path
        path_text = '  ->  '.join(self.path)
        tk.Label(container, text=path_text, font=('Courier', 10),
                 bg=CARD, fg=WHITE, padx=14, pady=10, wraplength=450).pack(pady=16)

        tk.Label(container, text=str(len(self.path)) + ' courses',
                 font=('Helvetica', 10), bg=BACKGROUND, fg=DARK_GREY).pack()

        restart_btn = tk.Label(container, text='  Start over  ',
                               font=('Helvetica', 10), bg=BLUE, fg=WHITE,
                               cursor='hand2', pady=6, padx=10)
        restart_btn.pack(pady=12)
        restart_btn.bind('<Button-1>', lambda e: self._reset())

    def _show_dead_end_screen(self) -> None:
        """Show a message when no courses are available to pick from."""
        container = tk.Frame(self.centre_panel, bg=BACKGROUND)
        container.pack(expand=True)

        tk.Label(container, text='No available courses',
                 font=('Helvetica', 12, 'bold'), bg=BACKGROUND, fg=RED).pack(pady=(0, 8))
        tk.Label(container,
                 text='Some prerequisites may reference courses\n'
                      'outside this dataset or require credit conditions.',
                 font=('Helvetica', 10), bg=BACKGROUND, fg=GREY,
                 justify='center').pack(pady=8)

        button_row = tk.Frame(container, bg=BACKGROUND)
        button_row.pack(pady=8)

        undo_btn = tk.Label(button_row, text='  Undo  ', font=('Helvetica', 10),
                            bg=CARD, fg=GREY, cursor='hand2', pady=6, padx=10)
        undo_btn.pack(side='left', padx=4)
        undo_btn.bind('<Button-1>', lambda e: self._undo_last())

        restart_btn = tk.Label(button_row, text='  Start over  ',
                               font=('Helvetica', 10), bg=RED, fg=WHITE,
                               cursor='hand2', pady=6, padx=10)
        restart_btn.pack(side='left', padx=4)
        restart_btn.bind('<Button-1>', lambda e: self._reset())

    # ************************Course info panel (right side)******************

    def _display_course_info(self, course_code: str) -> None:
        """Show information about a course in the right panel text area."""
        if course_code not in self.graph._vertices:
            return

        vertex = self.graph._vertices[course_code]

        self.info_text.config(state='normal')
        self.info_text.delete('1.0', 'end')

        # Course code and name
        self.info_text.insert('end', vertex.code + '\n', 'course_code')
        self.info_text.insert('end', vertex.name + '\n\n')

        # Basic stats line
        stats_line = str(vertex.credits) + ' cr'
        stats_line += '  |  Level ' + str(vertex.level)
        stats_line += '  |  ' + vertex.department
        if vertex.breadth is not None:
            stats_line += '  |  Breadth ' + str(vertex.breadth)
        self.info_text.insert('end', stats_line + '\n\n', 'grey_text')

        # Prerequisites
        self.info_text.insert('end', 'Prerequisites\n', 'section_header')
        if vertex.prerequisites is None or vertex.prerequisites.items is None:
            self.info_text.insert('end', 'None\n\n')
        else:
            prereq_text = self._format_prereq_tree(vertex.prerequisites, 0)
            self.info_text.insert('end', prereq_text + '\n')

        # Exclusions
        if vertex.exclusions is not None:
            self.info_text.insert('end', 'Exclusions\n', 'section_header')
            if isinstance(vertex.exclusions, str):
                exclusion_text = vertex.exclusions
            else:
                exclusion_text = ', '.join(vertex.exclusions)
            self.info_text.insert('end', exclusion_text + '\n\n', 'grey_text')

        # Description
        if vertex.description is not None:
            self.info_text.insert('end', 'Description\n', 'section_header')
            self.info_text.insert('end', vertex.description + '\n')

        # Apply text styling
        self.info_text.tag_config('course_code', font=('Courier', 11), foreground=YELLOW)
        self.info_text.tag_config('grey_text', foreground=GREY)
        self.info_text.tag_config('section_header', font=('Helvetica', 10, 'bold'),
                                  foreground=BLUE)

        self.info_text.config(state='disabled')

    def _format_prereq_tree(self, boolean_list: BooleanList, depth: int) -> str:
        """Return a formatted string showing the prerequisite tree. Completed courses
        are marked with a checkmark.
        """
        if boolean_list.items is None:
            return '  ' * depth + 'None\n'

        indent = '  ' * depth

        if boolean_list.operator == 'AND':
            header_text = 'ALL of:'
        else:
            header_text = 'ONE of:'

        result_so_far = indent + header_text + '\n'

        for item in boolean_list.items:
            if isinstance(item, str):
                # Course code - show checkmark if completed
                if item in self.completed:
                    mark = 'v'
                else:
                    mark = 'o'
                result_so_far += indent + '  ' + mark + ' ' + item + '\n'

            elif isinstance(item, BooleanList):
                # Nested boolean list - recurse
                result_so_far += self._format_prereq_tree(item, depth + 1)

            elif isinstance(item, CreditCondition):
                # Credit requirement
                if item.department is not None:
                    dept_text = item.department
                else:
                    dept_text = 'any'
                result_so_far += indent + '  * ' + str(item.amount_credits) + ' credits in ' + dept_text + '\n'

        return result_so_far

    # ************************Search dropdowns*********************************

    def _on_completed_search_typed(self, *args: object) -> None:
        """Called every time the user types in the completed courses search bar.
        Updates the dropdown with matching results.
        """
        query = self.search_var.get().strip()
        self._show_search_results(query, self.completed_search_dropdown,
                                  self._add_completed_course)

    def _on_target_search_typed(self, *args: object) -> None:
        """Called every time the user types in the target course search bar.
        Updates the dropdown with matching results.
        """
        query = self.target_var.get().strip()
        self._show_search_results(query, self.target_search_dropdown,
                                  self._pick_target_from_dropdown)

    def _show_search_results(self, query: str, dropdown_frame: tk.Frame,
                              on_click_action: callable) -> None:
        """Show search results in the given dropdown frame. When a result is clicked,
        on_click_action is called with the course code.
        """
        # Clear previous results
        for widget in dropdown_frame.winfo_children():
            widget.destroy()

        # Need at least 2 characters to search
        if len(query) < 2:
            return

        matching_courses = search_courses(self.graph, query)
        # Only show first 8 to keep it manageable
        results_to_show = matching_courses[:8]

        for course_code in results_to_show:
            course_name = self.graph._vertices[course_code].name
            display_text = ' ' + course_code + '  -  ' + course_name

            result_label = tk.Label(dropdown_frame, text=display_text,
                                    font=('Helvetica', 9), bg=CARD, fg=GREY,
                                    anchor='w', padx=8, pady=3, cursor='hand2')
            result_label.pack(fill='x')

            # When clicked, run the action with this course code
            result_label.bind('<Button-1>',
                              lambda e, code=course_code: on_click_action(code))

            # Hover effect
            result_label.bind('<Enter>',
                              lambda e, label=result_label: label.config(bg=CARD_HOVER, fg=WHITE))
            result_label.bind('<Leave>',
                              lambda e, label=result_label: label.config(bg=CARD, fg=GREY))

    def _pick_target_from_dropdown(self, course_code: str) -> None:
        """Set the target entry field when the user clicks a search result."""
        self.target_var.set(course_code)
        # Clear the dropdown
        for widget in self.target_search_dropdown.winfo_children():
            widget.destroy()

    # *******************Adding and removing completed courses***********************

    def _add_completed_from_entry(self) -> None:
        """Try to add whatever the user typed in the search bar as a completed course."""
        typed_code = self.search_var.get().strip().upper()
        if typed_code != '':
            self._add_completed_course(typed_code)

    def _add_completed_course(self, course_code: str) -> None:
        """Add a course to the completed set if it exists in the graph."""
        course_code = course_code.upper().strip()

        if course_code not in self.graph._vertices:
            messagebox.showwarning('Not found',
                                   '"' + course_code + '" is not in the course graph.')
            return

        # Don't add duplicates
        if course_code in self.completed:
            return

        self.completed.add(course_code)
        self.completed_listbox.insert('end', ' ' + course_code)
        
        if course_code not in self.graph.get_all_course_codes():
            self.graph.add_vertex(course_code)

        # Clear the search field and dropdown
        self.search_var.set('')
        for widget in self.completed_search_dropdown.winfo_children():
            widget.destroy()

    def _remove_completed_course(self) -> None:
        """Remove the currently selected course from the completed list."""
        selection = self.completed_listbox.curselection()
        if len(selection) == 0:
            return

        selected_index = selection[0]
        selected_code = self.completed_listbox.get(selected_index).strip()
        self.completed.discard(selected_code)
        self.completed_listbox.delete(selected_index)

    # ************************************Path display********************

    def _refresh_path_display(self) -> None:
        """Redraw the list of courses the user has picked so far in the left panel."""
        if not hasattr(self, 'path_frame'):
            return

        # Clear old path labels
        for widget in self.path_frame.winfo_children():
            widget.destroy()

        if len(self.path) == 0:
            tk.Label(self.path_frame, text='No courses yet',
                     font=('Helvetica', 9), bg=PANEL, fg=DARK_GREY).pack(anchor='w')
            return

        for i in range(len(self.path)):
            course_code = self.path[i]

            # Colour the target course differently
            if course_code == self.target:
                text_colour = YELLOW
            else:
                text_colour = GREEN

            step_text = str(i + 1) + '.  ' + course_code
            tk.Label(self.path_frame, text=step_text, font=('Courier', 10),
                     bg=PANEL, fg=text_colour).pack(anchor='w', pady=1)

    # ****************************************Undo and reset*************************

    def _undo_last(self) -> None:
        """Remove the last selected course and go back one step."""
        if len(self.path) == 0:
            return

        last_course = self.path.pop()
        self.completed.discard(last_course)

        self._refresh_path_display()
        self.completed_count_label.config(text=str(len(self.completed)) + ' completed')
        self._refresh_course_options()

    def _reset(self) -> None:
        """Go back to the setup screen with everything cleared."""
        self.completed = set()
        self.target = None
        self.path = []
        self.phase = 'setup'
        self._show_setup()

    # *******************************Utility****************************************

    def _clear_all_panels(self) -> None:
        """Remove all widgets from the three main panels."""
        for panel in [self.left_panel, self.centre_panel, self.right_panel]:
            for widget in panel.winfo_children():
                widget.destroy()


def run(json_file: str = 'data/courses_formatted_3.json') -> None:
    """Load the course graph and launch the interface."""
    graph = load_graph_from_json(json_file)
    CourseNavigator(graph)


if __name__ == '__main__':
    run()
