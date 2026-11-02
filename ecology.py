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
import re
import math

AREAS = {
    'grove': {'name': 'the tree grove east of the workbench', 'x': 17., 'z': 10., 'r': 6.5},
    'woodland_edge': {'name': 'the woodland edge around the clearing', 'x': 0., 'z': 0., 'r_min': 17., 'r_max': 31.},
    'spring_side': {'name': 'the ground around the spring and fruit bushes', 'x': -17., 'z': -1., 'r': 5.},
    'clearing': {'name': 'the open clearing', 'x': 0., 'z': 0., 'r': 15.},
    'deeper_woods': {'name': 'the deeper woods beyond the edge', 'x': 0., 'z': 0., 'r_min': 31., 'r_max': 46.},
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
        # Trees added later (the deeper woods, planted ones) get a species once; nothing else changes.
        for ident, t in world['trees'].items():
            if ident not in eco['tree_species']:
                eco['tree_species'][ident] = t.get('species') or SPECIES_CYCLE[(int(ident.split('-')[1]) * 7) % len(SPECIES_CYCLE)]
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
    if t['stage'] == 'young':
        return [(t['id'], f'{t["id"]} is a young {sp} he planted, about {t["height"]:.1f} m tall, with {leaf_state(sp, doy)}.')]
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


# What can only be made out up close: bark, branching, buds and leaf form. Real British
# natural history, written for each species. Seen when he inspects a tree, or when an
# observation is focused on that tree by name.
CLOSE = {
    'hornbeam': {'bark': 'smooth silver-grey bark; the trunk is fluted with shallow ridges, like tensed muscle',
                 'branches': 'branches rise steeply from low on the trunk, crowded with fine twigs',
                 'buds': 'slender pointed buds lie pressed flat against the twigs',
                 'leaves': 'oval leaves with doubly toothed edges and straight parallel veins, pleated between the veins'},
    'oak': {'bark': 'rough grey-brown bark split into deep vertical fissures and ridges',
            'branches': 'thick branches spread wide and twist as they go',
            'buds': 'rounded brown buds sit clustered at the twig tips',
            'leaves': 'leaves with rounded lobes, two small ear-like lobes at the base and almost no stalk'},
    'silver birch': {'bark': 'the white bark peels in papery bands; low on the trunk it turns dark and cracked',
                     'branches': 'slender branches angle upwards and the fine twigs droop at their tips',
                     'buds': 'small pointed buds sit on twigs dotted with tiny pale warts',
                     'leaves': 'small triangular leaves with double-toothed edges on thin stalks'},
    'hazel': {'bark': 'smooth, shiny copper-brown bark peeling in thin papery strips',
              'branches': 'several stems rise together from one base rather than a single trunk',
              'buds': 'small rounded buds, faintly hairy, alternate along the twigs',
              'leaves': 'rounded leaves, soft and hairy, with a pointed tip and toothed edges'},
    'ash': {'bark': 'pale grey bark, smooth on the young stems, in a criss-cross of ridges on the old trunk',
            'branches': 'branches curve downwards then turn up at their tips',
            'buds': 'stout black buds sit in opposite pairs at the twig ends',
            'leaves': 'each leaf is a row of paired leaflets along one stalk'},
    'holly': {'bark': 'thin smooth grey bark',
              'branches': 'dense branches keep their leaves all year',
              'buds': 'small green buds sit where the leaves meet the twigs',
              'leaves': 'glossy dark leaves, the lower ones spiny-edged and the higher ones smoother'},
}


NEGATIONS = re.compile(r'\b(not|no|past|except|excluding|besides|beyond|instead of|other than|apart from|rather than|away from|avoid|avoiding|skip|skipping|without)\b')
NEW_WORDS = re.compile(r"\b(unrecorded|unlogged|not yet recorded|never recorded|not recorded|haven't recorded|have not recorded|unseen|unfamiliar|new to me|fresh)\b")


def _negated(text, at):
    """True when a name sits in a clause he is steering away from: 'not a hornbeam, hazel or tree-65'."""
    clause = re.split(r'[.;:!?]|\bbut\b|\binstead\b|\bthen\b', text[:at])[-1]
    return bool(NEGATIONS.search(clause))


# Close detail of the smaller plants: real British natural history, seen when he looks at one by name or place.
CLOSE_PLANTS = {
    'bramble': ['leaves of three to five toothed leaflets, dark above and paler beneath',
                'ridged purplish stems armed with hooked prickles; where stem tips touch the ground they have rooted'],
    'bracken': ['each frond is divided again and again along one tall grooved stem',
                'the stems rise singly from underground runners, not from a crown'],
    'ivy': ['leaves on the climbing stems are lobed; leaves on the flowering shoots are plain ovals',
            'the climbing stems are covered in short brown rootlets pressed into the bark'],
    'holly seedlings': ['the small glossy leaves have wavy, sharply spined edges', 'each seedling is only a hand or two high'],
    'honeysuckle': ['oval leaves in opposite pairs along the stems', 'the stems twine clockwise, seen from above'],
    'male fern': ['the fronds are divided twice; each small lobe is blunt and finely toothed',
                  'pale brown papery scales cover the base of the stalks'],
    'nettles': ['heart-shaped toothed leaves in opposite pairs', 'fine stinging hairs cover the square stems and the leaves'],
    'moss': ['a dense cushion of tiny overlapping leaves, darker and wetter at the base'],
    'fly agaric': ['the white flecks on the caps rub off; underneath are crowded white gills',
                   'each stem is white with a ragged ring and a swollen base'],
    'grass': ['fine blades, with last summer\'s seed heads gone to straw'],
}


def plant_close_facts(p, doy):
    return [(p['id'], f'Up close, the {p["species"]} at ({p["x"]:.0f}, {p["z"]:.0f}) has {d}.') for d in CLOSE_PLANTS.get(p['species'], [])]


def close_facts(state, t, doy):
    sp = state['ecology']['tree_species'][t['id']]
    if t['stage'] != 'standing' or sp not in CLOSE:
        return []
    c, i = CLOSE[sp], t['id']
    facts = [(i, f'Up close, {i} has {c["bark"]}.'), (i, f'On {i}, {c["branches"]}.')]
    cal = LEAVES.get(sp)
    if cal is None or _between(doy, cal[1] - 60, 365) or _between(doy, 1, cal[0]):
        facts.append((i, f'On {i}, {c["buds"]}.'))
    if leaf_cover(sp, doy) > 0:
        late = cal is not None and doy > cal[1]
        facts.append((i, f'{i} has {c["leaves"]}' + ('; the ones left have turned yellow-brown.' if late else '.')))
    return facts


def in_area(area, x, z):
    a = AREAS[area]
    d = math.hypot(x - a['x'], z - a['z'])
    if 'r' in a:
        return d <= a['r']
    return a['r_min'] <= d <= a['r_max']


RELATION_WORDS = ('climbs', 'beneath', 'under', 'twist', 'feeding', 'near', 'light', 'shade', 'damp', 'north-facing', 'stump')


# What kind of thing each species is, in plain words he might use when looking for one (v0.23.2).
PLANT_KIND = {'bramble': 'shrub bush', 'holly seedlings': 'shrub bush seedling', 'honeysuckle': 'shrub climber vine',
              'ivy': 'climber vine', 'bracken': 'fern', 'male fern': 'fern', 'fly agaric': 'fungus mushroom toadstool',
              'bluebell': 'flower bulb', 'wood anemone': 'flower', 'nettles': 'herb weed', 'moss': 'moss',
              'grass': 'grass'}
KIND_WORDS = {'bird', 'animal', 'shrub', 'bush', 'tree', 'fern', 'flower', 'fungus', 'fungi', 'mushroom', 'toadstool', 'climber',
              'vine', 'moss', 'grass', 'herb', 'weed', 'seedling', 'bulb'}


def _tags(kind, text):
    """Plain descriptive words used only to match what he says he is looking for."""
    tags = kind + (' tree leaves season' if kind in LEAVES else ' plant ' + PLANT_KIND.get(kind, ''))
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
    if daylight >= .12:  # birds about the place (v0.25): their look and where they are, never named
        import birds, sys
        facts += [(a, x, 'bird animal ' + x) for a, x in birds.facts(state, sys.modules[__name__], area, daylight)]
    import wildlife, sys        # deer (v0.26): by look, where they are and what they are doing, never named
    facts += [(a, x, 'animal deer mammal ' + x) for a, x in wildlife.facts(state, sys.modules[__name__], area, daylight)]
    return facts


def fact_key(about, text):
    """What counts as having seen something: a bird is the same bird wherever it perches."""
    return _key(about) if str(about).startswith(('bird-', 'deer-')) else _key(text)


def _key(text):
    return hashlib.sha1(text.encode()).hexdigest()[:12]


def _terms(text):
    import memory_recall
    return memory_recall.words(text)


def observe(state, area, focus, doy, daylight, limit=5, lamp=False):
    """Return what Crow notices in an area. Focus makes matching things likelier, not guaranteed.

    In darkness nothing can be made out, unless he carries a light: then only a couple of nearby details."""
    eco = ensure(state)
    if area not in AREAS:
        return {'success': False, 'text': 'That area is not part of the world.', 'findings': []}
    a = AREAS[area]
    # The edge is a ring; a single centre measurement would be meaningless, so light is reported per finding there.
    light = ground_light(state, a['x'], a['z'], doy) if 'r' in a else None
    if daylight < .12 and not lamp:
        text = f'Observed {a["name"]} in darkness. Only outlines of trunks and shrubs were visible; no plant detail could be made out.'
        return {'success': True, 'text': text, 'findings': [], 'area': area, 'dark': True}
    if daylight < .12:
        limit = 2  # a lantern's small circle of light
    facts = visible_facts(state, area, doy, daylight)
    # What he is looking for, without the things he is steering away from ("a shrub, not a tree or fern").
    positive = NEW_WORDS.sub(' ', str(focus).lower())
    positive = re.sub(NEGATIONS.pattern + r'[^.;:!?]*', ' ', positive)
    want = _terms(positive)
    want_kinds = want & {w for k in KIND_WORDS for w in _terms(k)}
    steering_away = ' '.join(m.group() for m in re.finditer(NEGATIONS.pattern + r'[^.;:!?]*', NEW_WORDS.sub(' ', str(focus).lower())))
    avoid = _terms(steering_away) - want - _terms('plant leaves season edge woodland clearing grove')
    eco['observations'] += 1
    # Deterministic per observation so results are reproducible, but not the same every visit.
    # A focus that names something (tree-65) means looking at that thing: everything visible
    # about it comes first. Before v0.21.3 the name was reduced to the word "tree" and matched every tree.
    # Names he is steering away from ("not tree-65", "other than tree-65") are not what he is looking at.
    lowered = str(focus).lower()
    named = set()
    for m in re.finditer(r'\b[a-z]+-\d+\b|\((-?\d+(?:\.\d+)?),\s*(-?\d+(?:\.\d+)?)\)', lowered):
        if _negated(lowered, m.start()):
            continue
        if m.group(1) is None:
            named.add(m.group())
        else:  # a place he names by its coordinates: whatever grows right there
            x, z = float(m.group(1)), float(m.group(2))
            near = [p['id'] for p in eco['plants'] if math.hypot(p['x'] - x, p['z'] - z) < 2 and p.get('host') is None]
            near += [t['id'] for t in state['built_world']['trees'].values() if math.hypot(t['x'] - x, t['z'] - z) < 1.5]
            named.update(near[:2])
    seeking_new = not named and bool(NEW_WORDS.search(lowered))
    def avoided(fact):
        return bool(avoid & _terms(fact[2]))
    def of_kind(fact):
        return not avoided(fact) and (not want_kinds or bool(want_kinds & _terms(fact[2])))
    def about_named(fact):
        return fact[0] in named or any(re.search(r'\b' + re.escape(n) + r'\b', fact[1].lower()) for n in named)
    def lively(fact):
        # Something alive and moving catches the eye before one more still tree (v0.26.1). Before, ties among
        # new things fell to list order, plants and trees first, so animals were never the ones noticed.
        return 3 if str(fact[2]).startswith(('bird animal', 'animal deer')) else 0
    def order(fact):
        if about_named(fact):
            return -100 - len(want & _terms(fact[1]))
        if avoided(fact):
            return 100  # what he said he is not looking for comes last
        if seeking_new and fact_key(fact[0], fact[1]) not in eco['seen'] and of_kind(fact):
            return -50 - len(want & _terms(fact[1] + ' ' + fact[2])) - lively(fact)  # looking for what he has not noted yet
        overlap = len(want & _terms(fact[1] + ' ' + fact[2]))
        seen = eco['seen'].get(fact_key(fact[0], fact[1]), 0)
        jitter = int(_key(fact[1] + str(eco['observations'])), 16) % 1000 / 1000
        return (-(overlap * 2 + jitter - .8 * min(seen, 3) + lively(fact) / 3))
    ranked = sorted(facts, key=order)
    focused = [f for f in ranked if about_named(f)]
    if focused:
        # Looking at one named thing: close detail of it, and nothing about its neighbours.
        for n in named:
            t = state['built_world']['trees'].get(n)
            if t and in_area(area, t['x'], t['z']):
                focused += [(a, x, '') for a, x in close_facts(state, t, doy)]
            plant = next((p for p in eco['plants'] if p['id'] == n), None)
            if plant and in_area(area, plant['x'], plant['z']):
                focused += [(a, x, '') for a, x in plant_close_facts(plant, doy)]
        chosen = focused[:8 if limit > 2 else 2]
    else:
        chosen = ranked[:limit - 1]
        rest = [f for f in ranked[limit - 1:] if not (want & _terms(f[1] + ' ' + f[2]))]
        if rest:  # one incidental thing outside the focus, so attention is not a closed loop
            chosen.append(rest[eco['observations'] % len(rest)])
    findings = []
    for about, text, _ in chosen:
        k = fact_key(about, text)
        findings.append({'about': about, 'text': text, 'new': k not in eco['seen']})
        eco['seen'][k] = eco['seen'].get(k, 0) + 1
        record(state, about)
    if len(eco['seen']) > 6000:  # was 600, which made old sights count as new again once the woods grew
        for k in list(eco['seen'])[:500]:
            del eco['seen'][k]
    new = sum(f['new'] for f in findings)
    # The honest edge of what can be seen (v0.21.6). Stated plainly, with no suggestion of what to do.
    edge, edge_text = None, ''
    if named and not focused:
        edge = {'kind': 'not_here', 'target': ', '.join(sorted(named)), 'place': area, 'focus': focus[:160]}
        edge_text = f' {", ".join(sorted(named))} is not in {a["name"]}.'
    elif focused and findings and not new:
        target = ', '.join(sorted(named))
        edge = {'kind': 'seen_all', 'target': target, 'place': area, 'focus': focus[:160]}
        edge_text = (f' Everything that can be made out about {target} by eye has been seen before;'
                     f' nothing about it has changed since.')
    elif seeking_new and want_kinds and not any(of_kind(f) for f in facts):
        kind = ' or '.join(sorted(want_kinds))
        edge = {'kind': 'not_found', 'target': kind, 'place': area, 'focus': focus[:160]}
        edge_text = f' There is no {kind} anywhere in {a["name"]}.'
    elif seeking_new and want_kinds and not any(f['new'] and of_kind(next(x for x in chosen if x[1] == f['text'])) for f in findings):
        kind = ' or '.join(sorted(want_kinds))
        edge = {'kind': 'seen_all', 'target': f'{kind} in {area}', 'place': area, 'focus': focus[:160]}
        edge_text = f' Every {kind} that can be made out in {a["name"]} at the moment has been seen before.'
    elif seeking_new and findings and not new:
        edge = {'kind': 'seen_all', 'target': area, 'place': area, 'focus': focus[:160]}
        edge_text = f' Everything that can be made out in {a["name"]} at the moment has been seen before.'
    elif want and not named and not seeking_new and not any(want & _terms(f['text']) for f in findings):
        edge = {'kind': 'not_found', 'target': '', 'place': area, 'focus': focus[:160]}
        edge_text = ' Nothing matching what he was looking for could be made out here.'
    # The edge statement comes first, so it is never the part lost when a long observation is shortened (v0.23.3).
    text = (f'Observed {a["name"]}' + (f' (ground light about {round(light * 100)}% of open sky).' if light is not None else '.') +
            edge_text + ' ' + ' '.join(f['text'] for f in findings) +
            ('' if findings else ' Nothing distinct stood out.'))
    # Whether each detail was new is kept for bookkeeping (consolidation evidence, reports) but is no
    # longer told to him: a running novelty score was our yardstick, and it made watching feel like progress.
    return {'success': True, 'text': text, 'findings': findings, 'area': area, 'ground_light': light,
            'new_details': new, 'focus': focus[:160], 'edge': edge}


def inspect(state, ident, doy, daylight, lamp=False):
    eco = ensure(state)
    tree = state['built_world']['trees'].get(ident)
    plant = next((p for p in eco['plants'] if p['id'] == ident), None)
    if not tree and not plant:
        return None
    if daylight < .12 and not lamp:
        return {'success': True, 'text': f'Too dark to examine {ident} in detail.'}
    if tree:
        facts = _tree_facts(state, tree, doy) + close_facts(state, tree, doy)
        facts += [f for p in eco['plants'] if p.get('host') == ident for f in _plant_facts(state, p, doy, daylight)]
        x, z = tree['x'], tree['z']
    else:
        facts = _plant_facts(state, plant, doy, daylight) + plant_close_facts(plant, doy)
        x, z = plant['x'], plant['z']
        if not facts:
            facts = [(ident, f'Nothing of {plant["species"]} is visible above ground at ({x:.0f}, {z:.0f}) at this time of year.')]
    for about, f in facts:
        eco['seen'][_key(f)] = eco['seen'].get(_key(f), 0) + 1
        record(state, about)
    text = f'Inspected {ident} at ({x:.0f}, {z:.0f}); ground light {round(ground_light(state, x, z, doy) * 100)}% of open sky. ' + \
        ' '.join(f for _, f in facts)
    return {'success': True, 'text': text, 'findings': [{'about': a, 'text': f} for a, f in facts],
            'seen_key': ' '.join(sorted(_key(f) for _, f in facts))}


def note_gap(state, edge, at, action):
    """For the world builder only: where Crow looked for more than the world holds.

    Never shown to him or used in his decisions. Repeats of the same gap are counted."""
    if not edge:
        return None
    gaps = state.setdefault('world_gaps', [])
    key = (edge['kind'], edge.get('target') or '', ' '.join(sorted(_terms(edge.get('focus', ''))))[:120])
    gap = next((g for g in gaps if (g['kind'], g['target'], g['key']) == key), None)
    if gap is None:
        gap = {'kind': edge['kind'], 'target': key[1], 'key': key[2], 'first': at, 'times': 0, 'focuses': []}
        gaps.append(gap)
    gap.update(last=at, times=gap['times'] + 1, place=edge.get('place'), action=action)
    f = edge.get('focus', '')
    if f and f not in gap['focuses']:
        gap['focuses'] = (gap['focuses'] + [f])[-5:]
    state['world_gaps'] = sorted(gaps, key=lambda g: g['last'])[-80:]
    return gap


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


# ---- His field notebook (v0.24.2): what he has recorded, by place and kind. Only what he has seen. ----

def _place_of_tree(t):
    if in_area('grove', t['x'], t['z']):
        return 'grove'
    for area in ('woodland_edge', 'deeper_woods', 'spring_side', 'clearing'):
        if in_area(area, t['x'], t['z']):
            return area
    return 'woodland_edge'


def record(state, about):
    eco = state['ecology']
    eco.setdefault('recorded', {}).setdefault(about, True)


def backfill_recorded(state):
    """Once: rebuild what he has recorded from his own remembered events (ids and places named in them)."""
    eco = ensure(state)
    if eco.get('recorded_backfilled'):
        return
    rec = eco.setdefault('recorded', {})
    texts = ' '.join(str(m.get('event', '')) for m in state.get('memories', []) if m.get('kind') == 'experience')
    for ident in state['built_world']['trees']:
        if re.search(r'\b' + re.escape(ident) + r'\b', texts):
            rec.setdefault(ident, True)
    for p in eco['plants']:
        at = f"({p['x']:.0f}, {p['z']:.0f})"
        host = p.get('host')
        if at in texts or (host and re.search(re.escape(p['species'].split()[0]) + r'[^.]*\b' + re.escape(host) + r'\b', texts, re.I)):
            rec.setdefault(p['id'], True)
    eco['recorded_backfilled'] = True


def notebook(state):
    """His own records, compactly: per place, plants by kind with where they are, trees by species."""
    eco = ensure(state)
    rec = eco.get('recorded', {})
    trees = state['built_world']['trees']
    out = {}
    for p in eco['plants']:
        if p['id'] not in rec:
            continue
        kind = (PLANT_KIND.get(p['species'], 'plant').split() or ['plant'])[0]
        where = f"on {p['host']}" if p.get('host') else f"({p['x']:.0f}, {p['z']:.0f})"
        out.setdefault(p['area'], {}).setdefault(kind if kind in ('moss', 'grass') else kind + 's', {}).setdefault(p['species'], []).append(where)
    import birds
    for b in birds.BIRDS:
        if b['id'] in rec:
            out.setdefault('birds_seen', {}).setdefault('birds', {}).setdefault(b['look'], ['about the place'])
    import wildlife
    for d in wildlife._read(state)['deer']:
        if d['id'] in rec:
            out.setdefault('birds_seen', {}).setdefault('animals', {}).setdefault(
                wildlife._look(d, 330, 0).split(',')[0], ['about the place'])
    for ident, t in trees.items():
        if ident not in rec:
            continue
        sp = eco['tree_species'].get(ident, 'tree')
        bucket = out.setdefault(_place_of_tree(t), {}).setdefault('trees', {})
        bucket[sp] = bucket.get(sp, 0) + 1
    book = {}
    for place, kinds in out.items():
        lines = []
        for kind, items in sorted(kinds.items()):
            if kind == 'trees':
                lines.append('trees: ' + ', '.join(f'{sp} {n}' for sp, n in sorted(items.items())))
            else:
                lines.append(f'{kind}: ' + '; '.join(f'{sp} ' + ', '.join(w[:12] for w in ws[:6]) for sp, ws in sorted(items.items())))
        book['birds and animals he has seen' if place == 'birds_seen' else AREAS.get(place, {}).get('name', place)] = \
            [l.replace(' about the place', '') for l in lines] if place == 'birds_seen' else lines
    return book
