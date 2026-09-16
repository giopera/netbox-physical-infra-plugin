# netbox_physical_infra_plugin/tracer.py
import logging

logger = logging.getLogger(__name__)


def _node_key(node):
    if node is None:
        return None
    meta = getattr(node, '_meta', None)
    app = getattr(meta, 'app_label', node.__class__.__module__)
    model = getattr(meta, 'model_name', node.__class__.__name__.lower())
    pk = getattr(node, 'pk', id(node))
    return (app, model, pk)


def _as_list(value):
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


def _termination_node(termination):
    if termination is None:
        return None
    device = getattr(termination, 'device', None)
    return getattr(device, 'rack', None) or device or termination


def _orient_conduit(conduit, current_node):
    start = conduit.start_termination
    end = conduit.end_termination
    if _node_key(start) == _node_key(current_node):
        return {'conduit': conduit, 'from': start, 'to': end, 'reversed': False}
    if _node_key(end) == _node_key(current_node):
        return {'conduit': conduit, 'from': end, 'to': start, 'reversed': True}
    return None


def _find_chain(conduits, current_node, target_node, used=None):
    used = set() if used is None else used
    if target_node is not None and _node_key(current_node) == _node_key(target_node):
        return []
    for index, conduit in enumerate(conduits):
        if index in used:
            continue
        oriented = _orient_conduit(conduit, current_node)
        if oriented is None:
            continue
        if target_node is None:
            return [oriented]
        chain = _find_chain(conduits, oriented['to'], target_node, used | {index})
        if chain is not None:
            return [oriented, *chain]
    return None


def order_conduit_chain(cable):
    """Order cable conduits from side A to side B, treating them as undirected."""
    conduits = list(cable.conduits.all()) if hasattr(cable, 'conduits') else []
    if not conduits:
        return []

    a_term = next(iter(getattr(cable, 'a_terminations', [])), None)
    b_term = next(iter(getattr(cable, 'b_terminations', [])), None)
    start_node = _termination_node(a_term)
    target_node = _termination_node(b_term)
    chain = _find_chain(conduits, start_node, target_node)
    if chain is not None:
        return chain

    first = conduits[0]
    chain = [_orient_conduit(first, first.start_termination)]
    used = {0}
    current = first.end_termination
    while True:
        next_chain = _find_chain(conduits, current, None, used)
        if not next_chain:
            break
        chain.extend(next_chain)
        used.update(conduits.index(item['conduit']) for item in next_chain)
        current = next_chain[-1]['to']
    return chain


def _get_model_name(obj):
    if obj is None:
        return ''
    meta = getattr(obj, '_meta', None)
    if meta and hasattr(meta, 'model_name'):
        return meta.model_name.lower()
    return obj.__class__.__name__.lower()


def _is_passthrough_term(term):
    if term is None:
        return False
    model_name = _get_model_name(term)
    is_pass = model_name in ('frontport', 'rearport')
    print(f"[TRACER DEBUG] _is_passthrough_term: term={term!r} (model={model_name}) -> {is_pass}", flush=True)
    return is_pass


def _get_passthrough_counterpart(term):
    if term is None:
        return None
    model_name = _get_model_name(term)
    counterpart = None

    if model_name == 'frontport':
        # 1. Try legacy 'rear_port' attribute (NetBox < 4.5)
        if hasattr(term, 'rear_port'):
            counterpart = term.rear_port
            
        # 2. Try related 'mappings' attribute (NetBox >= 4.5)
        if counterpart is None and hasattr(term, 'mappings'):
            try:
                mapping = term.mappings.first()
                if mapping:
                    counterpart = mapping if _get_model_name(mapping) == 'rearport' else getattr(mapping, 'rear_port', None)
            except Exception as e:
                print(f"[TRACER DEBUG] frontport mappings error: {e}", flush=True)
                
        # 3. Direct PortMapping ORM Query (NetBox >= 4.5)
        if counterpart is None:
            try:
                from dcim.models import PortMapping
                pm = PortMapping.objects.filter(front_port=term).first()
                if pm:
                    counterpart = pm.rear_port
            except ImportError:
                pass
            except Exception as e:
                print(f"[TRACER DEBUG] PortMapping query error: {e}", flush=True)

    elif model_name == 'rearport':
        # 1. Look for known reverse M2M or ForeignKey manager names
        for attr in ('mappings', 'front_ports', 'frontports', 'frontport_set'):
            fp_rel = getattr(term, attr, None)
            if fp_rel is not None:
                try:
                    first_rel = None
                    if callable(getattr(fp_rel, 'all', None)):
                        first_rel = fp_rel.all().first()
                    elif hasattr(fp_rel, 'first'):
                        first_rel = fp_rel.first()
                    elif isinstance(fp_rel, (list, tuple)) and fp_rel:
                        first_rel = fp_rel[0]
                    elif not callable(fp_rel):
                        first_rel = fp_rel

                    if first_rel is not None:
                        if _get_model_name(first_rel) == 'frontport':
                            counterpart = first_rel
                        elif hasattr(first_rel, 'front_port'):
                            counterpart = first_rel.front_port
                        
                        if counterpart is not None:
                            break
                except Exception as e:
                    print(f"[TRACER DEBUG] relation {attr} error: {e}", flush=True)

        # 2. Try get_front_ports() method
        if counterpart is None and hasattr(term, 'get_front_ports'):
            try:
                fps = term.get_front_ports()
                if callable(getattr(fps, 'first', None)):
                    counterpart = fps.first()
                elif isinstance(fps, (list, tuple)) and fps:
                    counterpart = fps[0]
            except Exception:
                pass

        # 3. Direct Django ORM lookup fallback
        if counterpart is None:
            try:
                from dcim.models import FrontPort
                field_names = [f.name for f in FrontPort._meta.get_fields()]
                
                # Verify legacy field existence before query
                if 'rear_port' in field_names:
                    counterpart = FrontPort.objects.filter(rear_port=term).first()
                else:
                    # NetBox >= 4.5
                    try:
                        from dcim.models import PortMapping
                        pm = PortMapping.objects.filter(rear_port=term).first()
                        if pm:
                            counterpart = pm.front_port
                    except ImportError:
                        pass
            except Exception as e:
                print(f"[TRACER DEBUG] Direct query error: {e}", flush=True)

    print(f"[TRACER DEBUG] _get_passthrough_counterpart: term={term!r} ({model_name}) -> counterpart={counterpart!r}", flush=True)
    return counterpart


def _get_term_cable(term):
    if term is None:
        return None

    # 1. Direct '.cable' property
    cable = getattr(term, 'cable', None)
    if cable is not None:
        print(f"[TRACER DEBUG] _get_term_cable via .cable: term={term!r} -> cable={cable!r}", flush=True)
        return cable

    # 2. Related manager '.cables'
    cables = getattr(term, 'cables', None)
    if cables is not None:
        cb = None
        if callable(getattr(cables, 'all', None)):
            cb = cables.all().first()
        elif hasattr(cables, 'first'):
            cb = cables.first()
        elif isinstance(cables, (list, tuple)) and cables:
            cb = cables[0]
        if cb is not None:
            print(f"[TRACER DEBUG] _get_term_cable via .cables: term={term!r} -> cable={cb!r}", flush=True)
            return cb

    # 3. Generic relation / link
    link = getattr(term, 'link', None)
    if hasattr(link, 'a_terminations') or hasattr(link, 'b_terminations'):
        print(f"[TRACER DEBUG] _get_term_cable via .link: term={term!r} -> cable={link!r}", flush=True)
        return link

    # 4. CableTermination ORM query fallback
    try:
        from dcim.models import CableTermination
        from django.contrib.contenttypes.models import ContentType
        ct = ContentType.objects.get_for_model(term)
        cterm = CableTermination.objects.filter(termination_type=ct, termination_id=term.pk).select_related('cable').first()
        if cterm and cterm.cable:
            print(f"[TRACER DEBUG] _get_term_cable via CableTermination ORM: term={term!r} -> cable={cterm.cable!r}", flush=True)
            return cterm.cable
    except Exception as e:
        print(f"[TRACER DEBUG] CableTermination ORM query error: {e}", flush=True)

    print(f"[TRACER DEBUG] _get_term_cable: term={term!r} -> NO CABLE FOUND", flush=True)
    return None


def _get_cable_terminations(cable, side):
    terms = getattr(cable, f'{side}_terminations', [])
    if callable(getattr(terms, 'all', None)):
        res = list(terms.all())
    elif isinstance(terms, (list, tuple)):
        res = list(terms)
    elif terms:
        res = [terms]
    else:
        res = []
    print(f"[TRACER DEBUG] _get_cable_terminations: cable={cable!r} side={side} -> {res}", flush=True)
    return res


def _trace_full_cable_chain(cable):
    if cable is None:
        return []

    start_pk = getattr(cable, 'pk', None) or id(cable)
    visited_cables = {start_pk}
    print(f"[TRACER DEBUG] === STARTING TRACE FOR CABLE #{start_pk} ===", flush=True)

    # 1. Trace Upstream (Side A direction)
    upstream_steps = []
    curr_cable = cable
    curr_side = 'a'

    while True:
        terms = _get_cable_terminations(curr_cable, curr_side)
        t_near = terms[0] if terms else None

        if _is_passthrough_term(t_near):
            t_far = _get_passthrough_counterpart(t_near)
            next_cable = _get_term_cable(t_far) if t_far else None
            next_cable_pk = getattr(next_cable, 'pk', None) or id(next_cable) if next_cable else None

            if next_cable and next_cable_pk not in visited_cables:
                visited_cables.add(next_cable_pk)
                upstream_steps.append({'type': 'passthrough', 'objects': [t_far, t_near]})
                upstream_steps.append({'type': 'cable', 'cable': next_cable})

                next_a_terms = _get_cable_terminations(next_cable, 'a')
                t_far_key = _node_key(t_far)
                in_a = any(_node_key(t) == t_far_key for t in next_a_terms)
                curr_side = 'b' if in_a else 'a'
                curr_cable = next_cable
                print(f"[TRACER DEBUG] Upstream moved to Cable #{next_cable_pk}, next side: {curr_side}", flush=True)
            else:
                endpoint_terms = [t_far, t_near] if t_far else [t_near]
                upstream_steps.append({'type': 'endpoint', 'objects': [t for t in endpoint_terms if t]})
                print(f"[TRACER DEBUG] Upstream hit boundary or already visited cable.", flush=True)
                break
        else:
            upstream_steps.append({'type': 'endpoint', 'objects': terms})
            print(f"[TRACER DEBUG] Upstream hit non-passthrough endpoint: {terms}", flush=True)
            break

    # 2. Trace Downstream (Side B direction)
    downstream_steps = []
    curr_cable = cable
    curr_side = 'b'

    while True:
        terms = _get_cable_terminations(curr_cable, curr_side)
        t_near = terms[0] if terms else None

        if _is_passthrough_term(t_near):
            t_far = _get_passthrough_counterpart(t_near)
            next_cable = _get_term_cable(t_far) if t_far else None
            next_cable_pk = getattr(next_cable, 'pk', None) or id(next_cable) if next_cable else None

            if next_cable and next_cable_pk not in visited_cables:
                visited_cables.add(next_cable_pk)
                downstream_steps.append({'type': 'passthrough', 'objects': [t_near, t_far]})
                downstream_steps.append({'type': 'cable', 'cable': next_cable})

                next_a_terms = _get_cable_terminations(next_cable, 'a')
                t_far_key = _node_key(t_far)
                in_a = any(_node_key(t) == t_far_key for t in next_a_terms)
                curr_side = 'b' if in_a else 'a'
                curr_cable = next_cable
                print(f"[TRACER DEBUG] Downstream moved to Cable #{next_cable_pk}, next side: {curr_side}", flush=True)
            else:
                endpoint_terms = [t_near, t_far] if t_far else [t_near]
                downstream_steps.append({'type': 'endpoint', 'objects': [t for t in endpoint_terms if t]})
                print(f"[TRACER DEBUG] Downstream hit boundary or already visited cable.", flush=True)
                break
        else:
            downstream_steps.append({'type': 'endpoint', 'objects': terms})
            print(f"[TRACER DEBUG] Downstream hit non-passthrough endpoint: {terms}", flush=True)
            break

    # 3. Assemble full path from End A to End B
    full_path = []

    for step in reversed(upstream_steps):
        if step['type'] in ('endpoint', 'passthrough'):
            full_path.append({
                'node_type': 'terminations',
                'objects': step['objects'],
                'label': ', '.join(str(o) for o in step['objects'])
            })
        elif step['type'] == 'cable':
            c = step['cable']
            full_path.append({
                'node_type': 'cable',
                'object': c,
                'label': f'Cable #{getattr(c, "pk", id(c))} ({getattr(c, "label", "") or "Unlabeled"})'
            })

    full_path.append({
        'node_type': 'cable',
        'object': cable,
        'label': f'Cable #{getattr(cable, "pk", id(cable))} ({getattr(cable, "label", "") or "Unlabeled"})'
    })

    for step in downstream_steps:
        if step['type'] in ('endpoint', 'passthrough'):
            full_path.append({
                'node_type': 'terminations',
                'objects': step['objects'],
                'label': ', '.join(str(o) for o in step['objects'])
            })
        elif step['type'] == 'cable':
            c = step['cable']
            full_path.append({
                'node_type': 'cable',
                'object': c,
                'label': f'Cable #{getattr(c, "pk", id(c))} ({getattr(c, "label", "") or "Unlabeled"})'
            })

    print(f"[TRACER DEBUG] === ASSEMBLED FULL PATH ({len(full_path)} steps) ===", flush=True)
    for idx, item in enumerate(full_path):
        print(f"  [{idx}] {item['node_type']}: {item.get('label') or item.get('objects')}", flush=True)

    return full_path


def trace_cable_path(cable):
    """Return the complete end-to-end cable path across pass-through ports and cables."""
    return _trace_full_cable_chain(cable)


def trace_route_segments(cable):
    """Return ordered pass-through and conduit segments across linked cables."""
    native_path = trace_cable_path(cable)
    route = []
    seen_pass_throughs = set()

    if native_path:
        pending_passthroughs = []
        for step in native_path:
            if step['node_type'] == 'terminations':
                for termination in step.get('objects', []):
                    model_name = _get_model_name(termination)
                    identity = (model_name, getattr(termination, 'pk', id(termination)))
                    if _is_passthrough_term(termination) and identity not in seen_pass_throughs:
                        pending_passthroughs.append(termination)
                        seen_pass_throughs.add(identity)
            elif step['node_type'] == 'cable':
                if pending_passthroughs:
                    route.append(('patch_panel', pending_passthroughs))
                    pending_passthroughs = []
                for conduit in order_conduit_chain(step['object']):
                    route.append(('conduit', conduit))

        if pending_passthroughs:
            route.append(('patch_panel', pending_passthroughs))
        return route

    for item in order_conduit_chain(cable):
        route.append(('conduit', item))
    return route