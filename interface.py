"""Interactive course pathway navigator.

This module provides a Tkinter-based graphical interface that allows a student
to build a personalized course pathway toward a target course. The student
selects completed courses and a target, then chooses courses layer by layer
from the set of currently eligible and relevant options until the target is
reached.

This module is Copyright (c) 2026.
"""
from __future__ import annotations
import tkinter as tk
from tkinter import messagebox
from course_graph import CourseGraph
from algorithms import get_next_needed_courses, search_courses
from json_to_graph import load_graph_from_json
from boolean_list import BooleanList, CreditCondition


# ─── Colour Palette ──────────────────────────────────────────────────────────
BG = '#0d1117'
PANEL_BG = '#161b22'
CARD_BG = '#21262d'
CARD_HOVER = '#30363d'
ACCENT = '#1f6feb'
SUCCESS = '#3fb950'
TEXT = '#e6edf3'
TEXT_SEC = '#8b949e'
TEXT_DIM = '#484f58'
TARGET_CLR = '#d29922'
BORDER = '#30363d'
DANGER = '#f85149'


# ─── Fonts ────────────────────────────────────────────────────────────────────
FONT_TITLE = ('Helvetica Neue', 16, 'bold')
FONT_HEADING = ('Helvetica Neue', 12, 'bold')
FONT_BODY = ('Helvetica Neue', 11)
FONT_SMALL = ('Helvetica Neue', 10)
FONT_TINY = ('Helvetica Neue', 9)
FONT_CODE = ('SF Mono', 11)
FONT_CODE_SMALL = ('SF Mono', 10)


class CourseNavigator:
    """The main application class that manages the Tkinter interface and
    the state of the course pathway navigation.

    Instance Attributes:
        - graph: the CourseGraph containing all course data
        - completed: the set of course codes the student has marked as completed
        - target: the current target course code, or None if not yet set
        - path: the ordered list of courses the student has selected layer by layer
        - phase: the current phase of the interface, either 'setup' or 'navigate'
    """
    graph: CourseGraph
    completed: set[str]
    target: str | None
    path: list[str]
    phase: str

    def __init__(self, graph: CourseGraph) -> None:
        """Initialize the navigator with the given CourseGraph and launch the interface."""
        self.graph = graph
        self.completed = set()
        self.target = None
        self.path = []
        self.phase = 'setup'

        self.root = tk.Tk()
        self.root.title('Course Pathway Navigator')
        self.root.geometry('1100x720')
        self.root.configure(bg=BG)
        self.root.minsize(900, 550)

        self._build_layout()
        self._show_setup_phase()
        self.root.mainloop()

    # ─── Layout ──────────────────────────────────────────────────────────

    def _build_layout(self) -> None:
        """Build the top-level layout frames: header, left panel, centre panel, right panel."""
        self.header = tk.Frame(self.root, bg=PANEL_BG, height=48)
        self.header.pack(fill='x')
        self.header.pack_propagate(False)

        tk.Label(self.header, text='Course Pathway Navigator',
                 font=FONT_TITLE, bg=PANEL_BG, fg=TEXT).pack(side='left', padx=16)

        self.header_status = tk.Label(self.header, text='',
                                      font=FONT_SMALL, bg=PANEL_BG, fg=TEXT_SEC)
        self.header_status.pack(side='right', padx=16)

        tk.Frame(self.root, bg=ACCENT, height=1).pack(fill='x')

        self.main = tk.Frame(self.root, bg=BG)
        self.main.pack(fill='both', expand=True)

        self.left_panel = tk.Frame(self.main, bg=PANEL_BG, width=260)
        self.left_panel.pack(side='left', fill='y')
        self.left_panel.pack_propagate(False)

        self.centre_panel = tk.Frame(self.main, bg=BG)
        self.centre_panel.pack(side='left', fill='both', expand=True)

        self.right_panel = tk.Frame(self.main, bg=PANEL_BG, width=280)
        self.right_panel.pack(side='right', fill='y')
        self.right_panel.pack_propagate(False)

    # ─── Setup Phase ─────────────────────────────────────────────────────

    def _show_setup_phase(self) -> None:
        """Display the setup phase where the user inputs completed courses and a target."""
        self.phase = 'setup'
        self.header_status.config(text='Setup')
        self._clear_panels()

        # Left: completed courses list
        self._section_header(self.left_panel, 'Completed Courses')

        self.completed_listbox = tk.Listbox(
            self.left_panel, bg=CARD_BG, fg=TEXT, font=FONT_CODE_SMALL,
            selectbackground=ACCENT, selectforeground=TEXT,
            borderwidth=0, highlightthickness=0, relief='flat')
        self.completed_listbox.pack(fill='both', expand=True, padx=12, pady=(0, 8))

        self._make_label_btn(self.left_panel, 'Remove selected', DANGER,
                             self._remove_completed_course)

        # Centre: inputs
        centre = tk.Frame(self.centre_panel, bg=BG)
        centre.pack(expand=True)

        # Completed courses search
        tk.Label(centre, text='Add completed courses',
                 font=FONT_HEADING, bg=BG, fg=TEXT).pack(pady=(0, 4))
        tk.Label(centre, text='Search by code or name',
                 font=FONT_TINY, bg=BG, fg=TEXT_DIM).pack()

        row1 = tk.Frame(centre, bg=BG)
        row1.pack(pady=(6, 0))
        self.search_var = tk.StringVar()
        self.search_var.trace_add('write', self._on_search_changed)
        self.search_entry = tk.Entry(
            row1, textvariable=self.search_var, font=FONT_BODY, width=28,
            bg=CARD_BG, fg=TEXT, insertbackground=TEXT,
            borderwidth=0, highlightthickness=1, highlightcolor=ACCENT,
            highlightbackground=BORDER)
        self.search_entry.pack(side='left', ipady=5, padx=(0, 6))
        self._make_label_btn(row1, 'Add', SUCCESS,
                             self._add_completed_from_search, side='left')

        self.search_results_frame = tk.Frame(centre, bg=CARD_BG)
        self.search_results_frame.pack(fill='x', padx=60, pady=(0, 4))

        # Divider
        tk.Frame(centre, bg=BORDER, height=1).pack(fill='x', padx=50, pady=16)

        # Target course search
        tk.Label(centre, text='Set target course',
                 font=FONT_HEADING, bg=BG, fg=TEXT).pack(pady=(0, 4))
        tk.Label(centre, text='The course you want to reach',
                 font=FONT_TINY, bg=BG, fg=TEXT_DIM).pack()

        row2 = tk.Frame(centre, bg=BG)
        row2.pack(pady=(6, 0))
        self.target_var = tk.StringVar()
        self.target_var.trace_add('write', self._on_target_search_changed)
        self.target_entry = tk.Entry(
            row2, textvariable=self.target_var, font=FONT_BODY, width=28,
            bg=CARD_BG, fg=TEXT, insertbackground=TEXT,
            borderwidth=0, highlightthickness=1, highlightcolor=TARGET_CLR,
            highlightbackground=BORDER)
        self.target_entry.pack(side='left', ipady=5, padx=(0, 6))

        self.target_results_frame = tk.Frame(centre, bg=CARD_BG)
        self.target_results_frame.pack(fill='x', padx=60, pady=(0, 4))

        # Divider
        tk.Frame(centre, bg=BORDER, height=1).pack(fill='x', padx=50, pady=16)

        # Start
        self._make_label_btn(centre, 'Start navigating  \u2192', ACCENT,
                             self._start_navigation)

        # Right: instructions
        self._section_header(self.right_panel, 'How it works')
        steps = [
            '1  Add courses you\'ve completed.',
            '2  Type your target course.',
            '3  Click Start.',
            '4  Pick courses layer by layer.',
            '5  Repeat until you reach your target.',
        ]
        for s in steps:
            tk.Label(self.right_panel, text=s, font=FONT_SMALL, bg=PANEL_BG,
                     fg=TEXT_SEC, wraplength=240, justify='left',
                     anchor='w').pack(padx=14, pady=2, anchor='w')

    # ─── Navigation Phase ────────────────────────────────────────────────

    def _start_navigation(self) -> None:
        """Validate inputs and transition to navigation phase."""
        code = self.target_var.get().strip().upper()
        if not code:
            messagebox.showwarning('Missing target', 'Enter a target course code.')
            return
        if code not in self.graph._vertices:
            messagebox.showerror('Invalid course', f'"{code}" not found.')
            return
        if code in self.completed:
            messagebox.showinfo('Done', f'You already completed {code}.')
            return

        self.target = code
        self.path = []
        self.phase = 'navigate'
        self.header_status.config(text=f'Target: {self.target}')
        self._show_navigation_phase()

    def _show_navigation_phase(self) -> None:
        """Display the navigation phase."""
        self._clear_panels()
        self._build_left_nav()
        self._build_right_info()
        self._update_eligible_display()

    def _build_left_nav(self) -> None:
        """Build left sidebar for navigation."""
        tk.Label(self.left_panel, text='TARGET', font=FONT_TINY,
                 bg=PANEL_BG, fg=TEXT_DIM).pack(pady=(14, 0), padx=14, anchor='w')
        tk.Label(self.left_panel, text=self.target, font=FONT_CODE,
                 bg=PANEL_BG, fg=TARGET_CLR).pack(padx=14, anchor='w')

        tk.Frame(self.left_panel, bg=BORDER, height=1).pack(
            fill='x', padx=14, pady=10)

        tk.Label(self.left_panel, text='YOUR PATH', font=FONT_TINY,
                 bg=PANEL_BG, fg=TEXT_DIM).pack(padx=14, anchor='w')

        self.path_frame = tk.Frame(self.left_panel, bg=PANEL_BG)
        self.path_frame.pack(fill='both', expand=True, padx=14, pady=(4, 0))
        self._update_path_display()

        tk.Frame(self.left_panel, bg=BORDER, height=1).pack(
            fill='x', padx=14, pady=8)

        self.completed_label = tk.Label(
            self.left_panel, text=f'{len(self.completed)} completed',
            font=FONT_TINY, bg=PANEL_BG, fg=TEXT_DIM)
        self.completed_label.pack(padx=14, anchor='w', pady=(0, 8))

        self._make_label_btn(self.left_panel, 'Undo last', CARD_BG,
                             self._undo_last, fg=TEXT_SEC)
        self._make_label_btn(self.left_panel, 'Start over', DANGER, self._reset)
        tk.Frame(self.left_panel, bg=PANEL_BG, height=8).pack()

    def _build_right_info(self) -> None:
        """Build the right panel for course details."""
        self._section_header(self.right_panel, 'Course info')

        self.info_text = tk.Text(
            self.right_panel, bg=PANEL_BG, fg=TEXT, font=FONT_SMALL,
            wrap='word', borderwidth=0, highlightthickness=0, padx=14, pady=4)
        self.info_text.pack(fill='both', expand=True)
        self.info_text.config(state='disabled')
        self._show_course_info(self.target)

    # ─── Eligible Display ────────────────────────────────────────────────

    def _update_eligible_display(self) -> None:
        """Refresh centre panel with current layer of eligible courses."""
        for w in self.centre_panel.winfo_children():
            w.destroy()

        if self.target in self.completed:
            self._show_success()
            return

        eligible = get_next_needed_courses(self.graph, self.target, self.completed)
        if not eligible:
            self._show_dead_end()
            return

        tk.Label(self.centre_panel, text='Choose your next course',
                 font=FONT_HEADING, bg=BG, fg=TEXT).pack(pady=(16, 2))
        n = len(eligible)
        tk.Label(self.centre_panel,
                 text=f'{n} option{"s" if n != 1 else ""}',
                 font=FONT_TINY, bg=BG, fg=TEXT_DIM).pack(pady=(0, 12))

        canvas = tk.Canvas(self.centre_panel, bg=BG, highlightthickness=0)
        vsb = tk.Scrollbar(self.centre_panel, orient='vertical', command=canvas.yview)
        inner = tk.Frame(canvas, bg=BG)

        inner.bind('<Configure>',
                   lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        cw = canvas.create_window((0, 0), window=inner, anchor='nw')
        canvas.configure(yscrollcommand=vsb.set)
        canvas.bind('<Configure>', lambda e: canvas.itemconfig(cw, width=e.width))

        canvas.pack(side='left', fill='both', expand=True)
        vsb.pack(side='right', fill='y')

        canvas.bind_all('<MouseWheel>',
                        lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), 'units'))

        sorted_eligible = sorted(eligible, key=lambda c: (
            c != self.target,
            self.graph._vertices[c].department,
            self.graph._vertices[c].level, c))

        cur_dept = None
        for code in sorted_eligible:
            v = self.graph._vertices[code]
            is_t = code == self.target

            if not is_t and v.department != cur_dept:
                cur_dept = v.department
                div = tk.Frame(inner, bg=BG)
                div.pack(fill='x', padx=24, pady=(10, 4))
                tk.Frame(div, bg=BORDER, height=1).pack(
                    side='left', fill='x', expand=True)
                tk.Label(div, text=f'  {cur_dept}  ', font=FONT_TINY,
                         bg=BG, fg=TEXT_DIM).pack(side='left')
                tk.Frame(div, bg=BORDER, height=1).pack(
                    side='left', fill='x', expand=True)

            bg = TARGET_CLR if is_t else CARD_BG
            hov = '#b8860b' if is_t else CARD_HOVER
            pre = '\u2605  ' if is_t else ''
            suf = '   TARGET' if is_t else ''

            lbl = tk.Label(inner, text=f'  {pre}{code}  \u2014  {v.name}{suf}',
                           font=FONT_BODY, bg=bg, fg=TEXT, anchor='w',
                           cursor='hand2', padx=10, pady=9)
            lbl.pack(fill='x', padx=16, pady=2)

            lbl.bind('<Button-1>', lambda e, c=code: self._on_course_selected(c))
            lbl.bind('<Enter>', lambda e, c=code, l=lbl, h=hov: (
                l.config(bg=h), self._show_course_info(c)))
            lbl.bind('<Leave>', lambda e, l=lbl, b=bg: l.config(bg=b))

    def _on_course_selected(self, course: str) -> None:
        """Handle user clicking a course."""
        self.completed.add(course)
        self.path.append(course)
        self._update_path_display()
        self.completed_label.config(text=f'{len(self.completed)} completed')
        self._update_eligible_display()

    def _show_success(self) -> None:
        """Display success when target is reached."""
        f = tk.Frame(self.centre_panel, bg=BG)
        f.pack(expand=True)

        tk.Label(f, text='\u2713', font=('Helvetica Neue', 48),
                 bg=BG, fg=SUCCESS).pack(pady=(0, 8))
        tk.Label(f, text='Target reached', font=FONT_TITLE,
                 bg=BG, fg=SUCCESS).pack()

        path_str = '  \u2192  '.join(self.path)
        tk.Label(f, text=path_str, font=FONT_CODE_SMALL, bg=CARD_BG, fg=TEXT,
                 padx=14, pady=10, wraplength=450).pack(pady=16)
        tk.Label(f, text=f'{len(self.path)} courses', font=FONT_SMALL,
                 bg=BG, fg=TEXT_DIM).pack()

        self._make_label_btn(f, 'Start over', ACCENT, self._reset)

    def _show_dead_end(self) -> None:
        """Display dead-end message."""
        f = tk.Frame(self.centre_panel, bg=BG)
        f.pack(expand=True)

        tk.Label(f, text='No available courses', font=FONT_HEADING,
                 bg=BG, fg=DANGER).pack(pady=(0, 8))
        tk.Label(f, text='Some prerequisites may reference courses\n'
                         'outside this dataset or require credit conditions.',
                 font=FONT_SMALL, bg=BG, fg=TEXT_SEC, justify='center').pack(pady=8)

        row = tk.Frame(f, bg=BG)
        row.pack(pady=8)
        self._make_label_btn(row, 'Undo', CARD_BG, self._undo_last,
                             side='left', fg=TEXT_SEC)
        tk.Frame(row, bg=BG, width=8).pack(side='left')
        self._make_label_btn(row, 'Start over', DANGER, self._reset, side='left')

    # ─── Course Info ─────────────────────────────────────────────────────

    def _show_course_info(self, code: str) -> None:
        """Show course details in right panel."""
        if code not in self.graph._vertices:
            return

        v = self.graph._vertices[code]
        t = self.info_text
        t.config(state='normal')
        t.delete('1.0', 'end')

        t.insert('end', f'{v.code}\n', 'code')
        t.insert('end', f'{v.name}\n\n', 'name')

        details = f'{v.credits} cr  \u00b7  Level {v.level}  \u00b7  {v.department}'
        if v.breadth:
            details += f'  \u00b7  Breadth {v.breadth}'
        t.insert('end', details + '\n\n', 'dim')

        t.insert('end', 'Prerequisites\n', 'heading')
        if v.prerequisites is None or v.prerequisites.items is None:
            t.insert('end', 'None\n\n')
        else:
            t.insert('end', self._format_boolean_list(v.prerequisites) + '\n')

        if v.exclusions:
            t.insert('end', 'Exclusions\n', 'heading')
            exc = v.exclusions if isinstance(v.exclusions, str) else ', '.join(
                v.exclusions)
            t.insert('end', exc + '\n\n', 'dim')

        if v.description:
            t.insert('end', 'Description\n', 'heading')
            t.insert('end', v.description + '\n')

        t.tag_config('code', font=FONT_CODE, foreground=TARGET_CLR)
        t.tag_config('name', font=FONT_BODY, foreground=TEXT)
        t.tag_config('dim', foreground=TEXT_SEC)
        t.tag_config('heading', font=('Helvetica Neue', 10, 'bold'),
                     foreground=ACCENT)
        t.config(state='disabled')

    def _format_boolean_list(self, bl: BooleanList, indent: int = 0) -> str:
        """Format a BooleanList as a readable indented string."""
        if bl.items is None:
            return '  ' * indent + 'None\n'

        pre = '  ' * indent
        op = 'ALL of:' if bl.operator == 'AND' else 'ONE of:'
        out = f'{pre}{op}\n'

        for item in bl.items:
            if isinstance(item, str):
                mark = '\u2713' if item in self.completed else '\u25cb'
                out += f'{pre}  {mark} {item}\n'
            elif isinstance(item, BooleanList):
                out += self._format_boolean_list(item, indent + 1)
            elif isinstance(item, CreditCondition):
                dept = item.department or 'any'
                out += f'{pre}  \u25cf {item.amount_credits} credits in {dept}\n'
        return out

    # ─── Search ──────────────────────────────────────────────────────────

    def _on_search_changed(self, *args: object) -> None:
        """Handle typing in the completed-courses search bar."""
        self._populate_search_dropdown(
            self.search_var.get().strip(),
            self.search_results_frame,
            self._add_completed_course)

    def _on_target_search_changed(self, *args: object) -> None:
        """Handle typing in the target course search bar."""
        self._populate_search_dropdown(
            self.target_var.get().strip(),
            self.target_results_frame,
            self._set_target_from_search)

    def _populate_search_dropdown(self, query: str, frame: tk.Frame,
                                   on_click: callable) -> None:
        """Fill a dropdown frame with search results."""
        for w in frame.winfo_children():
            w.destroy()
        if len(query) < 2:
            return

        results = search_courses(self.graph, query)[:8]
        for code in results:
            name = self.graph._vertices[code].name
            lbl = tk.Label(frame, text=f' {code}  \u2014  {name}', font=FONT_TINY,
                           bg=CARD_BG, fg=TEXT_SEC, anchor='w',
                           padx=8, pady=3, cursor='hand2')
            lbl.pack(fill='x')
            lbl.bind('<Button-1>', lambda e, c=code: on_click(c))
            lbl.bind('<Enter>', lambda e, l=lbl: l.config(bg=CARD_HOVER, fg=TEXT))
            lbl.bind('<Leave>', lambda e, l=lbl: l.config(bg=CARD_BG, fg=TEXT_SEC))

    def _set_target_from_search(self, code: str) -> None:
        """Set the target entry from a search result click."""
        self.target_var.set(code)
        for w in self.target_results_frame.winfo_children():
            w.destroy()

    def _add_completed_from_search(self) -> None:
        """Add course from search entry text."""
        code = self.search_var.get().strip().upper()
        if code:
            self._add_completed_course(code)

    def _add_completed_course(self, code: str) -> None:
        """Validate and add a course to completed set."""
        code = code.upper().strip()
        if code not in self.graph._vertices:
            messagebox.showwarning('Not found', f'"{code}" not in the course graph.')
            return
        if code in self.completed:
            return
        self.completed.add(code)
        self.completed_listbox.insert('end', f' {code}')
        self.search_var.set('')
        for w in self.search_results_frame.winfo_children():
            w.destroy()

    def _remove_completed_course(self) -> None:
        """Remove selected course from completed set."""
        sel = self.completed_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        code = self.completed_listbox.get(idx).strip()
        self.completed.discard(code)
        self.completed_listbox.delete(idx)

    # ─── Path Display ────────────────────────────────────────────────────

    def _update_path_display(self) -> None:
        """Refresh the path display in the left panel."""
        if not hasattr(self, 'path_frame'):
            return
        for w in self.path_frame.winfo_children():
            w.destroy()
        if not self.path:
            tk.Label(self.path_frame, text='No courses yet',
                     font=FONT_TINY, bg=PANEL_BG, fg=TEXT_DIM).pack(anchor='w')
            return
        for i, code in enumerate(self.path):
            fg = TARGET_CLR if code == self.target else SUCCESS
            tk.Label(self.path_frame, text=f'{i + 1}.  {code}',
                     font=FONT_CODE_SMALL, bg=PANEL_BG, fg=fg).pack(
                anchor='w', pady=1)

    # ─── Undo & Reset ────────────────────────────────────────────────────

    def _undo_last(self) -> None:
        """Undo the last course selection."""
        if not self.path:
            return
        last = self.path.pop()
        self.completed.discard(last)
        self._update_path_display()
        self.completed_label.config(text=f'{len(self.completed)} completed')
        self._update_eligible_display()

    def _reset(self) -> None:
        """Reset everything back to setup."""
        self.completed = set()
        self.target = None
        self.path = []
        self.phase = 'setup'
        self._show_setup_phase()

    # ─── Helpers ─────────────────────────────────────────────────────────

    def _clear_panels(self) -> None:
        """Clear all three panels."""
        for p in [self.left_panel, self.centre_panel, self.right_panel]:
            for w in p.winfo_children():
                w.destroy()

    def _section_header(self, parent: tk.Frame, text: str) -> None:
        """Add a section header to a panel."""
        tk.Label(parent, text=text.upper(), font=FONT_TINY,
                 bg=PANEL_BG, fg=TEXT_DIM).pack(pady=(14, 2), padx=14, anchor='w')
        tk.Frame(parent, bg=BORDER, height=1).pack(fill='x', padx=14, pady=(0, 8))

    def _make_label_btn(self, parent: tk.Frame, text: str, bg_color: str,
                        command: callable, side: str = 'top',
                        fg: str = TEXT) -> None:
        """Create a clickable label styled as a button (macOS compatible)."""
        lbl = tk.Label(parent, text=f'  {text}  ', font=FONT_SMALL,
                       bg=bg_color, fg=fg, cursor='hand2', pady=6, padx=10)
        lbl.pack(padx=14, pady=3, fill='x' if side == 'top' else None, side=side)
        lbl.bind('<Button-1>', lambda e: command())
        hover = CARD_HOVER if bg_color == CARD_BG else bg_color
        lbl.bind('<Enter>', lambda e, l=lbl: l.config(bg=hover))
        lbl.bind('<Leave>', lambda e, l=lbl, b=bg_color: l.config(bg=b))


# ─── Entry Point ─────────────────────────────────────────────────────────────

def run(json_file: str = 'data/courses_formatted_3.json') -> None:
    """Load the course graph from the given JSON file and launch the navigator interface.

    Preconditions:
        - json_file exists and is valid JSON formatted according to project standards
    """
    graph = load_graph_from_json(json_file)
    CourseNavigator(graph)


if __name__ == '__main__':
    run()
