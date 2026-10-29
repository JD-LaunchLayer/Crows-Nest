"""Private, source-backed reading history. No model-generated world facts."""
import copy
import json
import re

CONTEXT_CHARS = 2500


def source_only(source):
    return {key: source.get(key, '') for key in ['query', 'title', 'url', 'text', 'retrieved']}


def ensure(state, root):
    """Recover older cached readings without inventing missing processing notes."""
    records = {record['id']: record for record in state.setdefault('reading_log', [])}
    memories = {memory['id']: memory for memory in state.get('memories', []) if 'source' in memory}
    sources = {key: memory['source'] for key, memory in memories.items()}
    for path in (root / 'crow-reading').glob('article-*.json'):
        match = re.fullmatch(r'article-(\d+)\.json', path.name)
        if not match or int(match[1]) in records:
            continue
        try:
            source = json.loads(path.read_text())
            if isinstance(source, dict) and isinstance(source.get('title'), str):
                sources.setdefault(int(match[1]), source)
        except (OSError, ValueError):
            continue  # Leave a damaged archive untouched; it is not a new experience.
    for memory_id, source in sources.items():
        if memory_id in records:
            continue
        saved = source.get('journal')
        if isinstance(saved, dict) and saved.get('id') == memory_id:
            records[memory_id] = copy.deepcopy(saved)
            continue
        memory = memories.get(memory_id, {})
        lesson = next((item.get('interpretation', '') for item in state.get('long_term', [])
                       if item.get('source_id') == memory_id), '')
        records[memory_id] = {
            'id': memory_id, 'at': memory.get('at') or source.get('retrieved', ''),
            'title': source.get('title', ''), 'url': source.get('url', ''),
            'query': source.get('query', ''), 'question': '', 'intention': '',
            'reason': memory.get('reason', ''), 'mode': 'legacy', 'status': 'legacy',
            'summary': '', 'lesson': lesson, 'answer_status': 'unknown',
            'next_step': '', 'processed_chars': 0,
        }
    state['reading_log'] = sorted(records.values(), key=lambda record: record['id'])


def save_article(root, source, record):
    folder = root / 'crow-reading'
    folder.mkdir(exist_ok=True)
    path = folder / f"article-{record['id']}.json"
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps({**source_only(source), 'journal': record}, indent=2, ensure_ascii=False))
    temp.replace(path)


def record_reading(state, memory, pending, root):
    source = pending['reading']
    decision = pending['decision']
    record = {
        'id': memory['id'], 'at': memory['at'], 'title': source['title'], 'url': source['url'],
        'query': source.get('query', ''), 'question': decision.get('research_question', '')[:240],
        'intention': decision.get('intention', '')[:300], 'reason': decision.get('reason', '')[:350],
        'mode': decision.get('reading_mode', 'lookup'), 'status': 'awaiting_note',
        'summary': '', 'lesson': '', 'answer_status': 'unknown',
        'next_step': decision.get('next_step', '')[:300], 'processed_chars': 0,
    }
    state.setdefault('reading_log', []).append(record)
    save_article(root, source, record)


def appraise(state, memory, result, root):
    record = next((record for record in state['reading_log'] if record['id'] == memory['id']), None)
    if record is None:
        return
    record.update(status='processed', summary=result.get('reading_summary', '')[:900],
                  lesson=result.get('lesson', '')[:350], answer_status=result.get('answer_status', 'unknown'),
                  next_step=result.get('next_step', '')[:300],
                  processed_chars=min(CONTEXT_CHARS, len(memory['source'].get('text', ''))))
    save_article(root, memory['source'], record)


def page(state, before=None, limit=20):
    records = state.get('reading_log', [])
    older = [record for record in records if before is None or record['id'] < before]
    return {'items': list(reversed(older[-limit:])), 'total': len(records), 'has_more': len(older) > limit}


def article(root, memory_id):
    """The HTTP handler supplies an integer, never a path from the client."""
    return json.loads((root / 'crow-reading' / f'article-{memory_id}.json').read_text())
