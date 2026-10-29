"""Sleep-time memory consolidation: a finite, competitive, revisable mind.

Adapted from the approach described for Pino (pinos.world), with Crow-specific
choices. While Crow sleeps, the model rereads that day's actual experiences
against what he already holds and returns new memories, revisions of old ones,
reinforcements and contradictions. The executor here, not the model, decides
what is admitted, using fixed, auditable rules:

- Three sections of at most 24 entries each: `life` (what mattered, beliefs
  about himself and his world), `skills` (how to do things) and `world` (what
  the world has shown him is possible or impossible).
- Every entry must cite at least one real event from the day, or revise an
  entry he already holds. Ungrounded text is discarded.
- Strength fades by half every three weeks of active life unless something
  reinforces it. Paused or closed time does not fade memories.
- A full section only admits a new memory that is stronger than its weakest
  entry, which is then forgotten. Forgotten entries are kept in a visible
  archive, never silently deleted.
- Topic ceilings, with no banned-topic list: one content word may appear in at
  most four entries of a section, and one pair of content words in at most two.
- A revision replaces the wording but keeps the earlier wording in `previous`.

The raw event log and the per-event lessons are untouched; this is a separate,
consolidated view that decisions can draw on. None of this chooses what Crow
does next.
"""
import contextlib
import itertools
import math

import memory_recall

SECTIONS = {
    'life': 'things that mattered to you, and what you now believe about yourself and your world',
    'skills': 'how to do things, as your own attempts have shown (methods, mistakes, what worked)',
    'world': 'what the world has shown you is possible, impossible, available or scarce',
}
CAPACITY = 24
HALF_LIFE_HOURS = 21 * 24
WORD_CEILING = 4
DIGEST_BUDGET = 2000  # crow.py widens this when a larger cloud model is in use
PAIR_CEILING = 2


def ensure(state):
    mind = state.setdefault('mind', {})
    for name in SECTIONS:
        mind.setdefault(name, [])
    mind.setdefault('forgotten', [])
    mind.setdefault('next_id', 1)
    mind.setdefault('last_event_id', 0)
    mind.setdefault('last_active_hours', state.get('body', {}).get('active_hours', 0.))
    mind.setdefault('nights', 0)
    return mind


def fade(state):
    """Apply decay for active hours since the last consolidation."""
    mind = ensure(state)
    now_hours = state.get('body', {}).get('active_hours', 0.)
    elapsed = max(0., now_hours - mind['last_active_hours'])
    factor = 0.5 ** (elapsed / HALF_LIFE_HOURS)
    for name in SECTIONS:
        for entry in mind[name]:
            entry['strength'] = round(entry['strength'] * factor, 4)
    mind['last_active_hours'] = now_hours


def day_digest(state, budget=None):
    """The day's actual experiences since the last consolidation, most salient first."""
    budget = budget or DIGEST_BUDGET
    mind = ensure(state)
    appraisal = {a['source_id']: a for a in state.get('appraisals', [])}
    items = []
    for m in state.get('memories', []):
        if m['id'] <= mind['last_event_id'] or m.get('kind') in ('started', 'resumed', 'consolidated'):
            continue
        a = appraisal.get(m['id'], {})
        weight = float(a.get('importance') or 0) + (.3 if m.get('world_result', {}).get('trial') else 0)
        weight += .2 if m.get('new_evidence', True) and m.get('new_source_text', True) else -.3
        text = m['event'][:200]
        if a.get('meaning'):
            text += ' | meant: ' + a['meaning'][:120]
        items.append((weight, m['id'], text))
    items.sort(key=lambda x: (-x[0], x[1]))
    chosen, used = [], 0
    for weight, ident, text in items:
        if used + len(text) + 12 > budget:
            continue
        used += len(text) + 12
        chosen.append({'id': ident, 'event': text})
    return sorted(chosen, key=lambda x: x['id'])


def _content(text):
    return memory_recall.words(text)


def _violates_ceiling(entries, text, ignore_id=None):
    """True if adding text would let one word own >4 entries or one word pair own >2."""
    new = _content(text)
    others = [_content(e['text']) for e in entries if e['id'] != ignore_id]
    for w in new:
        if sum(w in o for o in others) + 1 > WORD_CEILING:
            return f'the word "{w}" already anchors {WORD_CEILING} memories'
    for a, b in itertools.combinations(sorted(new), 2):
        if sum(a in o and b in o for o in others) + 1 > PAIR_CEILING:
            return f'the idea "{a} + {b}" already anchors {PAIR_CEILING} memories'
    return None


def apply(state, section, result, digest_ids, at):
    """Admit the model's proposals under the fixed rules. Returns a report of what happened."""
    mind = ensure(state)
    entries = mind[section]
    by_id = {e['id']: e for e in entries}
    report = {'added': [], 'revised': [], 'reinforced': [], 'contested': [], 'forgotten': [], 'refused': []}
    for ident in result.get('reinforced_ids', [])[:8]:
        if ident in by_id:
            e = by_id[ident]
            e['strength'] = round(min(1.5, e['strength'] + .3), 4)
            e['reinforced'] = at
            report['reinforced'].append(ident)
    for ident in result.get('contradicted_ids', [])[:8]:
        if ident in by_id:
            e = by_id[ident]
            e['strength'] = round(e['strength'] * .5, 4)
            e['contested'] = at
            report['contested'].append(ident)
    for proposal in result.get('memories', [])[:5]:
        text = ' '.join(str(proposal.get('text', '')).split())[:220]
        evidence = [i for i in proposal.get('evidence_ids', []) if i in digest_ids][:4]
        revises = proposal.get('revises', 0)
        importance = proposal.get('importance', .5)
        if not isinstance(importance, (int, float)) or not math.isfinite(importance):
            importance = .5
        importance = max(0., min(1., importance))
        if len(text) < 8:
            continue
        if revises in by_id:
            old = by_id[revises]
            why = _violates_ceiling(entries, text, ignore_id=revises)
            if why:
                report['refused'].append({'text': text, 'why': why})
                continue
            if not evidence:
                report['refused'].append({'text': text, 'why': 'no event from today was cited for the revision'})
                continue
            old.setdefault('previous', []).append({'text': old['text'], 'until': at})
            old['previous'] = old['previous'][-5:]
            old.update(text=text, revised=at, strength=round(max(old['strength'], .5 + .5 * importance), 4))
            old['evidence'] = (old.get('evidence', []) + evidence)[-8:]
            report['revised'].append(revises)
            continue
        if not evidence:
            report['refused'].append({'text': text, 'why': 'no event from today was cited'})
            continue
        if any(memory_recall.similar(e['text'], text) for e in entries):
            twin = next(e for e in entries if memory_recall.similar(e['text'], text))
            twin['strength'] = round(min(1.5, twin['strength'] + .2), 4)
            report['reinforced'].append(twin['id'])
            continue
        why = _violates_ceiling(entries, text)
        if why:
            report['refused'].append({'text': text, 'why': why})
            continue
        strength = round(.5 + .5 * importance, 4)
        if len(entries) >= CAPACITY:
            weakest = min(entries, key=lambda e: e['strength'])
            if weakest['strength'] >= strength:
                report['refused'].append({'text': text, 'why': 'not stronger than anything already held'})
                continue
            entries.remove(weakest)
            mind['forgotten'].append({**weakest, 'section': section, 'forgotten': at})
            mind['forgotten'] = mind['forgotten'][-200:]
            report['forgotten'].append(weakest['id'])
        entry = {'id': mind['next_id'], 'text': text, 'strength': strength, 'created': at, 'evidence': evidence}
        mind['next_id'] += 1
        entries.append(entry)
        by_id[entry['id']] = entry
        report['added'].append(entry['id'])
    return report


def schema(section_ids, digest_ids):
    integer_ids = {'type': 'integer', 'enum': section_ids or [0]}
    return {'type': 'object', 'additionalProperties': False,
            'required': ['memories', 'reinforced_ids', 'contradicted_ids'],
            'properties': {
                'memories': {'type': 'array', 'maxItems': 5, 'items': {
                    'type': 'object', 'additionalProperties': False,
                    'required': ['text', 'revises', 'evidence_ids', 'importance'],
                    'properties': {'text': {'type': 'string'},
                                   'revises': {'type': 'integer', 'enum': [0] + section_ids},
                                   'evidence_ids': {'type': 'array', 'maxItems': 4,
                                                    'items': {'type': 'integer', 'enum': digest_ids or [0]}},
                                   'importance': {'type': 'number', 'minimum': 0, 'maximum': 1}}}},
                'reinforced_ids': {'type': 'array', 'maxItems': 8, 'items': integer_ids},
                'contradicted_ids': {'type': 'array', 'maxItems': 8, 'items': integer_ids}}}


def prompt(section, entries, digest):
    held = [{'id': e['id'], 'text': e['text'][:160], 'strength': round(e['strength'], 2)} for e in entries]
    return ('You are asleep, consolidating memory. Below is what actually happened since you last slept, and what you '
            f'currently hold about {SECTIONS[section]}. Space is limited to {CAPACITY} memories; weaker ones fade and can be lost. '
            'Return only what is worth carrying in this section: new memories (each citing evidence_ids of today\'s events), '
            'revisions (revises = the id of a held memory whose wording today\'s events change), held ids today reinforced, and '
            'held ids today contradicted. Fewer, sharper memories are better than many. Do not restate a held memory in new '
            'words; reinforce it instead. Nothing new is a valid result. Do not record what you did not experience, and do not '
            'turn an absence of information into an insight. '
            + 'TODAY: ' + str(digest) + ' HELD: ' + str(held))


def consolidate(state, model_call, at, lock=None):
    """Run one consolidation over all sections. model_call(prompt, schema, limit, purpose) -> (dict, seconds).

    Model calls happen outside `lock`; changes to state are applied inside it."""
    lock = lock or contextlib.nullcontext()
    with lock:
        mind = ensure(state)
        fade(state)
        digest = day_digest(state)
        sections = {name: [dict(e) for e in mind[name]] for name in SECTIONS}
    if not digest:
        return None
    ids = [d['id'] for d in digest]
    results = {}
    for section, entries in sections.items():
        result, _ = model_call(prompt(section, entries, digest), schema([e['id'] for e in entries], ids), 600,
                               'consolidate:' + section)
        if not isinstance(result, dict):
            raise ValueError('Invalid consolidation result')
        results[section] = result
    with lock:
        reports = {section: apply(state, section, result, set(ids), at) for section, result in results.items()}
        mind['last_event_id'] = max(ids)
        mind['nights'] += 1
    return reports


def recall_items(state):
    """Consolidated memories as recall candidates, weighted by strength."""
    mind = ensure(state)
    return [{'type': 'held_' + section, 'id': None, 'order': 0, 'text': e['text'][:220],
             'why': f"strength {round(e['strength'], 2)}", 'when': (e.get('revised') or e.get('created', ''))[:16],
             'importance': .4 + .4 * min(1., e['strength'])}
            for section in SECTIONS for e in mind[section]]


def strongest(state, n=3):
    mind = ensure(state)
    held = [(e['strength'], section, e['text']) for section in SECTIONS for e in mind[section]]
    return [f"{text[:160]} ({section})" for _, section, text in sorted(held, reverse=True)[:n]]


def summary(reports):
    counts = {k: sum(len(r[k]) for r in reports.values()) for k in ('added', 'revised', 'reinforced', 'contested', 'forgotten', 'refused')}
    return ('Slept on the day. Memory consolidation: ' +
            ', '.join(f'{n} {k}' for k, n in counts.items()) + '.'), counts
