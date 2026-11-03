"""His notebook (v0.29.1): somewhere to write things down in his own words, and read them back.

An ordinary possession, like his purse. Nothing tells him to write or what to write. It starts
empty: before this he had nowhere to write, so anything he thought he had "written" was only
remembered. Pages are kept for good and can be read back by a word or a day.
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


def read(state, query=''):
    pages = ensure(state)
    if not pages:
        return {'success': True, 'text': 'Opened his notebook: it is empty. He has never written anything in it.', 'pages': []}
    q = str(query).strip().lower()
    if q:
        day = re.search(r'(\d{1,2})-(\d{1,2})', q)
        if day:
            key = f'{int(day.group(1)):02d}-{int(day.group(2)):02d}'
            hits = [p for p in pages if str(p['at'])[5:10] == key or day.group(0) in (p['title'] + ' ' + p['text'])]
        else:
            words = [w for w in re.findall(r'[a-z]+', q) if len(w) > 2]
            hits = [p for p in pages if words and any(w in (p['title'] + ' ' + p['text']).lower() for w in words)]
        if not hits:
            return {'success': True, 'text': f'Looked through his notebook for "{query[:60]}": nothing he has written is about that. '
                                             f'He has written {len(pages)} page{"s" if len(pages) != 1 else ""} in all.', 'pages': []}
    else:
        hits = pages[-4:]
    shown = ' | '.join(f'page {p["id"]} ({str(p["at"])[:16].replace("T", " ")}) "{p["title"]}": {p["text"][:300].replace(chr(10), " / ")} '
                       f'[{shape(p["text"])}]' for p in hits[-5:])
    return {'success': True, 'text': 'Read back his notebook: ' + shown, 'pages': [p['id'] for p in hits[-5:]]}


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
