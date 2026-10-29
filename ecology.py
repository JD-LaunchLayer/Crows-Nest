"""An observable woodland: species, seasons, light and visible relationships.

This module supplies things that are actually there to be noticed. It does not
choose what Crow looks at, decide what is interesting or explain causes for
him. Observations report what is visible (a fern growing where the canopy is
dense, ivy flowers with insects on them); interpreting why is his job.

The woodland is an authored world, like the trees and spring: a plausible
south-east English mixed woodland with phenology approximated from typical
UK dates. It is not an ecological simulation. Plants do not yet grow, spread
or die in response to his actions, apart from the light measurement, which
follows the real standing/felled state of each tree. Seasonal appearance
follows the real UK calendar date, so what is visible changes through the year.
"""
import hashlib
import math

AREAS = {
    'grove': {'name': 'the tree grove east of the workbench', 'x': 17., 'z': 10., 'r': 6.5},
    'woodland_edge': {'name': 'the woodland edge around the clearing', 'x': 0., 'z': 0., 'r_min': 17., 'r_max': 31.},
    'spring_side': {'name': 'the ground around the spring and fruit bushes', 'x': -17., 'z': -1., 'r': 5.},
    'clearing': {'name': 'the open clearing', 'x': 0., 'z': 0., 'r': 15.},
}

# Approximate UK leaf calendar (day of year): leaf-out, autumn colour start, bare.
LEAVES = {'oak': (115, 295, 335), 'hornbeam': (105, 290, 330), 'silver birch': (105, 280, 315),
          'hazel': (100, 285, 320), 'ash': (130, 280, 305), 'holly': None}
AUTUMN = {'oak': '#9a7a3a', 'hornbeam': '#b08a3a', 'silver birch': '#c9a93b', 'hazel': '#b9a245', 'ash': '#8a9a55'}
GREEN = {'oak': '#4f6a3e', 'hornbeam': '#557245', 'silver birch': '#6b8a4a', 'hazel': '#5c7a45', 'ash': '#5d7848', 'holly': '#2f4a2c'}
SPECIES_CYCLE = ['oak', 'oak', 'oak', 'hornbeam', 'hornbeam', 'silver birch', 'silver birch', 'hazel', 'hazel', 'ash', 'holly']


def _between(doy, start, end):
    return start <= doy <= end if start <= end else doy >= start or doy <= end


def leaf_cover(species, doy):
    """Fraction of a full summer canopy present (0 bare – 1 full)."""
    cal = LEAVES.get(species)
    if cal is None:
        return 1.
    out, turn, bare = cal
    if doy < out or doy > bare:
        return 0.
    if doy < out + 25:
        return (doy - out) / 25
    if doy <= turn:
        return 1.
    return max(0., 1 - (doy - turn) / (bare - turn))


def leaf_state(species, doy):
    cal = LEAVES.get(species)
    if cal is None:
        return 'evergreen leaves'
    cover = leaf_cover(species, doy)
    if cover == 0:
        return 'bare branches'
    if doy < cal[0] + 25:
        return 'new leaves opening'
    if doy <= cal[1]:
        return 'full green leaves'
    return f'autumn leaves, about {round(cover * 100 / 5) * 5}% still on the branches'


def ensure(state):
    """Assign species and plant positions once. Tree IDs and stocks are untouched."""
    world = state['built_world']
    eco = state.setdefault('ecology', {})
    if eco.get('version') == 1:
        return eco
    trees = world['trees']
    species = {}
    for ident in trees:
        n = int(ident.split('-')[1])
        species[ident] = SPECIES_CYCLE[(n * 7) % len(SPECIES_CYCLE)]
    grove = [t for t in trees.values() if math.hypot(t['x'] - 17, t['z'] - 10) < 7]
    ring = sorted((t for t in trees.values() if t not in grove), key=lambda t: int(t['id'].split('-')[1]))

    def of(kind, n, pool):
        return [t for t in pool if species[t['id']] == kind][:n]

    def toward_clearing(t, d):
        r = math.hypot(t['x'], t['z']) or 1
        return round(t['x'] * (r - d) / r, 2), round(t['z'] * (r - d) / r, 2)

    plants = []

    def add(kind, x, z, area, host=None):
        ident = f"{kind.replace(' ', '_')}-{sum(1 for p in plants if p['species'] == kind) + 1}"
        plants.append({'id': ident, 'species': kind, 'x': round(x, 2), 'z': round(z, 2), 'area': area, 'host': host})

    for t in of('oak', 3, ring) + of('ash', 2, ring):
        add('ivy', t['x'], t['z'], 'woodland_edge', t['id'])
    for t in ring[2:30:7]:
        x, z = toward_clearing(t, 3.5)
        add('bramble', x, z, 'woodland_edge')
    for t in ring[5:40:12]:
        x, z = toward_clearing(t, 2.2)
        add('bracken', x, z, 'woodland_edge')
    for t in of('silver birch', 2, ring):
        add('fly agaric', t['x'] + .9, t['z'] + .6, 'woodland_edge', t['id'])
    for t in of('oak', 2, ring[10:]):
        add('holly seedlings', t['x'] + .7, t['z'] - .5, 'woodland_edge', t['id'])
    for t in of('hazel', 1, ring):
        add('honeysuckle', t['x'], t['z'], 'woodland_edge', t['id'])
    for i, (dx, dz) in enumerate([(-1.5, 1.2), (1.8, 2.5), (2.6, -1.8)]):
        add('bluebell', 17 + dx, 10 + dz, 'grove')
    add('wood anemone', 15.2, 12.4, 'grove')
    add('male fern', 18.6, 11.8, 'grove')
    add('male fern', 16.1, 7.9, 'grove')
    for t in grove[:3]:
        add('moss', t['x'], t['z'] - .2, 'grove', t['id'])
    add('nettles', -15.6, 2.4, 'spring_side')
    add('nettles', -18.4, 2.9, 'spring_side')
    add('grass', 4., -3., 'clearing')
    add('grass', -6., 6., 'clearing')
    eco.update(version=1, tree_species=species, plants=plants, seen={}, observations=0)
    return eco


def ground_light(state, x, z, doy):
    """Fraction of open-sky light reaching the ground, from actual standing trees."""
    eco = ensure(state)
    light = 1.
    for t in state['built_world']['trees'].values():
        if t['stage'] != 'standing':
            continue
        reach = t['height'] * .32 + 1
        d = math.hypot(t['x'] - x, t['z'] - z)
        if d < reach:
            light *= 1 - .75 * leaf_cover(eco['tree_species'][t['id']], doy) * (1 - d / reach * .5)
    return round(light, 2)


def _plant_facts(state, p, doy, daylight):
    eco = state['ecology']
    host = p.get('host')
    host_sp = eco['tree_species'].get(host, '')
    host_alive = host and state['built_world']['trees'].get(host, {}).get('stage') == 'standing'
    sp, at = p['species'], f"({p['x']:.0f}, {p['z']:.0f})"
    light = ground_light(state, p['x'], p['z'], doy)
    facts = []
    if sp == 'ivy':
        if host_alive:
            facts.append(f'Ivy climbs the trunk of {host} ({host_sp}), clinging by small rootlets; its leaves stay dark green.')
        else:
            facts.append(f'Ivy stems lie across the stump of {host}; the trunk they climbed is gone.')
        if _between(doy, 258, 324):
            facts.append(f'Ivy on {host} carries round heads of small yellow-green flowers.')
            if daylight > .3:
                facts.append(f'Wasps, hoverflies and bees are feeding on the ivy flowers on {host}; few other flowers are open nearby.')
        if _between(doy, 1, 95):
            facts.append(f'Ivy on {host} holds clusters of black berries.')
    elif sp == 'bramble':
        facts.append(f'A bramble thicket at {at} with arching thorny stems; ground light here is about {round(light * 100)}% of open sky.')
        if _between(doy, 150, 230):
            facts.append(f'The bramble at {at} has white-pink flowers.')
        if _between(doy, 215, 275):
            facts.append(f'The bramble at {at} has ripe blackberries; birds have taken some.')
        if _between(doy, 276, 330):
            facts.append(f'Bramble leaves at {at} are turning red-purple; a few shrivelled berries remain.')
    elif sp == 'bracken':
        if _between(doy, 120, 150):
            facts.append(f'Bracken fronds at {at} are uncurling from tight crooks.')
        elif _between(doy, 151, 269):
            facts.append(f'Waist-high green bracken at {at}; ground light about {round(light * 100)}% of open sky.')
        elif _between(doy, 270, 330):
            facts.append(f'Bracken at {at} has turned brown and is collapsing.')
        else:
            facts.append(f'Flattened dead bracken lies at {at}.')
    elif sp == 'fly agaric':
        if _between(doy, 245, 320):
            facts.append(f'Red, white-flecked toadstools stand in the litter near {host} ({host_sp}); none are under the nearby oaks.')
    elif sp == 'holly seedlings':
        facts.append(f'Small holly seedlings grow beneath {host} ({host_sp}); there is no mature holly directly overhead.')
    elif sp == 'honeysuckle':
        facts.append(f'Honeysuckle stems twist tightly around {host} ({host_sp}), always winding the same way.')
        if _between(doy, 160, 250):
            facts.append(f'Honeysuckle on {host} has trumpet-shaped scented flowers.')
        if _between(doy, 230, 290):
            facts.append(f'Honeysuckle on {host} has small red berries.')
    elif sp == 'bluebell':
        if _between(doy, 20, 104) or _between(doy, 141, 170):
            facts.append(f'Strap-shaped bluebell leaves carpet the ground at {at}, under {round(light * 100)}% light.')
        elif _between(doy, 105, 140):
            facts.append(f'Bluebells are flowering at {at} beneath the {"bare" if light > .6 else "opening"} canopy.')
    elif sp == 'wood anemone':
        if _between(doy, 60, 79) or _between(doy, 121, 160):
            facts.append(f'Deeply cut wood anemone leaves at {at}.')
        elif _between(doy, 80, 120):
            facts.append(f'White wood anemone flowers at {at}; they close in dull light.')
    elif sp == 'male fern':
        if _between(doy, 110, 320):
            facts.append(f'A shuttlecock of male fern fronds at {at}, in shade (about {round(light * 100)}% light).')
        else:
            facts.append(f'Browned male fern fronds lie flat at {at}; new crowns are curled at the centre.')
    elif sp == 'moss':
        if host_alive:
            facts.append(f'Moss grows thickly on the north-facing side of {host} ({host_sp}) and thinly on its south side.')
    elif sp == 'nettles':
        facts.append(f'A dense nettle bed at {at} near the spring, on damp dark soil.' +
                     (' Strings of green seed hang from the stems.' if _between(doy, 200, 320) else ''))
    elif sp == 'grass':
        facts.append(f'Grass and low herbs cover the open ground at {at}; ground light is about {round(light * 100)}% of open sky.')
    return [(p['id'], f) for f in facts]


def _tree_facts(state, t, doy):
    sp = state['ecology']['tree_species'][t['id']]
    if t['stage'] != 'standing':
        return [(t['id'], f'{t["id"]} is a felled {sp} tree; its stump and {t.get("stock", 0):g} kg of timber remain.')]
    article = 'an' if sp[0] in 'aeiou' else 'a'
    facts = [(t['id'], f'{t["id"]} is {article} {sp}, about {t["height"]:.1f} m tall, with {leaf_state(sp, doy)}.')]
    if sp == 'oak' and _between(doy, 255, 300):
        facts.append((t['id'], f'Acorns lie under {t["id"]}; some have been opened or carried off.'))
    if sp == 'hazel' and _between(doy, 240, 270):
        facts.append((t['id'], f'Hazelnuts hang on {t["id"]}; nibbled shells lie below.'))
    if sp == 'hazel' and (_between(doy, 280, 365) or _between(doy, 1, 14)):
        facts.append((t['id'], f'Small tight catkins are already formed on {t["id"]}.'))
    if sp == 'hazel' and _between(doy, 15, 80):
        facts.append((t['id'], f'Yellow catkins hang open on {t["id"]}, shedding pollen when shaken.'))
    if sp == 'silver birch':
        facts.append((t['id'], f'{t["id"]} has white peeling bark with dark diamond marks.'))
    if sp == 'hornbeam' and _between(doy, 270, 330):
        facts.append((t['id'], f'Bunches of winged hornbeam seeds hang on {t["id"]}.'))
    return facts


def in_area(area, x, z):
    a = AREAS[area]
    d = math.hypot(x - a['x'], z - a['z'])
    if 'r' in a:
        return d <= a['r']
    return a['r_min'] <= d <= a['r_max']


RELATION_WORDS = ('climbs', 'beneath', 'under', 'twist', 'feeding', 'near', 'light', 'shade', 'damp', 'north-facing', 'stump')


def _tags(kind, text):
    """Plain descriptive words used only to match what he says he is looking for."""
    tags = kind + (' tree leaves season' if kind in LEAVES else ' plant')
    if any(w in text for w in RELATION_WORDS):
        tags += ' interaction relationship between species growing together conditions'
    return tags


def visible_facts(state, area, doy, daylight):
    """(about, text, tags) for everything visible in an area now."""
    eco = ensure(state)
    facts = []
    for p in eco['plants']:
        if in_area(area, p['x'], p['z']):
            facts += [(a, t, _tags(p['species'], t)) for a, t in _plant_facts(state, p, doy, daylight)]
    for t in state['built_world']['trees'].values():
        if in_area(area, t['x'], t['z']):
            sp = eco['tree_species'][t['id']]
            facts += [(a, x, _tags(sp, x)) for a, x in _tree_facts(state, t, doy)]
    return facts


def _key(text):
    return hashlib.sha1(text.encode()).hexdigest()[:12]


def _terms(text):
    import memory_recall
    return memory_recall.words(text)


def observe(state, area, focus, doy, daylight, limit=5):
    """Return what Crow notices in an area. Focus makes matching things likelier, not guaranteed."""
    eco = ensure(state)
    if area not in AREAS:
        return {'success': False, 'text': 'That area is not part of the world.', 'findings': []}
    a = AREAS[area]
    # The edge is a ring; a single centre measurement would be meaningless, so light is reported per finding there.
    light = ground_light(state, a['x'], a['z'], doy) if 'r' in a else None
    if daylight < .12:
        text = f'Observed {a["name"]} in darkness. Only outlines of trunks and shrubs were visible; no plant detail could be made out.'
        return {'success': True, 'text': text, 'findings': [], 'area': area, 'dark': True}
    facts = visible_facts(state, area, doy, daylight)
    want = _terms(focus)
    eco['observations'] += 1
    # Deterministic per observation so results are reproducible, but not the same every visit.
    def order(fact):
        overlap = len(want & _terms(fact[1] + ' ' + fact[2]))
        seen = eco['seen'].get(_key(fact[1]), 0)
        jitter = int(_key(fact[1] + str(eco['observations'])), 16) % 1000 / 1000
        return (-(overlap * 2 + jitter - .8 * min(seen, 3)))
    ranked = sorted(facts, key=order)
    chosen = ranked[:limit - 1]
    rest = [f for f in ranked[limit - 1:] if not (want & _terms(f[1] + ' ' + f[2]))]
    if rest:  # one incidental thing outside the focus, so attention is not a closed loop
        chosen.append(rest[eco['observations'] % len(rest)])
    findings = []
    for about, text, _ in chosen:
        k = _key(text)
        findings.append({'about': about, 'text': text, 'new': k not in eco['seen']})
        eco['seen'][k] = eco['seen'].get(k, 0) + 1
    if len(eco['seen']) > 600:
        for k in list(eco['seen'])[:100]:
            del eco['seen'][k]
    new = sum(f['new'] for f in findings)
    text = (f'Observed {a["name"]}' + (f' (ground light about {round(light * 100)}% of open sky). ' if light is not None else '. ') +
            ' '.join(f['text'] for f in findings) +
            (f' {new} of {len(findings)} details were new to him.' if findings else ' Nothing distinct stood out.'))
    return {'success': True, 'text': text, 'findings': findings, 'area': area, 'ground_light': light,
            'new_details': new, 'focus': focus[:160]}


def inspect(state, ident, doy, daylight):
    eco = ensure(state)
    tree = state['built_world']['trees'].get(ident)
    plant = next((p for p in eco['plants'] if p['id'] == ident), None)
    if not tree and not plant:
        return None
    if daylight < .12:
        return {'success': True, 'text': f'Too dark to examine {ident} in detail.'}
    if tree:
        facts = _tree_facts(state, tree, doy)
        facts += [f for p in eco['plants'] if p.get('host') == ident for f in _plant_facts(state, p, doy, daylight)]
        x, z = tree['x'], tree['z']
    else:
        facts = _plant_facts(state, plant, doy, daylight)
        x, z = plant['x'], plant['z']
        if not facts:
            facts = [(ident, f'Nothing of {plant["species"]} is visible above ground at ({x:.0f}, {z:.0f}) at this time of year.')]
    text = f'Inspected {ident} at ({x:.0f}, {z:.0f}); ground light {round(ground_light(state, x, z, doy) * 100)}% of open sky. ' + \
        ' '.join(f for _, f in facts)
    return {'success': True, 'text': text, 'findings': [{'about': a, 'text': f} for a, f in facts]}


def view(state, doy):
    """Appearance for the 3D scene: crown colour/fullness and visible plant patches."""
    eco = ensure(state)
    trees = {}
    for ident, sp in eco['tree_species'].items():
        cover = leaf_cover(sp, doy)
        cal = LEAVES.get(sp)
        colour = GREEN[sp] if cal is None or doy <= cal[1] else AUTUMN[sp]
        trees[ident] = {'species': sp, 'cover': round(cover, 2), 'colour': colour}
    plants = []
    for p in eco['plants']:
        visible = bool(_plant_facts(state, p, doy, 1.))
        if visible and p['species'] not in ('moss', 'ivy', 'honeysuckle'):
            plants.append({k: p[k] for k in ('id', 'species', 'x', 'z')})
    return {'trees': trees, 'plants': plants}


def area_summary():
    return {k: v['name'] for k, v in AREAS.items()}
