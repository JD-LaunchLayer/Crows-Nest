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
         'craft': 'making', 'construct': 'making', 'plan': 'making', 'interact': 'making', 'garden': 'tending', 'plant_tree': 'tending'}


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


def age(state):
    """Stories left alone go dormant, and eventually are counted as left behind."""
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
    if not text or any(memory_recall.similar(t['text'], text) for t in state['threads'] if t['status'] == 'open'):
        return None
    thread = {'id': state['next_thread_id'], 'text': text, 'place': place, 'at': at, 'source_id': source_id, 'status': 'open'}
    state['next_thread_id'] += 1
    state['threads'].append(thread)
    opened = [t for t in state['threads'] if t['status'] == 'open']
    if len(opened) > 12:
        opened[0]['status'] = 'faded'
    state['threads'] = state['threads'][-80:]
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
    promise = {'id': state['next_promise_id'], 'text': text, 'to': to, 'at': at, 'status': 'open'}
    state['next_promise_id'] += 1
    state['promises'] = (state['promises'] + [promise])[-40:]
    return promise


def keep_promise(state, ident, at):
    for p in state.get('promises', []):
        if p['id'] == ident and p['status'] == 'open':
            p.update(status='kept (his account)', kept_at=at)
            return p
    return None


def open_items(state):
    ensure(state)
    return {'threads': [{'id': t['id'], 'text': t['text'], 'place': t['place']} for t in state['threads'] if t['status'] == 'open'][-6:],
            'promises': [{'id': p['id'], 'text': p['text'], 'to': p['to']} for p in state['promises'] if p['status'] == 'open'][-6:]}


# ---- Beliefs: patterns computed from his own record by fixed, published rules ----

PHRASE = {'eat': 'Eating', 'drink': 'Drinking at the spring', 'observe': 'Watching the woodland closely',
          'read': 'Looking things up at the library', 'browse': 'Searching the web at the café', 'craft': 'Carving',
          'rest': 'Resting', 'sleep': 'Sleeping', 'talk': 'Talking with Edda', 'trade': 'Trading at the post',
          'explore': 'Exploring the woodland', 'gather': 'Gathering materials', 'fell_tree': 'Felling trees',
          'construct': 'Building', 'plan': 'Planning things to build', 'inspect': 'Examining things closely',
          'reflect': 'Sitting and thinking', 'practise': 'Archery practice', 'use_item': 'Using my things',
          'garden': 'Working in the garden', 'move_object': 'Moving things around',
          'interact': 'Working with objects', 'plant_tree': 'Planting trees'}
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
        m = events.get(a.get('source_id'))
        if not m or m.get('action') not in PHRASE:
            continue
        result = m.get('world_result') if isinstance(m.get('world_result'), dict) else {}
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
