from html import escape

from django.utils.safestring import mark_safe

from .tracer import order_conduit_chain, trace_cable_path


DEFAULT_CABLE_COLOR = '000000'
DEFAULT_ROLE_COLOR = '9e9e9e'


def _svg_text(value, fallback='N/A'):
    """Return a null-safe, XML-escaped SVG text value."""
    return escape(str(value) if value not in (None, '') else fallback)

def _svg_color(value, fallback):
    """Return a safe six-digit RGB color for an SVG attribute."""
    color = str(value or '').lstrip('#')
    if len(color) == 6 and all(character in '0123456789abcdefABCDEF' for character in color):
        return color
    return fallback

def _termination_device(termination):
    """Safely extract the parent entity (Device, Module, Circuit, PowerFeed, etc.) from a termination."""
    if termination is None:
        return None
    for attr in ('device', 'module', 'circuit', 'power_panel', 'power_feed'):
        obj = getattr(termination, attr, None)
        if obj is not None:
            return obj
    return None

def _device_details(obj):
    """Return (name, model/type, location) for any NetBox device or object type."""
    if obj is None:
        return 'Unattached Endpoint', 'N/A', 'N/A'

    name = str(getattr(obj, 'name', None) or getattr(obj, 'label', None) or obj)

    # Determine type / model / summary
    model_str = 'N/A'
    if getattr(obj, 'device_type', None):
        dev_type = obj.device_type
        manufacturer = getattr(getattr(dev_type, 'manufacturer', None), 'name', None)
        model = getattr(dev_type, 'model', None)
        model_str = ' '.join(p for p in (manufacturer, model) if p) or 'N/A'
    elif getattr(obj, 'module_type', None):
        mod_type = obj.module_type
        manufacturer = getattr(getattr(mod_type, 'manufacturer', None), 'name', None)
        model = getattr(mod_type, 'model', None)
        model_str = ' '.join(p for p in (manufacturer, model) if p) or 'N/A'
    elif getattr(obj, 'circuit_type', None):
        provider = getattr(getattr(obj, 'provider', None), 'name', None)
        c_type = getattr(obj.circuit_type, 'name', None)
        model_str = ' '.join(p for p in (provider, c_type) if p) or 'N/A'
    elif hasattr(obj, '_meta'):
        model_str = obj._meta.verbose_name.title()

    # Determine location hierarchy
    location_parts = []
    for attr in ('site', 'location', 'rack'):
        val = getattr(obj, attr, None)
        if val and getattr(val, 'name', None):
            location_parts.append(val.name)
    if getattr(obj, 'rack', None) and getattr(obj, 'face', None):
        if hasattr(obj, 'get_face_display'):
            location_parts.append(obj.get_face_display())
    if getattr(obj, 'rack', None) and getattr(obj, 'position', None) is not None:
        location_parts.append(f'U{obj.position}')

    location_str = ' / '.join(str(p) for p in location_parts if p) or 'N/A'
    return name, model_str, location_str

def _device_url(device):
    return device.get_absolute_url() if device and hasattr(device, 'get_absolute_url') else '#'

def _termination_url(termination):
    return termination.get_absolute_url() if termination and hasattr(termination, 'get_absolute_url') else '#'

def _device_role_color(device):
    if device is None:
        return DEFAULT_ROLE_COLOR
    role = getattr(device, 'role', None) or getattr(device, 'device_role', None)
    return _svg_color(getattr(role, 'color', None), DEFAULT_ROLE_COLOR)

def _junction_box_details(junction_box):
    site = getattr(getattr(junction_box, 'site', None), 'name', None) or 'N/A'
    width = getattr(junction_box, 'width_mm', None)
    height = getattr(junction_box, 'height_mm', None)
    size = f'{width:g}x{height:g} mm' if width is not None and height is not None else 'N/A'
    return site, size

def _text_width(values, minimum=180):
    """Estimate a readable SVG text-panel width from its longest line."""
    longest_line = max((len(str(val)) for val in values), default=0)
    return max(minimum, longest_line * 7 + 24)

def _get_conduits_and_jboxes_for_cable(cable_obj):
    """Return ordered conduit and junction box layout items for a cable."""
    items = []
    if not cable_obj:
        return items
    conduit_chain = order_conduit_chain(cable_obj)
    for c_item in conduit_chain:
        conduit = c_item['conduit']
        conduit_length = getattr(conduit, 'length', getattr(conduit, 'length_meters', None))
        items.append({
            'type': 'conduit',
            'height': 108,
            'label': getattr(conduit, 'name', 'Conduit'),
            'length': conduit_length,
            'url': f"/plugins/netbox_physical_infra_plugin/conduits/{getattr(conduit, 'pk', '')}/"
        })
        
        end_term = c_item['to']
        if getattr(getattr(end_term, '_meta', None), 'model_name', None) == 'junctionbox':
            location, size = _junction_box_details(end_term)
            items.append({
                'type': 'junctionbox',
                'height': 148,
                'label': getattr(end_term, 'name', 'Junction Box'),
                'location': location,
                'size': size,
                'url': f"/plugins/netbox_physical_infra_plugin/junction-boxes/{getattr(end_term, 'pk', '')}/"
            })
    return items

def _build_path_model(cable):
    """Parse trace path into an alternating sequence of nodes and cable segments."""
    native_path = trace_cable_path(cable)

    term_groups = []
    cables = []
    current_terms = []

    for step in native_path:
        ntype = step.get('node_type')
        if ntype in ('terminations', 'interface'):
            objs = step.get('objects') or ([step.get('object')] if step.get('object') else [])
            current_terms.extend(objs)
        elif ntype == 'cable':
            term_groups.append(current_terms)
            current_terms = []
            cables.append(step.get('object'))

    if current_terms or not term_groups:
        term_groups.append(current_terms)

    # Fallback if trace yielded no cables
    if not cables:
        cables = [cable]
        a_terms = list(getattr(cable.a_terminations, 'all', lambda: cable.a_terminations)())
        b_terms = list(getattr(cable.b_terminations, 'all', lambda: cable.b_terminations)())
        term_groups = [a_terms, b_terms]

    while len(term_groups) <= len(cables):
        term_groups.append([])

    nodes = []
    num_groups = len(term_groups)

    for i, terms in enumerate(term_groups):
        if i == 0:
            term = terms[0] if terms else None
            nodes.append({'type': 'top_endpoint', 'term': term, 'device': _termination_device(term)})
        elif i == num_groups - 1:
            term = terms[-1] if terms else None
            nodes.append({'type': 'bottom_endpoint', 'term': term, 'device': _termination_device(term)})
        else:
            port_a = terms[0] if len(terms) > 0 else None
            port_b = terms[-1] if len(terms) > 1 else port_a
            dev = _termination_device(port_a) or _termination_device(port_b)
            nodes.append({'type': 'patch_panel', 'port_a': port_a, 'port_b': port_b, 'device': dev})

    cable_segments = []
    for cable_obj in cables:
        conduit_items = _get_conduits_and_jboxes_for_cable(cable_obj)
        sum_h = sum(item['height'] for item in conduit_items)
        # Ensure at least 50px clearance between devices; overridden by conduit/jbox sum if larger
        seg_h = max(100, sum_h)
        cable_segments.append({'cable': cable_obj, 'conduit_items': conduit_items, 'height': seg_h})

    return nodes, cable_segments

def generate_conduit_trace_svg(cable):
    """Generates a dynamic multi-cable SVG trace supporting all devices and interface types."""
    nodes, cable_segments = _build_path_model(cable)
    print("nodes: ", nodes)
    print("cable_segments: ", cable_segments)

    # Collect all text strings to compute optimal canvas width
    left_lines = []
    right_lines = []

    for node in nodes:
        if node['device'] is not None:
            left_lines.extend(_device_details(node['device']))

    for seg in cable_segments:
        c_obj = seg['cable']
        pk = getattr(c_obj, 'pk', None) or getattr(c_obj, 'id', None) or 'N/A'
        name = getattr(c_obj, 'label', None) or str(c_obj or 'Cable')
        status = c_obj.get_status_display() if hasattr(c_obj, 'get_status_display') else getattr(c_obj, 'status', 'N/A')
        right_lines.extend((f'Cable #{pk}', name, f'Status: {status}'))

        for item in seg['conduit_items']:
            left_lines.append(item['label'])
            if item.get('length') is not None:
                left_lines.append(f'Length: {item["length"]}')
            if item['type'] == 'junctionbox':
                left_lines.extend((item.get('location', ''), item.get('size', '')))

    left_width = _text_width(left_lines)
    right_width = _text_width(right_lines, minimum=170)
    width = left_width + 210 + right_width
    center_x = left_width + 105
    junction_box_half_width = 78.5 if any(
        item['type'] == 'junctionbox'
        for seg in cable_segments
        for item in seg['conduit_items']
    ) else 0
    cable_text_x = center_x + max(34, junction_box_half_width + 18)

    svg_bg_chassis = []
    svg_cable = []
    svg_fg_ports = []
    svg_text = []

    current_y = 0.5

    # --- TOP ENDPOINT ---
    top_node = nodes[0]
    a_term = top_node['term']
    a_device = top_node['device']
    a_name, a_model, a_location = _device_details(a_device)
    a_dev_url = _device_url(a_device)
    a_term_url = _termination_url(a_term)
    a_role_color = _device_role_color(a_device)

    if a_device is not None:
        svg_bg_chassis.append(f'<a xlink:href="{a_dev_url}" target="_parent"><rect class="parent-object" height="80" rx="10" style="fill:#{a_role_color}" width="{width - 1}" x="0.5" y="{current_y}" /></a>')
        svg_text.append(f'<text class="bold" x="{center_x}" y="{current_y + 16.5}">{_svg_text(a_name)}</text>')
        svg_text.append(f'<text x="{center_x}" y="{current_y + 39.5}">{_svg_text(a_model)}</text>')
        svg_text.append(f'<text x="{center_x}" y="{current_y + 62.5}">{_svg_text(a_location)}</text>')
        current_y += 80.0

    svg_fg_ports.append(f'<a xlink:href="{a_term_url}" target="_parent"><rect class="parent-object" height="40" rx="5" style="fill:#f0f0f0" width="{width - 2}" x="1" y="{current_y}" /></a>')
    port_a_label = _svg_text(a_term, "Unterminated End A")
    svg_text.append(f'<text class="bold" x="{center_x}" y="{current_y + 20.0}">{port_a_label}</text>')
    current_y += 40.0

    # --- MIDDLE CABLE SEGMENTS & PATCH PANELS ---
    num_cables = len(cable_segments)
    for k in range(num_cables):
        seg = cable_segments[k]
        cable_obj = seg['cable']
        conduit_items = seg['conduit_items']
        seg_h = seg['height']

        cable_start_y = current_y
        cable_end_y = current_y + seg_h

        # Continuous Cable Line
        cable_color = _svg_color(getattr(cable_obj, 'color', None), DEFAULT_CABLE_COLOR)
        svg_cable.append('<g class="connector">')
        svg_cable.append(f'<line class="cable-shadow" x1="{center_x}" x2="{center_x}" y1="{cable_start_y}" y2="{cable_end_y}" />')
        svg_cable.append(f'<line style="stroke:#{cable_color}; stroke-width:5" x1="{center_x}" x2="{center_x}" y1="{cable_start_y}" y2="{cable_end_y}" />')
        svg_cable.append('</g>')

        # Cable Label (Right Side)
        pk = getattr(cable_obj, 'pk', None) or getattr(cable_obj, 'id', None) or 'N/A'
        cable_num_str = f'Cable #{pk}'
        cable_name_str = getattr(cable_obj, 'label', None) or str(cable_obj or 'Cable')
        cable_status_str = cable_obj.get_status_display() if hasattr(cable_obj, 'get_status_display') else getattr(cable_obj, 'status', 'N/A')

        mid_y = (cable_start_y + cable_end_y) / 2.0
        svg_text.append(
            f'<text class="bold" style="text-anchor:start;paint-order:stroke;stroke:#fff;stroke-width:4px" '
            f'x="{cable_text_x}" y="{mid_y - 18.0}">{_svg_text(cable_num_str)}</text>'
            f'<text style="text-anchor:start;paint-order:stroke;stroke:#fff;stroke-width:4px" '
            f'x="{cable_text_x}" y="{mid_y}">{_svg_text(cable_name_str)}</text>'
            f'<text style="text-anchor:start;paint-order:stroke;stroke:#fff;stroke-width:4px" '
            f'x="{cable_text_x}" y="{mid_y + 18.0}">Status: {_svg_text(cable_status_str)}</text>'
        )

        # Render Conduits / Junction Boxes
        sub_y = cable_start_y
        left_text_x = center_x - 95
        for item in conduit_items:
            item_h = item['height']
            item_mid_y = sub_y + (item_h / 2.0)
            if item['type'] == 'conduit':
                rect_x = center_x - 12.5
                svg_fg_ports.append(
                    f'<a xlink:href="{item["url"]}" target="_parent">'
                    f'<rect style="fill:none; stroke:#000; stroke-width:1; rx:5" width="25" height="{item_h}" x="{rect_x}" y="{sub_y}" />'
                    f'</a>'
                )
                svg_text.append(f'<text class="bold" style="text-anchor:end;paint-order:stroke;stroke:#fff;stroke-width:4px" x="{left_text_x}" y="{item_mid_y - 9.0}">{_svg_text(item["label"])}</text>')
                if item.get('length') is not None:
                    svg_text.append(f'<text style="text-anchor:end;paint-order:stroke;stroke:#fff;stroke-width:4px" x="{left_text_x}" y="{item_mid_y + 9.0}">Length: {_svg_text(item["length"])}</text>')
            elif item['type'] == 'junctionbox':
                rect_x = center_x - 78.5
                svg_fg_ports.append(
                    f'<a xlink:href="{item["url"]}" target="_parent">'
                    f'<rect style="fill:none; stroke:#000; stroke-width:1; rx:5" width="157" height="{item_h}" x="{rect_x}" y="{sub_y}" />'
                    f'</a>'
                )
                svg_text.append(f'<text class="bold" style="text-anchor:end;paint-order:stroke;stroke:#fff;stroke-width:4px" x="{left_text_x}" y="{item_mid_y - 18.0}">{_svg_text(item["label"])}</text>')
                svg_text.append(f'<text style="text-anchor:end;paint-order:stroke;stroke:#fff;stroke-width:4px" x="{left_text_x}" y="{item_mid_y}">{_svg_text(item["location"])}</text>')
                svg_text.append(f'<text style="text-anchor:end;paint-order:stroke;stroke:#fff;stroke-width:4px" x="{left_text_x}" y="{item_mid_y + 18.0}">{_svg_text(item["size"])}</text>')
            sub_y += item_h

        current_y = cable_end_y

        # Render Next Patch Panel Node
        next_node = nodes[k + 1]
        if next_node['type'] == 'patch_panel':
            port_a = next_node['port_a']
            port_b = next_node['port_b']
            dev = next_node['device']

            dev_name, dev_model, dev_location = _device_details(dev)
            role_color = _device_role_color(dev)
            dev_url = _device_url(dev)

            port_a_name = str(port_a) if port_a else "Port In"
            port_b_name = str(port_b) if port_b else "Port Out"
            port_a_url = _termination_url(port_a)
            port_b_url = _termination_url(port_b)

            # Ingress Port
            svg_fg_ports.append(
                f'<a xlink:href="{port_a_url}" target="_parent">'
                f'<rect class="parent-object" height="40" rx="5" style="fill:#f0f0f0" width="{width - 2}" x="1" y="{current_y}" />'
                f'</a>'
            )
            svg_text.append(f'<text class="bold" x="{center_x}" y="{current_y + 20.0}">{_svg_text(port_a_name)}</text>')
            current_y += 40.0

            # Device Chassis Body (if device exists)
            if dev is not None:
                svg_bg_chassis.append(
                    f'<a xlink:href="{dev_url}" target="_parent">'
                    f'<rect class="parent-object" height="80" rx="10" style="fill:#{role_color}" width="{width - 1}" x="0.5" y="{current_y}" />'
                    f'</a>'
                )
                svg_text.append(f'<text class="bold" x="{center_x}" y="{current_y + 16.5}">{_svg_text(dev_name)}</text>')
                svg_text.append(f'<text x="{center_x}" y="{current_y + 39.5}">{_svg_text(dev_model)}</text>')
                svg_text.append(f'<text x="{center_x}" y="{current_y + 62.5}">{_svg_text(dev_location)}</text>')
                current_y += 80.0

            # Egress Port
            svg_fg_ports.append(
                f'<a xlink:href="{port_b_url}" target="_parent">'
                f'<rect class="parent-object" height="40" rx="5" style="fill:#f0f0f0" width="{width - 2}" x="1" y="{current_y}" />'
                f'</a>'
            )
            svg_text.append(f'<text class="bold" x="{center_x}" y="{current_y + 20.0}">{_svg_text(port_b_name)}</text>')
            current_y += 40.0

    # --- BOTTOM ENDPOINT ---
    bottom_node = nodes[-1]
    b_term = bottom_node['term']
    b_device = bottom_node['device']
    b_name, b_model, b_location = _device_details(b_device)
    b_dev_url = _device_url(b_device)
    b_term_url = _termination_url(b_term)
    b_role_color = _device_role_color(b_device)

    svg_fg_ports.append(
        f'<a xlink:href="{b_term_url}" target="_parent">'
        f'<rect class="parent-object" height="40" rx="5" style="fill:#fff" width="{width - 1}" x="0.5" y="{current_y}" />'
        f'</a>'
    )
    port_b_label = _svg_text(b_term, "Unterminated End B")
    svg_text.append(f'<text class="bold" x="{center_x}" y="{current_y + 20.0}">{port_b_label}</text>')
    current_y += 40.0

    if b_device is not None:
        svg_bg_chassis.append(
            f'<a xlink:href="{b_dev_url}" target="_parent">'
            f'<rect class="parent-object" height="80" rx="10" style="fill:#{b_role_color}" width="{width - 1}" x="0.5" y="{current_y}" />'
            f'</a>'
        )
        svg_text.append(f'<text class="bold" x="{center_x}" y="{current_y + 16.5}">{_svg_text(b_name)}</text>')
        svg_text.append(f'<text x="{center_x}" y="{current_y + 39.5}">{_svg_text(b_model)}</text>')
        svg_text.append(f'<text x="{center_x}" y="{current_y + 62.5}">{_svg_text(b_location)}</text>')
        current_y += 80.0

    total_height = current_y + 0.5

    # --- MASTER ASSEMBLY ---
    svg = []
    svg.append('<?xml version="1.0" encoding="UTF-8" standalone="no"?>')
    svg.append(f'<svg height="{total_height}" version="1.1" width="{width}" id="svg-conduit-trace" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">')
    svg.append('<defs><style type="text/css"><![CDATA[')
    svg.append('*{font-family:system-ui,-apple-system,Segoe UI,Roboto,Helvetica Neue,Noto Sans,Liberation Sans,Arial,sans-serif;font-size:.875rem}text{text-anchor:middle;dominant-baseline:middle;fill:#000}text.bold{font-weight:700}svg{background-color:#fff}svg rect{stroke:#000;stroke-width:1}svg line{stroke-width:5px}svg polyline{fill:none;stroke-width:5px}svg .cable-shadow{stroke:#666;stroke-width:7px}')
    svg.append(']]></style></defs>')

    svg.extend(svg_bg_chassis)
    svg.extend(svg_cable)
    svg.extend(svg_fg_ports)
    svg.extend(svg_text)

    svg.append('</svg>')
    return mark_safe('\n'.join(svg))