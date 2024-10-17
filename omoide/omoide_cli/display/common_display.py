"""Common rendering code."""

from typing import Any


def prettify_graph(graph: dict[str, Any]) -> str:
    """Make human-readable representation of a graph.

    Example of graph:
        graph = {
            'upper':
            {
                'middle':
                {
                    'lower':
                    {
                        'bottom1': { 'exit': None },
                        'bottom2': { 'exit': None },
                    }
                }
            }
        }

    Example of output:
        upper
        └─middle
            └─lower
                ├─bottom1
                │   └─exit
                └─bottom2
                    └─exit
    """
    memory: list[str] = []
    _prettify_graph(graph, memory)
    return _mix(memory)


def _mix(memory: list) -> str:
    """Handle graphs."""
    indexes: list[int] = []
    for i in range(len(memory)):
        line = memory[i]
        for each in indexes:
            if line[each] == ' ':
                line = line[:each] + '│' + line[each + 1 :]
            else:
                indexes.remove(each)

        memory[i] = line

        for j, symbol in enumerate(line):
            if symbol == '├':
                indexes.append(j)

    lines = [''.join(x) for x in memory]
    return '\n'.join(lines)


def _prettify_graph(
    graph: dict,
    memory: list[str],
    depth: int = 0,
) -> None:
    """Recursively traverse graph and store lines to nodes."""
    if not graph:
        return

    for i, (key, values) in enumerate(graph.items(), start=1):
        sep = '└' if i == len(graph) else '├'

        if depth == 0:
            memory.append(key)
        else:
            memory.append((depth - 1) * ' ' * 3 + sep + '─' + key)

        _prettify_graph(values, memory, depth + 1)


def combine_graphs(full_graph: dict, actual_graph: dict) -> str:
    """Highlight route on graph.

    Example of output:
        func_1
        ╚══>func_2
            ╚══>DummyState
                ╚══>func_3
                    ├══>func_5
                    │   ╚══>func_7
                    │       └exit
                    └func_4
                        └func_6
                            └exit
    """
    memory: list[str] = []
    _prettify_combined_graph(full_graph, actual_graph, memory)
    return _mix(memory)


def _prettify_combined_graph(
    full_graph: dict,
    actual_graph: dict | None,
    memory: list[str],
    depth: int = 0,
) -> None:
    """Recursively traverse graph and store lines to nodes."""
    actual_graph = actual_graph or {}

    if not full_graph:
        return

    for i, (key, values) in enumerate(full_graph.items(), start=1):
        sep = (
            ('╚' if key in actual_graph else '└')
            if i == len(full_graph)
            else '├'
        )

        line = '══>' if key in actual_graph else ''

        if depth == 0:
            memory.append(key)
        else:
            memory.append((depth - 1) * ' ' * 4 + sep + line + key)

        _prettify_combined_graph(
            values,
            actual_graph.get(key),
            memory,
            depth + 1,
        )
