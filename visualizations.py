import networkx as nx
from plotly.graph_objs import Scatter, Figure

import algorithms
from algorithms import get_course_codes
from course_graph import CourseGraph, _CourseVertex
from boolean_list import BooleanList

# Colours to use when visualizing different clusters.
COLOUR_SCHEME = [
    '#2E91E5', '#E15F99', '#1CA71C', '#FB0D0D', '#DA16FF', '#222A2A', '#B68100',
    '#750D86', '#EB663B', '#511CFB', '#00A08B', '#FB00D1', '#FC0080', '#B2828D',
    '#6C7C32', '#778AAE', '#862A16', '#A777F1', '#620042', '#1616A7', '#DA60CA',
    '#6C4516', '#0D2A63', '#AF0038'
]

LINE_COLOUR = 'rgb(210,210,210)'
VERTEX_BORDER_COLOUR = 'rgb(50, 50, 50)'
COLOUR = 'rgb(89, 205, 100)'


def visualize_course_graph(graph: CourseGraph, output_file: str = '') -> None:
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
                     line=dict(color=LINE_COLOUR, width=1),
                     hoverinfo='none',
                     )
    trace4 = Scatter(x=x_values,
                     y=y_values,
                     mode='markers+text',
                     name='nodes',
                     marker=dict(symbol='circle-dot',
                                 size=15,
                                 color=COLOUR,
                                 line=dict(color=VERTEX_BORDER_COLOUR, width=0.5)
                                 ),
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
    """Return a dictionary mapping each course to its depth in the digraph."""

    depths = {node: 0 for node in digraph.nodes}
    for node in nx.topological_sort(digraph):
        predecessors = list(digraph.predecessors(node))
        if not predecessors:
            continue
        depths[node] = max([depths[pred] for pred in predecessors]) + 1
    return depths

def hierarchical_layout(digraph: nx.DiGraph) -> dict[str, int]:
    """Return the position of each course in a digraph taking into account the number of prerequisites."""
    depths = get_depths(digraph)
    pos = {}

    by_depth = {}
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
    from course_graph import CourseGraph
    g = CourseGraph()
    v1 = _CourseVertex('CSC108H1', 'Intro to Programming', None, None, None, None, None)
    v2 = _CourseVertex('CSC148H1', 'Intro to Computer Science', None, None, None, BooleanList('AND', ['CSC108H1']), None)
    v3 = _CourseVertex('CSC207H1', 'Software Design', None, None, None, BooleanList('AND', ['CSC148H1']), None)
    g.add_vertex(v1)
    g.add_vertex(v2)
    g.add_vertex(v3)
    g.add_edge('CSC108H1', 'CSC148H1')
    g.add_edge('CSC148H1', 'CSC207H1')

    visualize_course_graph(g)
