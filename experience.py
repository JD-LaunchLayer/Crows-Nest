"""Evidence for developing interests, kept separately from legacy preference scores.

No counters here choose an action or declare a passion. A reported feeling, an
observed return and a successful physical outcome are different kinds of evidence.
Old scores are preserved without inventing the experiences that produced them.
"""
import copy
import memory_recall


def ensure(state):
    return state.setdefault('interest_history', {})


def record(state, memory, appraisal):
    history = ensure(state)
    topic = str(appraisal.get('topic') or '').strip().lower()[:60]
    if not topic:
        return
    topic = next((t for t in history if memory_recall.similar(t, topic)), topic)
    entry = history.setdefault(topic, {'topic': topic, 'episodes': []})
    if any(e['source_id'] == memory['id'] for e in entry['episodes']):
        return
    result = memory.get('world_result') or {}
    entry['episodes'].append({
        'source_id': memory['id'], 'at': memory.get('at', ''),
        'action': memory.get('action', ''), 'intention': memory.get('intention', '')[:180],
        'feeling': appraisal.get('feeling', '')[:200],
        'enjoyment': appraisal.get('enjoyment', 0),
        'fresh': memory.get('new_evidence', True) and memory.get('new_source_text', True),
        'physical_success': result.get('success') if memory.get('action') in
            ('craft', 'construct', 'interact', 'gather', 'fell_tree', 'move_object', 'use_item') else None,
        'choice_id': memory.get('choice_id'),
        'object_id': result.get('object_id'),
    })
    # Full experiences remain in the ordinary event log. This bounded index is
    # for decisions/observer inspection and does not erase the original history.
    entry['episodes'] = entry['episodes'][-80:]
    if len(history) > 48:
        oldest = min(history, key=lambda t: history[t]['episodes'][-1]['source_id'])
        del history[oldest]


def summary(state, limit=4):
    """Evidence, not a ranking of what Crow ought to enjoy. Latest topics first."""
    rows = []
    for topic, entry in state.get('interest_history', {}).items():
        es = entry['episodes']
        if not es:
            continue
        choices = {e['choice_id'] for e in es if e.get('choice_id') is not None}
        fresh = [e for e in es if e['fresh']]
        recent = es[-3:]
        rows.append({'topic': topic, 'episodes': len(es), 'separate_choices': len(choices),
            'fresh_experiences': len(fresh), 'recent_enjoyment': [e['enjoyment'] for e in recent],
            'physical_successes': sum(e['physical_success'] is True for e in es),
            'physical_failures': sum(e['physical_success'] is False for e in es),
            'latest_feeling': recent[-1]['feeling'][:120],
            'evidence_ids': [e['source_id'] for e in recent]})
    rows.sort(key=lambda r: r['evidence_ids'][-1], reverse=True)
    return rows[:limit]


def report(state):
    """Read-only multi-day behaviour measures. Counts are not an autonomy score."""
    events = state.get('memories', [])
    started = [m for m in events if m.get('kind') == 'started']
    days = sorted({m.get('at', '')[:10] for m in events if m.get('at')})
    choices = {}
    for m in started:
        day = m.get('at', '')[:10] or 'undated'
        row = choices.setdefault(day, {'choices': 0, 'actions': {}, 'cited_memory': 0})
        row['choices'] += 1
        action = m.get('action', '?')
        row['actions'][action] = row['actions'].get(action, 0) + 1
        row['cited_memory'] += bool(m.get('memory_ids_used'))
    attempts = state.get('procedures', {}).get('attempts', [])
    progress=[]
    for method in state.get('procedures',{}).get('methods',[]):
        measured=[a['measurements']['width_error_mm'] for a in attempts
                  if a['method_id']==method['id'] and 'width_error_mm' in a.get('measurements',{})]
        if len(measured)>1:progress.append({'method_id':method['id'],'measured_attempts':len(measured),
                                           'first_error_mm':measured[0],'latest_error_mm':measured[-1]})
    return {'coverage': 'saved history window; full event log is separate', 'dates': days,
        'by_day': choices, 'interests': summary(state, 48),
        'physical_attempts': len(attempts),
        'failed_attempts': sum(not a['success'] for a in attempts),
        'method_reuses': sum(a.get('reused', False) for a in attempts),
        'object_changes': sum(bool(a.get('changed_ids')) for a in attempts),
        'measured_method_changes':progress,
        'carving_trials':len(state.get('practical',{}).get('trials',[])),
        'world_objects_present':sum(bool(o.get('parts')) for o in state.get('built_world',{}).get('objects',{}).values()),
        'reading_repeats': sum(r.get('new_source_text') is False for r in state.get('reading_log', [])),
        'methods': copy.deepcopy(state.get('procedures', {}).get('methods', []))}
