"""The shape of his ongoing life: stories, unfinished threads, promises, beliefs and how projects feel.

Inspired by what pinos.world publishes about Pino; implemented independently for Crow.
All of this is bookkeeping over what actually happened. It never chooses an action.

- Stories are pursuits that continue across sessions and days. Each finished
  activity joins the open story whose aim matches its intention (or starts a new
  one); a story with several steps is "pursuing", goes dormant when left alone,
  and is "answered" or "done" only on real evidence.
- Threads are things he noticed and left open at a place, in his own words.
- Promises are things he said he would do for Edda; he can later say he kept one.
- Beliefs are patterns computed by fixed rules from his own record (how activities
  tended to make him feel, and how often they worked out). They are worded from
  templates, have a status, and are revised when the record changes.
- Project feel tracks pull, grind and doubt across project sessions.
"""
import re

import memory_recall

STORY_MATCH = .4
DORMANT_HOURS = 72
LEFT_HOURS = 240


def ensure(state):
    for key in ('stories', 'threads', 'promises', 'beliefs'):
        state.setdefault(key, [])
    state.setdefault('next_story_id', 1)
    state.setdefault('next_thread_id', 1)
    state.setdefault('next_promise_id', 1)


def _hours(state):
    return state.get('body', {}).get('active_hours', 0.)


KINDS = {'read': 'looking', 'browse': 'looking', 'observe': 'looking', 'inspect': 'looking', 'talk': 'asking',
         'craft': 'making', 'construct': 'making', 'plan': 'making', 'interact': 'making', 'garden': 'tending', 'plant_tree': 'tending', 'play_music': 'making'}


def note_step(state, memory):
    """Attach a finished activity to the story it continues, or begin one."""
    ensure(state)
    intention = ' '.join(str(memory.get('intention', '')).split())
    if not intention or memory.get('kind') not in ('experience', None):
        return None
    hours = _hours(state)
    candidates = [s for s in state['stories'] if s['stage'] in ('started', 'pursuing', 'dormant')]
    best = None
    for s in candidates:
        if any(memory_recall.similar(v, intention, STORY_MATCH) for v in s['variants']):
            best = s if best is None or s['updated_hours'] > best['updated_hours'] else best
    if best is None:
        best = {'id': state['next_story_id'], 'title': intention[:140], 'kind': KINDS.get(memory.get('action'), 'doing'),
                'stage': 'started', 'started': memory.get('at', ''), 'variants': [intention[:200]], 'steps': [],
                'updated': memory.get('at', ''), 'updated_hours': hours}
        state['next_story_id'] += 1
        state['stories'].append(best)
    elif not any(v == intention[:200] for v in best['variants']):
        best['variants'] = (best['variants'] + [intention[:200]])[-6:]
    best['steps'].append({'at': memory.get('at', ''), 'event_id': memory.get('id'), 'action': memory.get('action'),
                          'text': str(memory.get('event', ''))[:220], 'because': str(memory.get('reason', ''))[:180]})
    if len(best['steps']) > 30:
        best['steps'] = best['steps'][:3] + best['steps'][-27:]
    best['count'] = best.get('count', 0) + 1
    best['updated'] = memory.get('at', '')
    best['updated_hours'] = hours
    if best['stage'] in ('started', 'dormant') and best['count'] >= 3:
        best['stage'] = 'pursuing'
    memory['story_id'] = best['id']
    # Keep the list bounded: single-step beginnings that went nowhere go first.
    while len(state['stories']) > 60:
        stale = next((s for s in state['stories'] if s['count'] <= 1 and s is not best), state['stories'][0])
        state['stories'].remove(stale)
    return best


def settle(state, memory, answer_status=None):
    """Evidence that ends a story: a source that answered its question, or a completed making milestone."""
    story = next((s for s in state.get('stories', []) if s['id'] == memory.get('story_id')), None)
    if not story:
        return
    if answer_status == 'answered':
        story['stage'] = 'answered'
        story['ended'] = memory.get('at', '')
    elif 'Completed the planned making/building milestone' in str(memory.get('event', '')):
        story['stage'] = 'done'
        story['ended'] = memory.get('at', '')


# A body need is answered by the body itself (v0.25.2): after drinking, eating or sleeping, if the body
# no longer reports that need, the story about easing it is done. Before, nothing could ever end these,
# so "drink at the spring first" stayed open and kept being followed after the thirst had gone.
NEEDS = {'drink': (('thirst', 'drink', 'spring'), ('thirst',)),
         'eat': (('hunger', 'hungry', 'eat', 'food', 'meal', 'provisions'), ('hunger',)),
         'sleep': (('sleep', 'sleepiness', 'sleepy', 'tired'), ('sleepiness', 'sleepy')),
         # Resting while a meal settles (v0.26.3): done once nothing is still digesting.
         'rest': (('digest', 'digesting', 'digestion', 'meal', 'eaten', 'eating'), ('digesting', 'full'))}
REST_WORDS = ('rest', 'settle', 'pause', 'quiet', 'quietly', 'stay', 'sit', 'wait')
# v0.36.3: lying down is resting too. "Lie back down under the covers and rest until it gets light" began with a word
# not on the list above, so it was never seen as a rest and stayed "in the middle of" for 109 steps over two days.
LYING_WORDS = ('lie', 'lying', 'lay', 'covers', 'bed', 'blanket', 'blankets')


def settle_need(state, memory, sensations):
    need = NEEDS.get(memory.get('action'))
    story = next((s for s in state.get('stories', []) if s['id'] == memory.get('story_id')), None)
    # A rest is a pause, not a pursuit (v0.27): a story that is only about resting is done once he has rested.
    if memory.get('action') in ('rest', 'sleep') and story and story['stage'] in ('started', 'pursuing', 'dormant'):
        words = re.findall(r'[a-z]+', story['title'].lower())
        # v0.36.4: anywhere in it, not only at the start ("Stop the notebook copy loop for tonight; rest in the cabin…"
        # ran 99 steps). Only ever closed when his last three steps were all rest or sleep, so he really has rested.
        restful = ((words[:1] and words[0] in REST_WORDS) or any(w in LYING_WORDS for w in words[:6])
                   or (len(story['steps']) >= 3 and any(w in REST_WORDS or w in LYING_WORDS for w in words)))
        if restful and all(st.get('action') in ('rest', 'sleep') for st in story['steps'][-3:]):
            story['stage'] = 'done'
            story['ended'] = memory.get('at', '')
            story['ended_by'] = 'he rested'
            return
    if not need or not story or story['stage'] not in ('started', 'pursuing', 'dormant'):
        return
    result = memory.get('world_result') if isinstance(memory.get('world_result'), dict) else {}
    if memory.get('action') == 'eat' and result.get('success') is False and re.search(r'empty|bare', str(result.get('text', ''))):
        # v0.30.12: a plan to eat what is no longer there ends when he finds nothing; it is not carried on as
        # something he is in the middle of (which kept telling him "the last bit of bread" was still waiting).
        story['stage'] = 'left'
        story['ended'] = memory.get('at', '')
        story['ended_by'] = 'there was nothing there to eat'
        return
    title = story['title'].lower()
    felt = ' '.join(sensations).lower()
    words = set(re.findall(r'[a-z]+', title))
    if words & set(need[0]) and not any(w in felt for w in need[1]):
        story['stage'] = 'done'
        story['ended'] = memory.get('at', '')
        story['ended_by'] = 'the body no longer reported the need'


PROMISE_LAPSE_DAYS = 5


def age(state):
    """Stories left alone go dormant, and eventually are counted as left behind.
    Promises not kept within about five days lapse (v0.28): kept in his history, no longer open."""
    from datetime import datetime
    try:
        today = datetime.fromisoformat(state['clock']['iso'])
        for p in state.get('promises', []):
            if p['status'] == 'open':
                try:
                    old = (today - datetime.fromisoformat(p['at'])).total_seconds() > PROMISE_LAPSE_DAYS * 86400
                except (ValueError, TypeError):
                    continue
                if old:
                    p.update(status='lapsed (left behind)', lapsed_at=today.isoformat())
    except (KeyError, ValueError, TypeError):
        pass
    now = _hours(state)
    for s in state.get('stories', []):
        idle = now - s.get('updated_hours', now)
        if s['stage'] in ('started', 'pursuing') and idle > DORMANT_HOURS:
            s['stage'] = 'dormant'
        elif s['stage'] == 'dormant' and idle > LEFT_HOURS:
            s['stage'] = 'left'


def context(state, limit=4):
    """All his ongoing stories side by side (those with more than one step, not yet left behind).

    Listed in the order they began, with no excerpt of the latest step, so the one he is
    in the middle of is not given extra prominence. If there are more than `limit`, the
    ones touched longest ago are left out, but the remainder stay in starting order."""
    ensure(state)
    now = _hours(state)
    live = [s for s in state['stories'] if s['count'] >= 2 and s['stage'] != 'left']
    kept = sorted(live, key=lambda s: -s.get('updated_hours', 0))[:limit]
    return [{'id': s['id'], 'story': s['title'], 'stage': s['stage'], 'steps': s['count'],
             'hours_since_last_step': round(max(0., now - s.get('updated_hours', now))),
             'feel': s.get('feel', {}).get('last')}
            for s in sorted(kept, key=lambda s: s['id'])]


def add_thread(state, text, place, source_id, at):
    ensure(state)
    text = ' '.join(str(text).split())[:200]
    import inner
    if not text or any(memory_recall.similar(t['text'], text) or inner.same_promise(t['text'], text)
                       for t in state['threads'] if t['status'] == 'open'):
        return None   # v0.30.21: the same open question reworded is the same question, not another one
    thread = {'id': state['next_thread_id'], 'text': text, 'place': place, 'at': at, 'source_id': source_id, 'status': 'open', **_phantom(text)}
    state['next_thread_id'] += 1
    state['threads'].append(thread)
    opened = [t for t in state['threads'] if t['status'] == 'open']
    if len(opened) > 12:
        opened[0]['status'] = 'faded'
    state['threads'] = state['threads'][-500:]  # v0.28.3: kept for the long run
    return thread


def follow_thread(state, ident, source_id, at):
    for t in state.get('threads', []):
        if t['id'] == ident and t['status'] == 'open':
            t.update(status='followed', followed_at=at, followed_by=source_id)
            return t
    return None


def add_promise(state, text, to, at):
    ensure(state)
    text = ' '.join(str(text).split())[:200]
    if not text:
        return None
    import inner
    same = next((p for p in reversed(state['promises']) if p['status'] == 'open' and p.get('to') == to and
                 (memory_recall.similar(p['text'], text) or inner.same_promise(p['text'], text))), None)
    if same:   # v0.30.5: saying the same promise again is the same promise, said again, not a new one
        same['times_said'] = same.get('times_said', 1) + 1
        same['last_said'] = at
        return same
    promise = {'id': state['next_promise_id'], 'text': text, 'to': to, 'at': at, 'status': 'open', **_phantom(text)}
    state['next_promise_id'] += 1
    state['promises'] = (state['promises'] + [promise])[-500:]  # v0.28.3: kept for the long run
    return promise


def work_done(state, job, at, only_before=False):
    """v0.36.10: when he has actually done a piece of posted work, his open promises to do that work and the stories
    that were about getting to it are settled by the fact, in the world's words; his own words are kept. Before, he
    swept the post at 08:39 and spent the rest of the day still meaning to "head to the trading post to start on the
    sweeping I owe Edda" (a story 142 steps long), and his promise to sweep stayed open."""
    import town
    names = {'sweep_post': 'the sweeping', 'carry_crates': 'carrying the crates'}
    kept = 0
    for p in state.get('promises', []):
        if p['status'] == 'open' and town.same_work(p['text']) == job and not (only_before and str(p.get('at', '')) >= at):
            p.update(status='kept (the work was done)', kept_at=at)
            kept += 1
    for st in state.get('stories', []):
        if st.get('stage') in ('started', 'pursuing', 'dormant') and town.same_work(st.get('title', '')) == job \
                and not (only_before and str(st.get('started', '')) >= at):
            st.update(stage='done', ended=at, ended_by=f'he did {names.get(job, "the work")}')
    return kept


TERMS_WORDS = ('terms', 'decide', 'decision', 'answer', 'agree', 'agreeing', 'hear', 'repeat', 'lay out', 'plainly')


def work_agreed(state, job, at):
    """v0.36.12: once a piece of work is agreed with Edda, his stories about hearing its terms or deciding on it are
    answered, and his promises to give an answer are kept. Before, he agreed the crate carrying and then spent a whole
    night at her counter asking for its terms "one more time", led on by those stories."""
    import town
    names = {'sweep_post': 'the sweeping', 'carry_crates': 'carrying the crates'}
    for st in state.get('stories', []):
        t = st.get('title', '').lower()
        if st.get('stage') in ('started', 'pursuing', 'dormant') and town.same_work(t) == job and any(w in t for w in TERMS_WORDS):
            st.update(stage='answered', ended=at, ended_by=f'he agreed {names.get(job, "the work")} with Edda')
    for p in state.get('promises', []):
        t = p['text'].lower()
        if p['status'] == 'open' and any(w in t for w in ('terms', 'answer', 'before i agree')) and (town.same_work(t) in (job, None)):
            p.update(status='kept (he gave his answer)', kept_at=at)


def settle_agreed_work(state):
    """Once (v0.36.12): favours already agreed and waiting settle the term-hearing stories and answer promises made before."""
    import town
    if state.get('agreed_work_settled'):
        return
    for f in town.keeper(state).get('favours', []):
        job = town.same_work(f.get('task', ''))
        if job:
            work_agreed(state, job, f.get('agreed', ''))
    state['agreed_work_settled'] = True


def settle_done_work(state):
    """Once (v0.36.10): work already done before this change settles the promises and plans made before it was done."""
    if state.get('done_work_settled'):
        return
    for job, at in (state.get('trading', {}).get('jobs_done') or {}).items():
        work_done(state, job, at, only_before=True)
    state['done_work_settled'] = True


# v0.36.15: a question he is still carrying is answered when he has checked and the record agrees,
# and it stays open when the record does not. His words are kept. Nothing here tells him what to do.
ACCOUNT_SETTLED = "the purse and the post's book agree, and the book shows nothing still owed"
FOOD_SETTLED = 'there is food in the chest'
HOME_SETTLED = 'he is at the cabin'
_ACCOUNT = re.compile(
    r"\b(debt|shortfall|discrepanc\w*|let it go|nothing is owed|payment on)\b"
    r"|\b(owe[ds]?|owing|gap|missing)\b.{0,48}\b(gold|silver|credits?|ledger|purse)\b"
    r"|\b(gold|silver|credits?)\b.{0,48}\b(owe[ds]?|owing|gap|missing|ledger|debt)\b",
    re.I)
_EMPTY = re.compile(
    r"\b(empty|nothing(?: left| to eat)?|no food|bare)\b.{0,40}\b(chest|provisions|larder)\b"
    r"|\b(chest|provisions|larder)\b.{0,40}\b(empty|bare|nothing)\b",
    re.I)
_HOME = re.compile(r"\b(head(?:ing)? home|go home|walk home|back home|return home|back to (?:the |my )?cabin)\b", re.I)
_OWED = ('nothing is owed', 'nothing owed', 'not owed', 'do not owe', "don't owe", 'no debt', 'none is owed')
_PURSE_CLAIM = re.compile(
    r"(?:you have|your purse(?: holds| has| is)?|ledger shows|i show)\s+"
    r"(\d+ gold(?: \d+ silver)?|\d+ silver|nothing)\b", re.I)


def _account_question(text):
    return bool(_ACCOUNT.search(str(text)))


def _books_agree(state):
    """His purse and the post's own book name the same sum, and the book shows nothing still owed.
    A price he paid is not a debt; only what the book itself records as short is."""
    import town
    post = state.get('trading') or {}
    purse = round(float(post.get('credit', 0) or 0), 2)
    recorded = None
    for line in reversed(post.get('ledger') or []):
        if line.get('credit_after') is not None:
            recorded = round(float(line['credit_after']), 2)
            break
    if recorded is None or abs(recorded - purse) >= .05:
        return False
    try:
        owed = town.post_owes(state)['total']
    except Exception:
        return False
    return owed <= .05


def _edda_text(memory):
    bits = []
    result = memory.get('world_result') if isinstance(memory.get('world_result'), dict) else {}
    for turn in result.get('conversation') or []:
        if turn.get('who') == 'Edda':
            bits.append(str(turn.get('text', '')))
    if not bits and 'Edda' in str(memory.get('event', '')):
        bits.append(str(memory.get('event', '')))
    return ' '.join(bits)


def _account_stance(state):
    """What her latest word on the account was, checked against the purse now. None if she has not spoken to it."""
    import town
    words = town.money(state.get('trading', {}).get('credit', 0)).lower()
    stance = None
    for memory in state.get('memories', []):
        text = _edda_text(memory)
        if not text:
            continue
        low = text.lower()
        claim = _PURSE_CLAIM.search(low)
        if claim and claim.group(1).lower() not in (words, 'nothing'):
            stance = 'contradicts'
        elif (claim and claim.group(1).lower() == words) or any(p in low for p in _OWED):
            stance = 'confirms'
    return stance


def _purse_count_matches(state):
    import town
    words = town.money(state.get('trading', {}).get('credit', 0))
    found = None
    for memory in state.get('memories', []):
        event = str(memory.get('event', ''))
        if 'Opened his purse and counted' in event:
            found = event
    return bool(found) and words in found


def _chest_has_food(state):
    import foods
    try:
        return sum(foods.view(state).values()) > .05
    except Exception:
        return False


def _mark_thread(item, at, why):
    item.update(status='followed', followed_at=at, settled_by=why)


def _mark_story(item, at, why):
    item.update(stage='answered', ended=at, ended_by=why)


def _mark_promise(item, at, why):
    item.update(status='kept (the record answered it)', kept_at=at, settled_by=why)


def settle_by_evidence(state, at=''):
    """v0.36.15: an open question is answered when a fresh look and the record agree, and reopened when they do not.

    His wording stays. A price he paid is not treated as money still owed. Nothing is removed from his history."""
    ensure(state)
    at = at or (state.get('clock') or {}).get('iso', '')
    agree = _books_agree(state)
    stance = _account_stance(state)
    counted = _purse_count_matches(state)
    account_ok = agree and counted and stance == 'confirms'
    fed = _chest_has_food(state)
    home = state.get('location') == 'cabin'
    for item in state.get('threads', []):
        text = item.get('text', '')
        why = item.get('settled_by')
        if _account_question(text):
            if item.get('status') == 'followed' and why == ACCOUNT_SETTLED and not account_ok:
                item['status'] = 'open'
            elif item.get('status') == 'open' and account_ok:
                _mark_thread(item, at, ACCOUNT_SETTLED)
        elif _EMPTY.search(text):
            if item.get('status') == 'followed' and why == FOOD_SETTLED and not fed:
                item['status'] = 'open'
            elif item.get('status') == 'open' and fed:
                _mark_thread(item, at, FOOD_SETTLED)
        elif _HOME.search(text) and not _account_question(text):
            if item.get('status') == 'open' and home:
                _mark_thread(item, at, HOME_SETTLED)
    for item in state.get('stories', []):
        text = ' '.join([item.get('title', '')] + item.get('variants', []))
        why = item.get('ended_by')
        open_ = item.get('stage') in ('started', 'pursuing', 'dormant')
        if _account_question(text):
            if item.get('stage') == 'answered' and why == ACCOUNT_SETTLED and not account_ok:
                item['stage'] = 'pursuing'
            elif open_ and account_ok:
                _mark_story(item, at, ACCOUNT_SETTLED)
        elif _EMPTY.search(text):
            if item.get('stage') == 'answered' and why == FOOD_SETTLED and not fed:
                item['stage'] = 'pursuing'
            elif open_ and fed:
                _mark_story(item, at, FOOD_SETTLED)
        elif _HOME.search(text):
            if open_ and home:
                _mark_story(item, at, HOME_SETTLED)
    for item in state.get('promises', []):
        text = item.get('text', '')
        why = item.get('settled_by')
        if not _account_question(text):
            continue
        if str(item.get('status', '')).startswith('kept') and why == ACCOUNT_SETTLED and not account_ok:
            item['status'] = 'open'
        elif item.get('status') == 'open' and account_ok:
            _mark_promise(item, at, ACCOUNT_SETTLED)
    return True


def keep_promise(state, ident, at):
    for p in state.get('promises', []):
        if p['id'] == ident and p['status'] == 'open':
            p.update(status='kept (his account)', kept_at=at)
            return p
    return None


def open_items(state):
    ensure(state)
    note = lambda x: {'note_from_the_world': x['world_note']} if x.get('world_note') else {}
    return {'threads': [{'id': t['id'], 'text': t['text'], 'place': t['place'], **note(t)} for t in state['threads'] if t['status'] == 'open'][-6:],
            'promises': [{'id': p['id'], 'text': p['text'], 'to': p['to'], **note(p)} for p in state['promises'] if p['status'] == 'open'][-6:]}


# Things the world told him wrongly, now put right (v0.27). His words are kept exactly; a plain note is added beside them.
PHANTOMS = [
    (('tam', 'cracked board', 'loose board', 'the board'), 'There is no Tam and no cracked or loose board at the trading post; '
     'Edda said those by mistake. She runs the post on her own.'),
    (('soup',), 'Edda has no soup or meal of her own to give; she spoke of one by mistake. Food at the post is what is on '
     'her shelves, at its price.'),
    (('solid part', 'solid-part'), 'There was never a "solid part" rule. That message came from a fault in the world when a '
     'blueprint drawing did not work; it has been put right, and drawing a blueprint needs no materials.'),
]


def _phantom(text):
    """The plain note from the world for anything new that rests on the same mistakes (v0.27.1)."""
    import re
    low = str(text).lower()
    notes = [n for words, n in PHANTOMS if any(re.search(r'\b' + re.escape(w) + r'\b', low) for w in words)]
    return {'world_note': ' '.join(notes)} if notes else {}


def leave_phantom_stories(state):
    """v0.36.6: stories that rest on something the world said by mistake (Edda's soup) are left, with the world's note
    beside them; his words stay exactly as he wrote them. Run once."""
    import re
    ensure(state)
    if state.get('phantom_stories_left'):
        return 0
    n = 0
    for st in state.get('stories', []):
        note = _phantom(' '.join([st.get('title', '')] + st.get('variants', []))).get('world_note')
        if note and st.get('stage') in ('started', 'pursuing', 'dormant'):
            st.update(stage='left', ended_by=note)
            n += 1
    for item in state['threads'] + state['promises']:
        if not item.get('world_note'):
            note = _phantom(item['text']).get('world_note')
            if note:
                item['world_note'] = note
    state['phantom_stories_left'] = True
    return n


def annotate_phantoms(state):
    """Once: add a plain note from the world beside threads and promises that rest on things the world got wrong."""
    import re
    ensure(state)
    if state.get('phantoms_annotated'):
        return 0
    marked = 0
    for item in state['threads'] + state['promises']:
        low = item['text'].lower()
        notes = [n for words, n in PHANTOMS if any(re.search(r'\b' + re.escape(w) + r'\b', low) for w in words)]
        if notes:
            item['world_note'] = ' '.join(notes)
            marked += 1
    state['phantoms_annotated'] = True
    return marked


# ---- Beliefs: patterns computed from his own record by fixed, published rules ----

PHRASE = {'eat': 'Eating', 'drink': 'Drinking at the spring', 'observe': 'Watching the woodland closely',
          'read': 'Looking things up at the library', 'browse': 'Searching the web at the café', 'craft': 'Carving',
          'rest': 'Resting', 'sleep': 'Sleeping', 'talk': 'Talking with Edda', 'trade': 'Trading at the post',
          'explore': 'Exploring the woodland', 'gather': 'Gathering materials', 'fell_tree': 'Felling trees',
          'construct': 'Building', 'plan': 'Planning things to build', 'inspect': 'Examining things closely',
          'reflect': 'Sitting and thinking', 'practise': 'Archery practice', 'use_item': 'Using my things',
          'garden': 'Working in the garden', 'move_object': 'Moving things around',
          'interact': 'Working with objects', 'plant_tree': 'Planting trees', 'play_music': 'Playing the harp'}
MIN_OBS = 4


def _feeling_words(mean):
    if mean > .15:
        return 'tends to lift me'
    if mean < -.15:
        return 'tends to leave me low'
    return 'leaves me much the same'


def _outcome_words(rate):
    if rate >= .8:
        return 'usually works out'
    if rate <= .4:
        return 'often does not work out'
    return None


def _set_belief(state, key, statement, n, recent_agree, at):
    beliefs = state['beliefs']
    current = next((b for b in beliefs if b['key'] == key and b['status'] in ('forming', 'held', 'doubted')), None)
    status = 'forming' if n < 6 else ('held' if recent_agree else 'doubted')
    if current and current['statement'] == statement:
        current.update(status=status, observations=n, updated=at)
        return
    if current:
        current.update(status='revised', until=at)
    beliefs.append({'key': key, 'statement': statement, 'status': status, 'observations': n, 'since': at, 'updated': at})
    state['beliefs'] = beliefs[-80:]


def update_beliefs(state, at):
    """Recompute patterns from the last 400 appraisals and their events. Rules:
    - feeling: mean appraisal valence per activity over at least 4 occasions;
    - outcome: share of occasions whose world result succeeded, over at least 4;
    - 'held' needs 6+ occasions with the last three agreeing; otherwise 'doubted';
      a changed pattern revises the old statement, which stays visible."""
    ensure(state)
    events = {m['id']: m for m in state.get('memories', [])}
    by_action = {}
    for a in state.get('appraisals', [])[-400:]:
        if a.get('stand_in'):
            continue  # v0.30: hours lived by the stand-in mind do not shape his patterns
        m = events.get(a.get('source_id'))
        if not m or m.get('action') not in PHRASE:
            continue
        result = m.get('world_result') if isinstance(m.get('world_result'), dict) else {}
        if m['action'] in ('eat', 'drink') and result.get('success') is False:
            continue  # v0.30.8: finding the chest empty is not eating; it says nothing about how eating leaves him
        by_action.setdefault(m['action'], []).append((float(a.get('valence') or 0), result.get('success')))
    for action, obs in by_action.items():
        if len(obs) < MIN_OBS:
            continue
        mean = sum(v for v, _ in obs) / len(obs)
        words = _feeling_words(mean)
        recent = [_feeling_words(v) == words for v, _ in obs[-3:]]
        _set_belief(state, 'feel:' + action, f'{PHRASE[action]} {words}.', len(obs), sum(recent) >= 2, at)
        outcomes = [ok for _, ok in obs if isinstance(ok, bool)]
        if len(outcomes) >= MIN_OBS:
            words2 = _outcome_words(sum(outcomes) / len(outcomes))
            if words2:
                agree = [(ok if words2 == 'usually works out' else not ok) for ok in outcomes[-3:]]
                _set_belief(state, 'work:' + action, f'{PHRASE[action]} {words2}.', len(outcomes), sum(agree) >= 2, at)


def belief_context(state, limit=6):
    return [{'pattern': b['statement'], 'status': b['status'], 'seen': b['observations']}
            for b in state.get('beliefs', []) if b['status'] in ('held', 'doubted', 'forming')][-limit:]


# ---- How work feels: pull, grind and doubt, from his own appraisals of each session ----

EFFORTFUL = {'plant_tree', 'craft', 'construct', 'interact', 'gather', 'fell_tree', 'trade', 'garden', 'practise', 'explore', 'move_object'}


def felt(memory, valence, answer_status=None):
    result = memory.get('world_result') if isinstance(memory.get('world_result'), dict) else {}
    trial = result.get('trial') or {}
    if (trial and trial.get('goal_met') is False) or answer_status == 'not_answered' or result.get('success') is False:
        return 'doubt'
    if valence > .15:
        return 'pull'
    if valence <= .05 and memory.get('action') in EFFORTFUL:
        return 'grind'
    return 'neutral'


def _add_feel(record, kind):
    feel = record.setdefault('feel', {'pull': 0., 'grind': 0., 'doubt': 0., 'sessions': 0, 'last': None})
    for k in ('pull', 'grind', 'doubt'):
        feel[k] = round(feel[k] * .85, 3)
    if kind in ('pull', 'grind', 'doubt'):
        feel[kind] = round(feel[kind] + 1, 3)
    feel['sessions'] += 1
    feel['last'] = kind
    strongest = max(('pull', 'grind', 'doubt'), key=lambda k: feel[k])
    feel['mostly'] = strongest if feel[strongest] >= 1 else None


def record_feel(state, memory, valence, answer_status=None):
    """Attach how this session felt to its story and, if it counted towards one, its project."""
    kind = felt(memory, valence, answer_status)
    for s in state.get('stories', []):
        if s['id'] == memory.get('story_id'):
            _add_feel(s, kind)
    for p in state.get('projects', []):
        if p['id'] == memory.get('project_id'):
            _add_feel(p, kind)
    return kind
