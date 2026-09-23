# netbox_physical_infra_plugin/network_map.py
"""
Builds a full infrastructure map (not just a single cable's path) starting from
one JunctionBox and walking every Conduit reachable from it.

Overview of the approach:

1. `discover_network(start_box)` does a breadth-first walk across the graph of
   JunctionBox <-> Terminal <-> Conduit <-> Terminal <-> JunctionBox, following
   every conduit it finds. A conduit that terminates on something other than a
   Terminal (a device interface, a power feed, etc.) is kept as an "external"
   leaf node rather than expanded further, since there's nothing more of *this*
   plugin's graph beyond it. This is what "propagate to other objects and build
   the most extensive net" means in practice: every JunctionBox reachable via
   any conduit, transitively, ends up in the map.

2. `compute_layout(...)` turns that graph into (col, row) grid coordinates.
   Because each Terminal already declares which side of its box it lives on
   (up/down/left/right), that side *is* the natural compass direction to place
   whatever is on the other end of the conduit: a terminal on the 'right' side
   means "the thing on the other end of this conduit belongs to my right".
   Starting from the origin box at (0, 0), we place every newly-discovered
   neighbour one grid cell in that direction, and if that cell is already
   taken we push further out along the same direction until we find a free
   one. It's a heuristic, not a general-purpose graph-layout solver, but it
   keeps the schematic readable and honors the physical side of each port,
   which is what was asked for.

3. `svg_from_layout(...)` in network_svg.py (companion module) turns the
   layout into the actual SVG, reusing the visual language of the existing
   single-cable trace (same stroke widths, fonts, colors, link-wrapped rects).
"""
from collections import deque, defaultdict

from django.contrib.contenttypes.models import ContentType

from .models import Terminal


DIRECTION_VECTORS = {
    'up': (0, -1),
    'down': (0, 1),
    'left': (-1, 0),
    'right': (1, 0),
}


def _node_key(obj):
    """Stable identity for any model instance, used for de-duplication."""
    if obj is None:
        return None
    ct = ContentType.objects.get_for_model(obj)
    return (ct.app_label, ct.model, obj.pk)


def get_terminal_sides(box):
    """Return {'up': [Terminal, ...], 'down': [...], 'left': [...], 'right': [...]}
    for a JunctionBox, each list ordered by `index` ascending.

    Per the index convention on the Terminal model: for 'up'/'down' index 1 is
    the leftmost terminal on that edge; for 'left'/'right' index 1 is the
    topmost terminal on that edge.
    """
    sides = {'up': [], 'down': [], 'left': [], 'right': []}
    for term in box.terminals.all().order_by('position', 'index'):
        sides.setdefault(term.position, []).append(term)
    return sides


def _resolve_termination(termination):
    """Split a conduit termination into (junction_box, terminal, external_obj).

    Exactly one of (junction_box/terminal) or external_obj is populated.
    """
    if termination is None:
        return None, None, None
    if isinstance(termination, Terminal):
        return termination.junction_box, termination, None
    return None, None, termination


def discover_network(start_box, max_boxes=200):
    """Breadth-first walk of every JunctionBox reachable from `start_box`.

    Returns a tuple (boxes, box_sides, edges, externals):
      boxes:      {box_pk: JunctionBox}, in discovery order
      box_sides:  {box_pk: {'up': [Terminal,...], 'down': [...], ...}}
      edges:      list of dicts, one per Conduit encountered:
                  {
                      'conduit': Conduit,
                      'a_box': JunctionBox|None, 'a_terminal': Terminal|None, 'a_external': obj|None,
                      'b_box': JunctionBox|None, 'b_terminal': Terminal|None, 'b_external': obj|None,
                  }
      externals:  {node_key: object} for every non-Terminal endpoint encountered
                  (a device interface, power feed, circuit termination, etc.)

    `max_boxes` is a safety valve against runaway/looped data.
    """
    boxes = {start_box.pk: start_box}
    box_sides = {start_box.pk: get_terminal_sides(start_box)}
    edges = []
    externals = {}
    seen_conduits = set()

    queue = deque([start_box])

    while queue:
        box = queue.popleft()
        sides = box_sides[box.pk]

        for terminal_list in sides.values():
            for term in terminal_list:
                for conduit in term.connected_conduits:
                    if conduit.pk in seen_conduits:
                        continue
                    seen_conduits.add(conduit.pk)

                    a_box, a_term, a_ext = _resolve_termination(conduit.start_termination)
                    b_box, b_term, b_ext = _resolve_termination(conduit.end_termination)

                    edges.append({
                        'conduit': conduit,
                        'a_box': a_box, 'a_terminal': a_term, 'a_external': a_ext,
                        'b_box': b_box, 'b_terminal': b_term, 'b_external': b_ext,
                    })

                    for other_box in (a_box, b_box):
                        if (
                            other_box is not None
                            and other_box.pk not in boxes
                            and len(boxes) < max_boxes
                        ):
                            boxes[other_box.pk] = other_box
                            box_sides[other_box.pk] = get_terminal_sides(other_box)
                            queue.append(other_box)

                    for other_ext in (a_ext, b_ext):
                        if other_ext is not None:
                            externals.setdefault(_node_key(other_ext), other_ext)

    return boxes, box_sides, edges, externals


def _free_cell(target, vec, occupied):
    """If `target` is already taken, keep stepping further out along `vec`
    (the same compass direction) until a free grid cell is found."""
    cell = target
    steps = 0
    while cell in occupied and steps < 100:
        steps += 1
        cell = (target[0] + vec[0] * steps, target[1] + vec[1] * steps)
    return cell


def compute_layout(boxes, box_sides, edges, start_box):
    """Assign grid (col, row) coordinates to every JunctionBox, and to every
    external leaf node, based on the compass direction implied by each
    conduit's local terminal side.

    Returns (box_coords, external_coords):
      box_coords:      {box_pk: (col, row)}
      external_coords: {node_key: (col, row, external_obj, direction_vector)}
    """
    # adjacency[box_pk] -> list of (neighbour_box_or_None, local_terminal, edge, neighbour_side)
    # `neighbour_side` ('a' or 'b') tells us which half of `edge` the neighbour
    # lives on, so that if neighbour_box is None we know whether to look at
    # edge['a_external'] or edge['b_external'] for the leaf node.
    adjacency = defaultdict(list)
    for edge in edges:
        a_box, a_term = edge['a_box'], edge['a_terminal']
        b_box, b_term = edge['b_box'], edge['b_terminal']
        if a_box is not None:
            adjacency[a_box.pk].append((b_box, a_term, edge, 'b'))
        if b_box is not None:
            adjacency[b_box.pk].append((a_box, b_term, edge, 'a'))

    box_coords = {start_box.pk: (0, 0)}
    occupied = {(0, 0): start_box.pk}
    external_coords = {}

    queue = deque([start_box.pk])
    visited_boxes = {start_box.pk}

    while queue:
        box_pk = queue.popleft()
        cur = box_coords[box_pk]

        for neighbour_box, local_term, edge, neighbour_side in adjacency[box_pk]:
            vec = DIRECTION_VECTORS.get(getattr(local_term, 'position', None), (1, 0))
            target = (cur[0] + vec[0], cur[1] + vec[1])

            if neighbour_box is not None:
                if neighbour_box.pk in visited_boxes:
                    continue
                cell = _free_cell(target, vec, occupied)
                box_coords[neighbour_box.pk] = cell
                occupied[cell] = neighbour_box.pk
                visited_boxes.add(neighbour_box.pk)
                queue.append(neighbour_box.pk)
            else:
                ext_obj = edge[f'{neighbour_side}_external']
                if ext_obj is None:
                    continue
                key = _node_key(ext_obj)
                if key in external_coords:
                    continue
                taken = dict(occupied)
                taken.update({(c, r): 1 for c, r, *_ in external_coords.values()})
                cell = _free_cell(target, vec, taken)
                external_coords[key] = (cell[0], cell[1], ext_obj, vec)

    return box_coords, external_coords
