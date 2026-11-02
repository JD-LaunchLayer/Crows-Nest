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
         'craft': 'making', 'construct': 'making', 'plan': 'making', 'garden': 'tending'}


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
    """His ongoing stories, as he would recall them (only those with more than one step)."""
    ensure(state)
    out = []
    for s in sorted(state['stories'], key=lambda s: -s.get('updated_hours', 0)):
        if s['count'] < 2 or s['stage'] in ('left',):
            continue
        out.append({'id': s['id'], 'story': s['title'], 'stage': s['stage'], 'steps': s['count'],
                    'last_step': s['steps'][-1]['text'][:140] if s['steps'] else '',
                    'feel': s.get('feel', {}).get('last')})
        if len(out) >= limit:
            break
    return out


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
