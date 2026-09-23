# netbox_physical_infra_plugin/network_svg.py
"""
Renders the graph built by network_map.discover_network()/compute_layout()
into a single SVG "infrastructure map": every JunctionBox reachable from a
starting box, drawn as a rectangle with its Terminals sticking out of the
correct edge (up/down/left/right, ordered by `index`), connected by
orthogonal lines representing Conduits. Anything a conduit terminates on that
isn't one of our Terminals (a device interface, a power feed, etc.) is drawn
as a small chassis block, same as the device blocks in the single-cable trace.

Visual language is intentionally borrowed from svg_generator.py: same font
stack, same stroke widths, same "shadowed cable line" trick, same
link-wrapped <rect>/<text> pattern so clicking an element navigates to that
object's NetBox page.
"""
from html import escape

from django.utils.safestring import mark_safe

from .network_map import discover_network, compute_layout, DIRECTION_VECTORS, _node_key as _ext_key
from .svg_generator import (
    _svg_text, _device_details, _device_role_color,
    _termination_device, _termination_url, _junction_box_details,
    DEFAULT_CABLE_COLOR,
)


# --- layout constants (pixels) -------------------------------------------
MIN_BOX_WIDTH = 170
MIN_BOX_HEIGHT = 120
HEADER_HEIGHT = 48      # room inside the box for name / site / size text
PORT_SPACING = 34       # spacing between adjacent ports on the same edge
PORT_MARGIN = 26        # inset from the box corner to the first/last port
STUB_LEN = 20           # how far a conduit line pokes out before turning
CELL_GAP_X = 170         # extra breathing room between grid columns
CELL_GAP_Y = 170         # extra breathing room between grid rows
EXTERNAL_WIDTH = 170
EXTERNAL_HEIGHT = 80
MARGIN = 40


def _box_size(sides):
    top_n = len(sides.get('up', []))
    bottom_n = len(sides.get('down', []))
    left_n = len(sides.get('left', []))
    right_n = len(sides.get('right', []))
    width = max(MIN_BOX_WIDTH, (max(top_n, bottom_n, 1) - 1) * PORT_SPACING + PORT_MARGIN * 2)
    height = max(MIN_BOX_HEIGHT, HEADER_HEIGHT + (max(left_n, right_n, 1) - 1) * PORT_SPACING + PORT_MARGIN * 2)
    return width, height


def _port_points(sides, box_x, box_y, box_w, box_h):
    """Return {terminal_pk: (edge_x, edge_y, stub_x, stub_y, dir_vec, terminal)}."""
    points = {}

    def place(term_list, axis_fixed, axis_start, axis_len, is_row, dir_vec):
        n = len(term_list)
        for i, term in enumerate(term_list):
            frac = (i + 1) / (n + 1)
            pos_along = axis_start + axis_len * frac
            if is_row:  # up/down: pos_along is x, axis_fixed is y
                ex, ey = pos_along, axis_fixed
            else:       # left/right: pos_along is y, axis_fixed is x
                ex, ey = axis_fixed, pos_along
            sx, sy = ex + dir_vec[0] * STUB_LEN, ey + dir_vec[1] * STUB_LEN
            points[term.pk] = (ex, ey, sx, sy, dir_vec, term)

    place(sides.get('up', []), box_y, box_x, box_w, True, DIRECTION_VECTORS['up'])
    place(sides.get('down', []), box_y + box_h, box_x, box_w, True, DIRECTION_VECTORS['down'])
    place(sides.get('left', []), box_x, box_y, box_h, False, DIRECTION_VECTORS['left'])
    place(sides.get('right', []), box_x + box_w, box_y, box_h, False, DIRECTION_VECTORS['right'])
    return points


def _route_orthogonal(p0, d0, p1, d1):
    """Build a polyline of points from p0 (leaving in direction d0) to p1
    (leaving in direction d1, i.e. the path arrives from that side)."""
    sx, sy = p0[0] + d0[0] * STUB_LEN, p0[1] + d0[1] * STUB_LEN
    ex, ey = p1[0] + d1[0] * STUB_LEN, p1[1] + d1[1] * STUB_LEN

    horiz0 = d0[0] != 0
    horiz1 = d1[0] != 0

    points = [p0, (sx, sy)]
    if horiz0 and horiz1:
        midx = (sx + ex) / 2
        points += [(midx, sy), (midx, ey)]
    elif (not horiz0) and (not horiz1):
        midy = (sy + ey) / 2
        points += [(sx, midy), (ex, midy)]
    elif horiz0 and not horiz1:
        points += [(ex, sy)]
    else:
        points += [(sx, ey)]
    points += [(ex, ey), p1]
    return points


def _fmt_points(points):
    return ' '.join(f'{x:.1f},{y:.1f}' for x, y in points)


def generate_infrastructure_map_svg(start_box):
    """Generate the full infrastructure map SVG starting from `start_box`,
    following every conduit reachable from it, transitively, across every
    JunctionBox it touches."""
    boxes, box_sides, edges, externals = discover_network(start_box)
    box_coords, external_coords = compute_layout(boxes, box_sides, edges, start_box)

    # --- box pixel sizes & cell size -------------------------------------
    box_sizes = {pk: _box_size(box_sides[pk]) for pk in boxes}
    max_w = max((w for w, h in box_sizes.values()), default=MIN_BOX_WIDTH)
    max_h = max((h for w, h in box_sizes.values()), default=MIN_BOX_HEIGHT)
    max_w = max(max_w, EXTERNAL_WIDTH)
    max_h = max(max_h, EXTERNAL_HEIGHT)
    cell_w = max_w + CELL_GAP_X
    cell_h = max_h + CELL_GAP_Y

    all_cols = [c for c, r in box_coords.values()] + [c for c, r, *_ in external_coords.values()]
    all_rows = [r for c, r in box_coords.values()] + [r for c, r, *_ in external_coords.values()]
    min_col, min_row = min(all_cols, default=0), min(all_rows, default=0)

    def cell_origin(col, row):
        return (col - min_col) * cell_w, (row - min_row) * cell_h

    # box_x/box_y = top-left of each box rect, centered in its grid cell
    box_rects = {}
    for pk, (col, row) in box_coords.items():
        ox, oy = cell_origin(col, row)
        w, h = box_sizes[pk]
        bx = ox + (cell_w - w) / 2
        by = oy + (cell_h - h) / 2
        box_rects[pk] = (bx, by, w, h)

    ext_rects = {}
    for key, (col, row, obj, vec) in external_coords.items():
        ox, oy = cell_origin(col, row)
        w, h = EXTERNAL_WIDTH, EXTERNAL_HEIGHT
        bx = ox + (cell_w - w) / 2
        by = oy + (cell_h - h) / 2
        ext_rects[key] = (bx, by, w, h)

    # --- SVG layers --------------------------------------------------------
    svg_conduits = []
    svg_boxes = []
    svg_externals = []
    svg_ports = []
    svg_text = []

    # Junction boxes: chassis rect + header text + ports on all 4 sides
    port_points = {}  # terminal_pk -> (ex, ey, sx, sy, dir_vec, terminal)
    for pk, box in boxes.items():
        bx, by, bw, bh = box_rects[pk]
        site, size = _junction_box_details(box)
        box_url = box.get_absolute_url() if hasattr(box, 'get_absolute_url') else '#'

        svg_boxes.append(
            f'<a xlink:href="{box_url}" target="_parent">'
            f'<rect class="parent-object" height="{bh:.1f}" rx="10" '
            f'style="fill:#eef4ff" width="{bw:.1f}" x="{bx:.1f}" y="{by:.1f}" /></a>'
        )
        cx = bx + bw / 2
        svg_text.append(f'<text class="bold" x="{cx:.1f}" y="{by + 18:.1f}">{_svg_text(box.name)}</text>')
        svg_text.append(f'<text x="{cx:.1f}" y="{by + 36:.1f}">{_svg_text(site)}</text>')
        svg_text.append(f'<text x="{cx:.1f}" y="{by + 52:.1f}" style="font-size:.75rem">{_svg_text(size)}</text>')

        sides = box_sides[pk]
        pts = _port_points(sides, bx, by, bw, bh)
        port_points.update(pts)

        for term_pk, (ex, ey, sx, sy, vec, term) in pts.items():
            connected = term.is_connected
            fill = '#333' if connected else '#ccc'
            term_url = term.get_absolute_url() if hasattr(term, 'get_absolute_url') else '#'
            svg_ports.append(
                f'<a xlink:href="{term_url}" target="_parent">'
                f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="5" style="fill:{fill};stroke:#000;stroke-width:1">'
                f'<title>{_svg_text(term.name)}</title></circle></a>'
            )
            if not connected:
                # short dashed stub with no destination, so an empty port still
                # visibly reads as "sticking out of the box" per the request
                svg_ports.append(
                    f'<line x1="{ex:.1f}" y1="{ey:.1f}" x2="{sx:.1f}" y2="{sy:.1f}" '
                    f'style="stroke:#ccc;stroke-width:2;stroke-dasharray:3,3" />'
                )
            # label offset further out along the same direction as the stub
            lx, ly = ex + vec[0] * (STUB_LEN + 6), ey + vec[1] * (STUB_LEN + 6)
            anchor = 'middle'
            if vec[0] > 0:
                anchor = 'start'
            elif vec[0] < 0:
                anchor = 'end'
            svg_text.append(
                f'<text style="font-size:.7rem;text-anchor:{anchor};'
                f'paint-order:stroke;stroke:#fff;stroke-width:3px" '
                f'x="{lx:.1f}" y="{ly:.1f}">{_svg_text(term.name)}</text>'
            )

    # External (non-JunctionBox) endpoints
    for key, (bx, by, bw, bh) in ext_rects.items():
        _, _, obj, vec = external_coords[key]
        device = _termination_device(obj)
        name, model, location = _device_details(device or obj)
        role_color = _device_role_color(device)
        url = _termination_url(obj)
        cx = bx + bw / 2

        svg_externals.append(
            f'<a xlink:href="{url}" target="_parent">'
            f'<rect class="parent-object" height="{bh:.1f}" rx="8" '
            f'style="fill:#{role_color}" width="{bw:.1f}" x="{bx:.1f}" y="{by:.1f}" /></a>'
        )
        svg_text.append(f'<text class="bold" x="{cx:.1f}" y="{by + 20:.1f}">{_svg_text(name)}</text>')
        svg_text.append(f'<text style="font-size:.75rem" x="{cx:.1f}" y="{by + 40:.1f}">{_svg_text(model)}</text>')
        svg_text.append(f'<text style="font-size:.7rem" x="{cx:.1f}" y="{by + 58:.1f}">{_svg_text(location)}</text>')

        # the edge point where this external block connects; attach it at the
        # midpoint of the side facing back toward its neighbour
        face = (-vec[0], -vec[1])
        if face[0] > 0:
            ext_point = (bx + bw, by + bh / 2)
        elif face[0] < 0:
            ext_point = (bx, by + bh / 2)
        elif face[1] > 0:
            ext_point = (bx + bw / 2, by + bh)
        else:
            ext_point = (bx + bw / 2, by)
        ext_rects[key] = (bx, by, bw, bh, ext_point, face)

    # Conduits: orthogonal connector between the two termination points
    for edge in edges:
        conduit = edge['conduit']

        if edge['a_terminal'] is not None and edge['a_terminal'].pk in port_points:
            p0 = port_points[edge['a_terminal'].pk]
            start_pt, start_dir = (p0[0], p0[1]), p0[4]
        elif edge['a_external'] is not None:
            ext_data = ext_rects.get(_ext_key(edge['a_external']))
            if not ext_data:
                continue
            start_pt, start_dir = ext_data[4], ext_data[5]
        else:
            continue

        if edge['b_terminal'] is not None and edge['b_terminal'].pk in port_points:
            p1 = port_points[edge['b_terminal'].pk]
            end_pt, end_dir = (p1[0], p1[1]), p1[4]
        elif edge['b_external'] is not None:
            ext_data = ext_rects.get(_ext_key(edge['b_external']))
            if not ext_data:
                continue
            end_pt, end_dir = ext_data[4], ext_data[5]
        else:
            continue

        path_points = _route_orthogonal(start_pt, start_dir, end_pt, end_dir)
        cable_color = DEFAULT_CABLE_COLOR
        pts_str = _fmt_points(path_points)
        svg_conduits.append(f'<polyline class="cable-shadow" points="{pts_str}" />')
        svg_conduits.append(f'<polyline style="stroke:#{cable_color};stroke-width:3;fill:none" points="{pts_str}" />')

        mid = path_points[len(path_points) // 2]
        cable_count = conduit.current_cable_count if hasattr(conduit, 'current_cable_count') else None
        label = conduit.name
        if cable_count:
            label = f'{label} ({cable_count} cable{"s" if cable_count != 1 else ""})'
        svg_text.append(
            f'<text style="font-size:.75rem;paint-order:stroke;stroke:#fff;stroke-width:4px" '
            f'x="{mid[0]:.1f}" y="{mid[1]:.1f}">{_svg_text(label)}</text>'
        )

    # --- canvas size ---------------------------------------------------
    max_x = max(
        [bx + bw for bx, by, bw, bh in box_rects.values()] +
        [v[0] + v[2] for v in ext_rects.values()] + [0]
    )
    max_y = max(
        [by + bh for bx, by, bw, bh in box_rects.values()] +
        [v[1] + v[3] for v in ext_rects.values()] + [0]
    )
    total_w = max_x + MARGIN * 2
    total_h = max_y + MARGIN * 2

    svg = []
    svg.append('<?xml version="1.0" encoding="UTF-8" standalone="no"?>')
    svg.append(
        f'<svg height="{total_h:.1f}" version="1.1" width="{total_w:.1f}" '
        f'id="svg-infrastructure-map" xmlns="http://www.w3.org/2000/svg" '
        f'xmlns:xlink="http://www.w3.org/1999/xlink">'
    )
    svg.append('<defs><style type="text/css"><![CDATA[')
    svg.append(
        '*{font-family:system-ui,-apple-system,Segoe UI,Roboto,Helvetica Neue,Noto Sans,'
        'Liberation Sans,Arial,sans-serif;font-size:.875rem}text{text-anchor:middle;'
        'dominant-baseline:middle;fill:#000}text.bold{font-weight:700}svg{background-color:#fff}'
        'svg rect{stroke:#000;stroke-width:1}svg line{stroke-width:2px}'
        'svg polyline{fill:none;stroke-width:3px}svg .cable-shadow{stroke:#666;stroke-width:5px}'
    )
    svg.append(']]></style></defs>')
    svg.append(f'<g transform="translate({MARGIN},{MARGIN})">')
    svg.extend(svg_boxes)
    svg.extend(svg_externals)
    svg.extend(svg_conduits)
    svg.extend(svg_ports)
    svg.extend(svg_text)
    svg.append('</g>')
    svg.append('</svg>')
    return mark_safe('\n'.join(svg))
