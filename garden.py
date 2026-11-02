"""Three garden beds beside the cabin: soil, water, weeds, seasons and slow growth.

An authored world opportunity, like the spring and fruit bushes. Nothing tells
Crow to garden or how; what he can observe is the soil, the weeds and the
plants. Rules (per active hour, nothing changes while he is paused or closed):

- moisture falls by about a quarter a day (faster in summer); watering takes
  2 litres from the spring basin and soaks the bed;
- weeds creep in (faster in summer); weeding clears them;
- a sown crop grows only while the bed is moist (>0.3) and not choked (weeds
  <0.6); at summer pace it ripens in about three weeks, in midwinter about
  four times slower; a bed left very dry for long withers the crop;
- a ripe crop can be picked: up to 3 servings of food, fewer if it suffered.

Seeds come from the trading post. This is a simple model, not horticulture.

v0.23: real crops with UK sowing seasons and growing times, all on his own
calendar. Tender crops (salad, radish, potatoes, mixed vegetables) do not grow in
cold months and are hurt by winter frost; hardy ones (broad beans, garlic, onion
sets) sit through winter and grow on in spring. Sowing out of season is allowed;
the seed simply does what real seed would. Nothing here tells him what to grow.
"""
import math

BEDS = [(-11.4, -15.6), (-9.0, -15.6), (-6.6, -15.6)]
SITE = (-9.0, -14.2)
DAYS_TO_RIPE = 21.
# item: (crop name, days to ripen at full summer pace, servings, hardy)
# Day counts are for summer growth; cold months slow everything, so autumn-planted
# hardy crops are ready the next summer, as in a real garden.
CROPS = {
    'seeds': ('mixed vegetables', 60, 3., False),
    'salad_seeds': ('salad leaves', 35, 2., False),
    'radish_seeds': ('radishes', 28, 1.5, False),
    'seed_potatoes': ('potatoes', 110, 6., False),
    'broad_bean_seeds': ('broad beans', 100, 4., True),
    'garlic_bulbs': ('garlic', 150, 3., True),
    'onion_sets': ('onions', 110, 3., True),
}
DURATIONS = {'sow': 900, 'water': 600, 'weed': 1200, 'harvest': 900, 'look': 300}


def ensure(state):
    g = state.setdefault('garden', {'beds': [{'n': i + 1, 'crop': None, 'growth': 0., 'moisture': .2, 'weeds': .1, 'health': 1.}
                                             for i in range(len(BEDS))], 'picked': 0.})
    return g


def season(doy):
    """1 around midsummer, 0.25 in midwinter (UK-like)."""
    return .25 + .75 * max(0., math.sin((doy - 80) / 365 * 2 * math.pi))


def warmth(doy):
    """0 in late January, 1 in late July: UK soil warmth lags the sun by about a month."""
    return .5 - .5 * math.cos(2 * math.pi * (doy - 20) / 365)


def advance(state, hours, doy):
    g = ensure(state)
    if hours <= 0:
        return
    days = hours / 24
    s = season(doy)
    for b in g['beds']:
        w = warmth(doy)  # winter rain and cold keep beds damp and weeds slow; summer dries them fast
        b['moisture'] = round(max(0., b['moisture'] - days * (.04 + .3 * w)), 4)
        b['weeds'] = round(min(1., b['weeds'] + days * (.01 + .15 * w)), 4)
        if b['crop'] == 'growing':
            _, ripe_days, _, hardy = CROPS.get(b.get('item', 'seeds'), CROPS['seeds'])
            w = warmth(doy)
            # Tender crops grow from about mid-April to late October; hardy ones creep on through winter.
            pace = w if w >= .4 else (max(w, .15) if hardy else 0.)
            if b['moisture'] > .3 and b['weeds'] < .6 and pace:
                b['growth'] = round(min(1., b['growth'] + days * pace / ripe_days), 4)
            if not hardy and w < .25:  # frosts from about late November to mid-March damage tender plants
                b['health'] = round(max(0., b['health'] - days * .25), 4)
            if b['moisture'] < .1:
                b['health'] = round(max(0., b['health'] - days * .5), 4)
            if b['weeds'] > .8:
                b['health'] = round(max(0., b['health'] - days * .1), 4)
            if b['health'] <= 0:
                b['crop'] = 'withered'


def stage(b):
    if b['crop'] == 'withered':
        return 'withered'
    if b['crop'] != 'growing':
        return 'empty'
    g = b['growth']
    return 'ripe' if g >= 1 else 'sown' if g < .08 else 'sprouting' if g < .35 else 'growing'


def look(b):
    """What can be seen at a bed: no advice, no numbers he could not perceive."""
    soil = 'soaked' if b['moisture'] > .7 else 'damp' if b['moisture'] > .3 else 'dry and pale' if b['moisture'] > .1 else 'cracked and dusty'
    weeds = 'no weeds' if b['weeds'] < .15 else 'a few weeds' if b['weeds'] < .45 else 'weeds spreading' if b['weeds'] < .75 else 'thick weeds'
    name = CROPS.get(b.get('item', 'seeds'), CROPS['seeds'])[0]
    plants = {'empty': 'bare soil', 'sown': f'{name} sown, no shoots yet', 'sprouting': f'small {name} shoots',
              'growing': f'leafy {name} plants', 'ripe': f'{name} ready to pick',
              'withered': f'brown, shrivelled {name}'}[stage(b)]
    if stage(b) in ('sprouting', 'growing', 'ripe') and b['health'] < .6:
        plants += ', some leaves yellowing'
    return f'Bed {b["n"]}: {plants}; soil {soil}; {weeds}.'


def summary(state):
    return [look(b) for b in ensure(state)['beds']]


def work(state, bed, task, item=''):
    g = ensure(state)
    b = next((x for x in g['beds'] if x['n'] == bed), None)
    if b is None:
        return {'success': False, 'text': 'There is no such bed.'}
    if task == 'look':
        return {'success': True, 'text': 'Looked over the garden. ' + look(b)}
    if task == 'water':
        water = state['provisions']['water_litres']
        if water < 2:
            return {'success': False, 'text': 'The spring basin is too low to carry enough water. ' + look(b)}
        state['provisions']['water_litres'] = round(water - 2, 2)
        b['moisture'] = 1.
        return {'success': True, 'text': f'Carried 2 litres from the spring and watered bed {bed}. ' + look(b)}
    if task == 'weed':
        b['weeds'] = 0.
        return {'success': True, 'text': f'Pulled the weeds from bed {bed}. ' + look(b)}
    if task == 'sow':
        if stage(b) not in ('empty', 'withered'):
            return {'success': False, 'text': f'Bed {bed} already has plants in it. ' + look(b)}
        owned = state.get('possessions', {})
        item = item if owned.get(item) and item in CROPS else next((k for k in CROPS if owned.get(k)), '')
        if not item:
            return {'success': False, 'text': 'He has nothing to sow or plant.'}
        owned[item] -= 1
        b.update(crop='growing', growth=0., health=1., item=item)
        return {'success': True, 'text': f'Sowed {CROPS[item][0]} in bed {bed}. ' + look(b)}
    if task == 'harvest':
        if stage(b) != 'ripe':
            return {'success': False, 'text': f'Nothing in bed {bed} is ready to pick. ' + look(b)}
        servings = round(CROPS.get(b.get('item', 'seeds'), CROPS['seeds'])[2] * max(.3, b['health']), 1)
        state['provisions']['pantry'] = round(state['provisions']['pantry'] + servings, 2)
        g['picked'] = round(g['picked'] + servings, 2)
        name = CROPS.get(b.get('item', 'seeds'), CROPS['seeds'])[0]
        b.update(crop=None, growth=0., health=1., item=None)
        return {'success': True, 'text': f'Picked {servings:g} servings of {name} from bed {bed}; they keep with his provisions.'}
    return {'success': False, 'text': 'He did not settle on what to do in the garden.'}
