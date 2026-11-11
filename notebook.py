"""His notebook (v0.29.1): somewhere to write things down in his own words, and read them back.

An ordinary possession, like his purse. Nothing tells him to write or what to write. It starts
empty: before this he had nowhere to write, so anything he thought he had "written" was only
remembered. Pages are kept for good and can be read back by a word, a day, or their page number.
"""
import re

KEEP = 2000


def ensure(state):
    return state.setdefault('notebook', [])


def write(state, title, text, at):
    pages = ensure(state)
    # Keep his line breaks (v0.29.2): before, everything was run together, so separate lines could never be written.
    text = '\n'.join(' '.join(l.split()) for l in str(text).replace('\r', '').split('\n') if l.strip())[:1500]
    title = ' '.join(str(title).split())[:80] or text[:40]
    if not text:
        return {'success': False, 'text': 'He opened his notebook but wrote nothing.'}
    page = {'id': (pages[-1]['id'] + 1) if pages else 1, 'at': at, 'title': title, 'text': text}
    pages.append(page)
    del pages[:-KEEP]
    return {'success': True, 'text': f'Wrote in his notebook, page {page["id"]}, "{title}": {text[:400]}', 'page': page['id']}


def _written(n):
    return f'He has written {n} page{"s" if n != 1 else ""} in all.'


def _about(query, pages):
    return {'success': True, 'text': f'Looked through his notebook for "{query[:60]}": nothing he has written is about that. '
                                     f'{_written(len(pages))}', 'pages': []}


def _listed(ids):
    if len(ids) == 1:
        return str(ids[0])
    if len(ids) == 2:
        return f'{ids[0]} and {ids[1]}'
    return ', '.join(str(i) for i in ids[:-1]) + f' and {ids[-1]}'


def _no_such(ids, n):
    """A numbered page he asked for is not in the book. This is not a search that found no topic."""
    noun = 'page' if len(ids) == 1 else 'pages'
    fact = 'there is no such page' if len(ids) == 1 else 'there are no such pages'
    return f'Looked for {noun} {_listed(ids)} in his notebook: {fact}. {_written(n)}'


def _page_ids(query):
    """Page numbers he named, or None when this is not a request for those pages.

    "69", "page 69" and "pages 69 and 70" name pages. A phrase that only happens to
    contain a number ("1 gold") does not, and neither does a day ("12-03").
    """
    q = str(query).strip().lower()
    if not q or not re.fullmatch(r'(?:pages?|and|&|,|\s|\d+)+', q):
        return None
    ids = []
    for raw in re.findall(r'\d+', q):
        n = int(raw)
        if n not in ids:
            ids.append(n)
    return ids or None


def _show(hits):
    shown = ' | '.join(f'page {p["id"]} ({str(p["at"])[:16].replace("T", " ")}) "{p["title"]}": {p["text"][:300].replace(chr(10), " / ")} '
                       f'[{shape(p["text"])}]' for p in hits)
    return {'success': True, 'text': 'Read back his notebook: ' + shown, 'pages': [p['id'] for p in hits]}


def read(state, query=''):
    pages = ensure(state)
    if not pages:
        return {'success': True, 'text': 'Opened his notebook: it is empty. He has never written anything in it.', 'pages': []}
    q = str(query).strip().lower()
    if not q:
        return _show(pages[-4:])
    # A day is still a day, including when the query also has words ("12-03 cord bundle").
    day = re.search(r'(\d{1,2})-(\d{1,2})', q)
    if day:
        key = f'{int(day.group(1)):02d}-{int(day.group(2)):02d}'
        hits = [p for p in pages if str(p['at'])[5:10] == key or day.group(0) in (p['title'] + ' ' + p['text'])]
        return _show(hits[-5:]) if hits else _about(query, pages)
    # v0.36.21: the world tells him the page number when he writes, so he can ask for that page.
    wanted = _page_ids(q)
    if wanted is not None:
        by_id = {}
        for p in pages:
            try:
                key = int(p.get('id'))
            except (TypeError, ValueError):
                continue
            by_id.setdefault(key, p)
        found = [by_id[n] for n in wanted if n in by_id]
        missing = [n for n in wanted if n not in by_id]
        if not found:
            return {'success': True, 'text': _no_such(missing, len(pages)), 'pages': []}
        result = _show(found)
        if missing:
            result['text'] += ' ' + _no_such(missing, len(pages))
        return result
    words = [w for w in re.findall(r'[a-z]+', q) if len(w) > 2]
    hits = [p for p in pages if words and any(w in (p['title'] + ' ' + p['text']).lower() for w in words)]
    return _show(hits[-5:]) if hits else _about(query, pages)


def shape(text):
    """What is physically on a page, plainly (v0.29.2): how many lines and sentences. No judgement of what they mean."""
    lines = [l for l in str(text).split('\n') if l.strip()]
    sentences = len([x for x in re.split(r'(?<=[.!?])\s+', ' '.join(lines)) if x.strip()])
    if len(lines) > 1:
        return f'{len(lines)} separate lines written on this page'
    return f'one paragraph of {sentences} sentence{"s" if sentences != 1 else ""}; no separate lines are written on this page'


def summary(state):
    pages = ensure(state)
    return {'pages_written': len(pages), 'latest_titles': [p['title'] for p in pages[-5:]]}
