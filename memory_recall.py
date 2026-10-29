"""Relevance-ranked recall from Crow's saved life, within a protected budget.

Retrieval decides what evidence reaches a decision. It does not decide the
decision. Every item keeps its saved source ID and a label separating what
happened (event), what was read (reading), what he concluded (lesson), how he
appraised something (appraisal) and what was measured (trial). Nothing here
adds, rewrites or deletes saved history.

Scoring is deliberately simple and auditable: rare shared words between the
current situation and an item (IDF-weighted), plus a small bonus for
importance he reported and a small recency bonus. It is keyword relevance, not
semantic embedding search, so paraphrases with no shared words can still be
missed.
"""
import json
import math
import re

STOP = set('''that this with from have were what when where which while about into your their there them then than
been being also some more most very just only over such does done made make makes them they these those would could
should will shall after before again because other another each every same still even much many like want wanted
understand understanding finished session started crow time feel felt think thought trying tried''' .split())


def words(text):
    found = set()
    for w in re.findall(r'[a-z]{4,}', str(text).lower()):
        if w in STOP:
            continue
        for suffix in ('ings', 'ing', 'ies', 'ed', 'es', 's'):
            if w.endswith(suffix) and len(w) - len(suffix) >= 4:
                w = w[:-len(suffix)]
                break
        if w.endswith('e') and len(w) > 4:
            w = w[:-1]  # carve/carving, stone/stones share a stem
        found.add(w)
    return found


def _short(text, limit):
    text = ' '.join(str(text or '').split())
    return text if len(text) <= limit else text[:limit - 1] + '…'


def candidates(state):
    """Every recallable item, labelled by evidence type. Nothing is generated."""
    items = []
    for m in state.get('memories', []):
        if m.get('kind') in ('started', 'resumed'):
            continue  # "Started X." carries little; its outcome event is recalled instead.
        items.append({'type': 'event', 'id': m.get('id'), 'order': m.get('id') or 0,
                      'text': _short(m.get('event'), 220), 'why': _short(m.get('reason'), 120),
                      'when': m.get('at', '')[:16], 'importance': 0})
        found = (m.get('world_result') or {}).get('findings') or []
        for f in found:  # each thing he actually noticed is recallable on its own
            items.append({'type': 'observed', 'id': m.get('id'), 'order': m.get('id') or 0,
                          'text': _short(f.get('text'), 200), 'why': _short(m.get('intention'), 100),
                          'when': m.get('at', '')[:16], 'importance': .2})
    for x in state.get('long_term', []):
        items.append({'type': 'lesson', 'id': x.get('source_id'), 'order': x.get('source_id') or 0,
                      'text': _short(x.get('interpretation'), 220), 'why': _short(x.get('fact'), 120),
                      'when': x.get('at', '')[:16], 'importance': .3})
    for a in state.get('appraisals', []):
        if not a.get('meaning'):
            continue
        items.append({'type': 'appraisal', 'id': a.get('source_id'), 'order': a.get('source_id') or 0,
                      'text': _short(a.get('meaning'), 200), 'why': _short(a.get('concern'), 100),
                      'when': a.get('at', '')[:16], 'importance': float(a.get('importance') or 0)})
    for r in state.get('reading_log', []):
        if r.get('status') != 'processed':
            continue
        items.append({'type': 'reading', 'id': r.get('id'), 'order': r.get('id') or 0,
                      'text': _short(f"{r.get('title')}: {r.get('summary')}", 220),
                      'why': _short(f"question: {r.get('question')} ({r.get('answer_status')})", 140),
                      'when': r.get('at', '')[:16], 'importance': .1})
    for t in state.get('practical', {}).get('trials', []):
        items.append({'type': 'trial', 'id': t.get('source_id'), 'order': t.get('source_id') or 0,
                      'text': _short(f"{t.get('shape')} with {t.get('method_id')}: error {t.get('actual_error_mm')} mm, "
                                     f"tolerance {t.get('target_error_mm')} mm, {'met' if t.get('goal_met') else 'missed'}. "
                                     f"{t.get('adjustment') or ''}", 220),
                      'why': _short(t.get('hypothesis'), 120), 'when': t.get('at', '')[:16], 'importance': .3})
    for i, f in enumerate(state.get('research_feedback', [])):
        items.append({'type': 'search_miss', 'id': None, 'order': 0,
                      'text': _short(f"Search '{f.get('query')}' found nothing relevant: {f.get('reason')}", 200),
                      'why': _short(f.get('question'), 120), 'when': '', 'importance': .1})
    return items


def query_terms(state):
    """What Crow is currently concerned with, taken only from his own saved state.

    His own intention, next step and active project count fully; the last few
    events count less, so a run of similar recent events cannot dominate recall.
    """
    terms = {}
    focus = [state.get('current_intention', ''), state.get('next_step', '')]
    focus += [p.get('title', '') for p in state.get('projects', []) if p.get('status') == 'active']
    pending = state.get('pending') or {}
    if pending.get('decision'):
        focus.append(pending['decision'].get('intention', ''))
    for w in words(' '.join(str(x) for x in focus)):
        terms[w] = 1.0
    for m in state.get('memories', [])[-3:]:
        for w in words(m.get('event', '')):
            terms.setdefault(w, .35)
    return terms


def recall(state, budget_chars=1700, exclude_ids=(), limit=8):
    """Return the most relevant saved items that fit in budget_chars of JSON.

    Recent events are supplied separately, so their IDs can be excluded here.
    Identical texts are recalled once with a count, which shows repetition
    without spending the budget on duplicates.
    """
    items = candidates(state)
    if not items:
        return []
    query = query_terms(state)
    exclude = set(exclude_ids)
    docs = [words(i['text'] + ' ' + i['why']) for i in items]
    df = {}
    for d in docs:
        for w in d:
            df[w] = df.get(w, 0) + 1
    n = len(items)
    newest = max((i['order'] for i in items), default=0) or 1
    scored = []
    for item, d in zip(items, docs):
        if item['type'] == 'event' and item['id'] in exclude:
            continue
        overlap = sum(query[w] * math.log(1 + n / df[w]) for w in d & query.keys())
        if overlap <= 0:
            continue
        recency = .5 * (item['order'] / newest) if item['order'] else 0
        scored.append((overlap + item['importance'] + recency, item))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    chosen, seen, used, per_type = [], {}, 2, {}
    out_terms = {}

    def _near_duplicate(terms, seen):
        # Reworded versions of the same note (e.g. repeated "did not answer my question") count once.
        for k, other in out_terms.items():
            if terms and other and len(terms & other) / len(terms | other) >= .5:
                return seen[k]
        return None
    for score, item in scored:
        if per_type.get(item['type'], 0) >= max(2, limit // 3):
            continue  # keep several kinds of evidence visible rather than one flooded kind
        key = re.sub(r'\W+', ' ', item['text'].casefold()).strip()
        twin = seen.get(key) or _near_duplicate(words(item['text']), seen)
        if twin:
            twin['times_recorded'] = twin.get('times_recorded', 1) + 1
            continue
        out = {k: item[k] for k in ('type', 'id', 'when', 'text', 'why') if item[k] not in (None, '')}
        size = len(json.dumps(out, ensure_ascii=False)) + 25
        if used + size > budget_chars:
            continue
        used += size
        seen[key] = out
        out_terms[key] = words(item['text'])
        per_type[item['type']] = per_type.get(item['type'], 0) + 1
        chosen.append(out)
        if len(chosen) >= limit:
            break
    return chosen


def recent_pattern(state, window=12):
    """Factual counts of recent choices, so a lack of progress is observable.

    This is an observation, not a nudge: no threshold triggers any action.
    """
    started = [m for m in state.get('memories', []) if m.get('kind') == 'started'][-window:]
    actions = {}
    for m in started:
        a = m.get('action') or '?'
        actions[a] = actions.get(a, 0) + 1
    streak, current = 0, (state.get('current_intention') or '').casefold().strip()
    for m in reversed(started):
        if current and (m.get('intention') or '').casefold().strip() == current:
            streak += 1
        else:
            break
    log = state.get('reading_log', [])[-window:]
    unanswered = sum(1 for r in log if r.get('answer_status') == 'not_answered')
    repeats = sum(1 for r in log if r.get('new_source_text') is False)
    return {'last_choices': actions, 'decisions_with_current_intention': streak,
            'recent_readings': len(log), 'readings_not_answering': unanswered, 'repeated_excerpts': repeats}
