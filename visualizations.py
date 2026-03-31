"""CSC111 Winter 2026 Project 2: Course Graph Visualizations

Module Description
==================

This module contains functions for visualizing the CourseGraph using Plotly and NetworkX.

Copyright and Usage Information
===============================

This file is Copyright (c) 2026.
"""
import networkx as nx
from plotly.graph_objs import Scatter, Figure

from course_graph import CourseGraph, _CourseVertex
from boolean_list import BooleanList

LINE_COLOUR = 'rgb(210,210,210)'
VERTEX_BORDER_COLOUR = 'rgb(50, 50, 50)'
COLOUR = 'rgb(89, 205, 100)'


def visualize_course_graph(graph: CourseGraph, output_file: str = '') -> None:
    """Display the course prerequisite graph as an interactive Plotly figure.

    If output_file is given, write the figure to that path instead of displaying it.
    """
    digraph = graph.to_networkx()

    pos = hierarchical_layout(digraph)

    x_values = [pos[k][0] for k in digraph.nodes]
    y_values = [pos[k][1] for k in digraph.nodes]
    labels = list(digraph.nodes)

    x_edges = []
    y_edges = []
    for edge in digraph.edges:
        x_edges += [pos[edge[0]][0], pos[edge[1]][0], None]
        y_edges += [pos[edge[0]][1], pos[edge[1]][1], None]

    trace3 = Scatter(x=x_edges,
                     y=y_edges,
                     mode='lines',
                     name='edges',
                     line={'color': LINE_COLOUR, 'width': 1},
                     hoverinfo='none',
                     )
    trace4 = Scatter(x=x_values,
                     y=y_values,
                     mode='markers+text',
                     name='nodes',
                     marker={'symbol': 'circle-dot',
                             'size': 15,
                             'color': COLOUR,
                             'line': {'color': VERTEX_BORDER_COLOUR, 'width': 0.5}
                             },
                     text=labels,
                     textposition='middle center',
                     hovertemplate='%{text}',
                     hoverlabel={'namelength': 0}
                     )

    data1 = [trace3, trace4]
    fig = Figure(data=data1)
    fig.update_layout({'showlegend': False})
    fig.update_xaxes(showgrid=False, zeroline=False, visible=False)
    fig.update_yaxes(showgrid=False, zeroline=False, visible=False)

    if output_file == '':
        fig.show()
    else:
        fig.write_image(output_file)


def get_depths(digraph: nx.DiGraph) -> dict[str, int]:
    """Return a dictionary mapping each node to its depth in the digraph.

    Depth is defined as the length of the longest path of predecessors leading to that node.
    """
    depths = {n: 0 for n in digraph.nodes}
    for node in nx.topological_sort(digraph):
        predecessors = list(digraph.predecessors(node))
        if not predecessors:
            continue
        depths[node] = max([depths[pred] for pred in predecessors]) + 1
    return depths


def hierarchical_layout(digraph: nx.DiGraph) -> dict[str, tuple[int, int]]:
    """Return a position dict for each node, laid out by prerequisite depth.

    Nodes at the same depth share the same vertical level.
    """
    depths = get_depths(digraph)
    pos = {}

    by_depth: dict[int, list] = {}
    for course, depth in depths.items():
        if depth not in by_depth:
            by_depth[depth] = []
        by_depth[depth].append(course)
    for depth, courses in by_depth.items():
        y = -depth
        for i, course in enumerate(courses):
            x = i * 2
            pos[course] = (x, y)
    return pos


if __name__ == '__main__':
    import doctest
    doctest.testmod()
    # import python_ta
    # python_ta.check_all(config={
    #     'extra-imports': ['networkx', 'plotly', 'plotly.graph_objs', 'course_graph', 'boolean_list'],
    #     'allowed-io': [],
    #     'max-line-length': 120
    # })

    g = CourseGraph()
    v1 = _CourseVertex('CSC108H1', 'Intro to Programming')
    v2 = _CourseVertex('CSC148H1', 'Intro to Computer Science', BooleanList('AND', ['CSC108H1']))
    v3 = _CourseVertex('CSC207H1', 'Software Design', BooleanList('AND', ['CSC148H1']))
    g.add_vertex(v1)
    g.add_vertex(v2)
    g.add_vertex(v3)
    g.add_edge('CSC108H1', 'CSC148H1')
    g.add_edge('CSC148H1', 'CSC207H1')

    visualize_course_graph(g)
