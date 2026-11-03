#!/usr/bin/env python3
"""Check the trading post's book against his purse, for Jordan. Read-only: nothing is written anywhere.

    python3 tools/books_check.py            # the whole book checked, then 3 December in detail
    python3 tools/books_check.py 12-05      # a different day in detail
    python3 tools/books_check.py cord       # entries, notebook pages and Edda's notes containing a word

Every change to his purse goes through the post and is written in its book with what he had after.
This walks the book in order and reports any entry where the purse moved by a different amount
than the entry says, any purse figure in an entry that disagrees with the purse itself, and whether
the purse now matches the last entry. If all of that agrees, the world's own accounts are sound and
anything that does not add up for him is in his own memory or notes, not in the world.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MONEY = r'(\d+) gold(?: (\d+) silver)?|(\d+) silver|(\d+(?:\.\d+)?) credits?'


def amount(m):
    g, s, s_only, cr = m.groups()
    if cr is not None:
        return float(cr)
    if s_only is not None:
        return int(s_only) / 10
    return int(g) + (int(s) / 10 if s else 0)


def show(x):
    if abs(x * 10 - round(x * 10)) > 1e-6:      # part of a silver: no coin is that small, so say it exactly
        return f'{x:.2f} gold (not a whole number of silver)'
    tenths = int(round(abs(x) * 10))
    g, s = divmod(tenths, 10)
    return ('-' if x < 0 else '') + (' '.join(([f'{g} gold'] if g else []) + ([f'{s} silver'] if s else [])) or 'nothing')


def stated(text):
    """What the entry says changed hands, and which way (None: the entry moves no money)."""
    if text.startswith(('Agreed a favour', 'New stock arrived', 'The weekly delivery', 'Wrote "', 'From now on the post counts')):
        return None
    body = re.split(r'\.?\s*(?:Left in his purse|In his purse):', text)[0]
    body = re.sub(r'\(board price[^)]*\)', '', body)
    found = list(re.finditer(MONEY, body))
    if not found:
        return None
    x = amount(found[-1])
    return -x if text.startswith('Bought') else x


def purse_in(text):
    m = re.search(r'(?:Left in his purse|In his purse):\s*(' + MONEY + r'|nothing)', text)
    if not m:
        return None
    return 0. if m.group(1) == 'nothing' else amount(re.match(MONEY, m.group(1)))


def main():
    query = (sys.argv[1] if len(sys.argv) > 1 else '12-03').strip()
    save = ROOT / 'crow-save.json'
    if '--save' in sys.argv:
        save = Path(sys.argv[sys.argv.index('--save') + 1])
    state = json.loads(save.read_text())
    post = state.get('trading', {})
    book = post.get('ledger', [])
    purse = float(post.get('credit', 0))
    print(f"THE POST'S BOOK, CHECKED AGAINST HIS PURSE (read-only) · {len(book)} entries\n")

    problems, prev = [], None
    for e in book:
        after = e.get('credit_after')
        said = stated(e.get('text', ''))
        if after is not None and prev is not None:
            moved = round(after - prev, 2)
            expect = round(said or 0., 2)
            if abs(moved - expect) > .049:
                problems.append(f"  {str(e.get('at', ''))[:16].replace('T', ' ')} · the purse moved {show(moved)}, the entry says {show(expect)}: {e['text'][:160]}")
        p = purse_in(e.get('text', ''))
        if p is not None and after is not None and abs(p - after) > .049:
            problems.append(f"  {str(e.get('at', ''))[:16].replace('T', ' ')} · the entry says he had {show(p)}, the purse held {show(after)}")
        if after is not None:
            prev = after
    print('Entries that disagree with the purse:')
    print('\n'.join(problems) if problems else '  none: every amount in the book matches what his purse did.')
    print(f"\nHis purse now: {show(purse)} · the last entry left him with {show(prev) if prev is not None else 'no figure'}"
          + (' · they agree.' if prev is None or abs(prev - purse) < .05 else ' · THEY DIFFER: money moved outside the book.'))

    day = re.fullmatch(r'(\d{1,2})-(\d{1,2})', query)
    key = f'{int(day.group(1)):02d}-{int(day.group(2)):02d}' if day else None
    hits = [e for e in book if (str(e.get('at', ''))[5:10] == key if key else query.lower() in e.get('text', '').lower())]
    print(f"\nIn the book for {query}:" if hits else f"\nNothing in the book for {query}.")
    before = None
    for e in book:
        if e in hits:
            print(f"  {str(e.get('at', ''))[:16].replace('T', ' ')} · {e['text']}"
                  + (f"  [purse {show(before)} → {show(e['credit_after'])}]" if before is not None and e.get('credit_after') is not None else ''))
        if e.get('credit_after') is not None:
            before = e['credit_after']

    words = [query.lower()] + (['cord'] if key else [])
    pages = [p for p in state.get('notebook', []) if any(w in (p.get('title', '') + ' ' + p.get('text', '')).lower() for w in words)]
    print(f"\nHis notebook pages about it ({len(pages)}; his notebook began on {str((state.get('notebook') or [{}])[0].get('at', 'never'))[:16].replace('T', ' ')}):")
    for p in pages[:12]:
        print(f"  page {p['id']} ({str(p.get('at', ''))[:16].replace('T', ' ')}) \"{p.get('title', '')}\": " + p.get('text', '').replace('\n', ' / ')[:400])
    if len(pages) > 12:
        print(f'  … and {len(pages) - 12} more')

    notes = [n for n in state.get('keeper', {}).get('notes', []) if any(w in n.get('text', '').lower() for w in words + ['silver', 'gap', 'owe'])]
    print('\nWhat Edda has noted about it (her notes, not his):')
    print('\n'.join(f"  {str(n.get('at', ''))[:16].replace('T', ' ')} · {n['text']}" for n in notes[-8:]) or '  nothing.')


if __name__ == '__main__':
    main()
