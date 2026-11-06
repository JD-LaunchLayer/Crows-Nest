"""Every action Crow can take, defined once (v0.31.0, phase 1 of the materials and building work).

Before this, one action was spread over ACTIONS, DURATIONS, ACTION_MENU, inner.CHOICES and
unavailable_reasons(). Those names are now built from this registry, unchanged, so behaviour is the same.
Each record: where it happens, how long it takes, the neutral menu line, his own first-person words for it,
and, if it can be impossible, when and why (in his words). The details step and the executor still live
in crow.py; they move here as the generic verbs arrive.
"""
from dataclasses import dataclass
from typing import Callable, Optional
import foods
import world_state


@dataclass(frozen=True)
class Action:
    place: str
    duration: Optional[int]   # None: decided when it starts (sleep by tiredness, resumed work by what is left)
    menu: str
    choice: str
    impossible: Optional[Callable] = None   # state -> True when the world cannot do it now
    why: str = ''                           # his words for why not


REGISTRY = {
    'rest': Action('cabin', 900, 'quiet rest in the cabin',
        'sit or lie quietly in my cabin, awake'),
    'sleep': Action('cabin', None, 'sleep in the cabin until you wake',
        'go to bed and sleep until I wake rested'),
    'practise': Action('range', 1800, 'archery practice at the range; each session counts where the arrows land',
        'practise archery at the range'),
    'explore': Action('woods', 1200, 'walk through part of the woodland, noticing what is there and picking up loose wood',
        'walk through part of the woods, picking up loose wood as I go'),
    'walk': Action('woods', None, 'walk on foot to a place you know',
        'walk to a place I know'),
    'craft': Action('workbench', 2700, 'carve a small piece from 1 kg wood with a measured outcome',
        'carve something small from wood',
        impossible=lambda s: s['materials'] < 1,
        why='I have no wood to carve'),
    'read': Action('library', 900, 'look something up on Wikipedia, or read at leisure',
        'look something up or read in the reading cabin'),
    'observe': Action('woods', 600, 'look closely at one part of the woodland or clearing and notice what is actually there',
        'look closely at one part of the woods or the clearing'),
    'reflect': Action('cabin', 600, 'think quietly in the cabin',
        'sit and think in my cabin'),
    'gather': Action('woods', 1200, 'carry 3 kg of wood or stone into inventory',
        'gather wood or stone'),
    'plan': Action('workbench', 600, 'draft a construction blueprint (builds nothing)',
        'sketch a plan for something to build'),
    'construct': Action('workbench', 1800, 'work on an existing blueprint if materials allow',
        'work on building something I planned',
        impossible=lambda s: not any(p['status'] in ['proposed', 'in_progress'] for p in world_state.ensure(s)['plans']),
        why='I have no plan to build from'),
    'move_object': Action('workbench', 300, 'carry a loose object somewhere else',
        'carry something somewhere else',
        impossible=lambda s: not any(o.get('portable') for o in world_state.ensure(s)['objects'].values()),
        why='there is nothing here I can pick up'),
    'inspect': Action('workbench', 60, 'examine one object, tree or plant closely',
        'take a close look at something'),
    'fell_tree': Action('woods', 5400, 'fell a standing tree with the axe; timber stays at the site',
        'fell a tree with my axe'),
    'eat': Action('cabin', 300, 'eat from an available food source',
        'eat something',
        impossible=lambda s: not foods.kinds(s) and s['provisions'].get('berries', 0) <= .001,
        why='there is nothing to eat: my food chest is empty and the bushes are bare'),
    'drink': Action('cabin', 120, 'drink from the spring',
        'drink at the spring'),
    'resume_work': Action('cabin', None, 'resume one of your paused jobs with its saved progress',
        'pick up something I left half-done',
        impossible=lambda s: not s['suspended_work'],
        why='I have nothing half-done to pick up'),
    'browse': Action('cafe', 900, 'use the terminal at the internet café to search the wider web and read pages',
        'search the web at the café'),
    'trade': Action('shop', 300, 'go to the trading post: buy, sell, do a posted job or a favour you agreed with Edda, or ask for something',
        'go to the trading post: buy, sell, work, or look at the ledger'),
    'talk': Action('shop', 600, 'talk with Edda Thorne, who keeps the trading post: chat, bargain, barter, ask or offer favours',
        'go and talk with Edda'),
    'use_item': Action('workbench', 300, 'use something you own, in whatever way you choose',
        'use one of my things',
        impossible=lambda s: not any(s.get('possessions', {}).values()),
        why='I have nothing of my own to use'),
    'interact': Action('workbench', 600, 'work material, divide or arrange solids, place things on surfaces, or sit or lie on something',
        'work with my hands: shape, split, stack, place, sit or lie on something'),
    'garden': Action('garden', 900, 'work at the garden beds beside the cabin',
        'work in my garden'),
    'plant_tree': Action('woods', 1200, 'plant a young tree you own somewhere in the woodland; it grows slowly over years',
        'plant a young tree',
        impossible=lambda s: not any(s.get('possessions', {}).get(k) for k in world_state.SAPLINGS),
        why='I have no young tree to plant'),
    'play_music': Action('cabin', 1800, 'sit and play the harp you own: make up a piece, change one of yours, play one again, or learn one from sheet music you have seen',
        'play my harp',
        impossible=lambda s: not s.get('possessions', {}).get('harp'),
        why='I have no harp'),
    'hunt': Action('woods', 7200, 'go out with the bow and arrows you own after an animal',
        'go out with my bow',
        impossible=lambda s: not (s.get('possessions', {}).get('hunting_bow') and s.get('possessions', {}).get('arrows')),
        why='I have no bow and arrows'),
    'butcher': Action('cabin', 10800, 'cut up the carcass beside the cabin with your knife',
        'cut up the carcass by my cabin',
        impossible=lambda s: not s.get('wildlife', {}).get('carcasses'),
        why='there is no carcass to cut up'),
    'preserve': Action('cabin', 14400, 'smoke fresh meat slowly over a wood fire so it keeps',
        'smoke meat over a slow fire',
        impossible=lambda s: 'venison' not in foods.kinds(s),
        why='I have no fresh meat to smoke'),
    'put_out_food': Action('woods', 2400, 'put a little of your food down somewhere outdoors and wait quietly nearby',
        'put a little food down outdoors and wait quietly',
        impossible=lambda s: not foods.kinds(s),
        why='I have no food to put out'),
    'notebook': Action('cabin', 900, 'write in or read back your notebook',
        'write in my notebook, or read it back'),
}

CHECK_ORDER = ['craft', 'resume_work', 'construct', 'move_object', 'use_item', 'plant_tree', 'hunt', 'butcher', 'preserve', 'put_out_food', 'eat', 'play_music']   # the order reasons have always been checked in


def unavailable(state):
    """What he might reach for that the world cannot do now, and why, in his words."""
    return {k: REGISTRY[k].why for k in CHECK_ORDER if REGISTRY[k].impossible(state)}


def places():
    return {k: a.place for k, a in REGISTRY.items()}


def durations():
    return {k: a.duration for k, a in REGISTRY.items() if a.duration is not None}


def menu():
    return {k: a.menu for k, a in REGISTRY.items()}


def choices():
    return {k: a.choice for k, a in REGISTRY.items()}
