"""The harp: a real 19-string lever harp, music he writes down, practice that shows, and sound Jordan can hear.

An authored world opportunity. Nothing here tells Crow to play, what to play or how.

- The instrument: 19 strings tuned to the white notes from C3 to G5. A lever at the top of a
  string raises it a semitone, so sharps are possible; flats are the same strings as the sharp
  below (B flat is A sharp). Nothing outside that range can be played.
- Writing music: notes as NAME+OCTAVE:BEATS separated by spaces, rests as R:BEATS, e.g.
  "C4:1 E4:0.5 G4:0.5 R:1". This is how pieces are kept, how the sheet music in the reading
  cabin is written, and how anything he finds elsewhere can be copied down.
- Playing is measured, not judged: notes that go astray (onto a neighbouring string) and how
  even the timing was. Both improve with hours at the harp and with familiarity with a piece;
  fatigue and harder pieces (fast, wide leaps, many lever changes) make them worse.
- What he actually played (slips and all) is kept, so it can be heard exactly as it went.
"""
import math
import random
import re

NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
NATURALS = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
LOW, HIGH = 48, 79          # C3 .. G5 (MIDI numbers)
BEATS = (.25, .5, .75, 1., 1.5, 2., 3., 4.)
MAX_NOTES = 160
DURATION = 1800              # a session at the harp, in lived seconds


def ensure(state):
    m = state.setdefault('music', {'hours': 0., 'pieces': [], 'next_piece': 1, 'songbook_seen': False, 'sessions': 0})
    return m


def midi_name(n):
    return f'{NAMES[n % 12]}{n // 12 - 1}'


def string_of(n):
    """The string a note is played on: naturals are their own string; a sharp is the string below with its lever up."""
    return n if NAMES[n % 12] in NATURALS else n - 1


def parse(text):
    """Notation to [(midi or None, beats)], plus plain-language problems. Unplayable notes are reported, not guessed."""
    notes, problems = [], []
    for tok in re.split(r'[\s,;|]+', str(text).strip()):
        if not tok:
            continue
        m = re.fullmatch(r'(?i)(r|rest|[a-g])([#b]?)(\d)?[:/](\d+(?:\.\d+)?)', tok)
        if not m:
            problems.append(f'"{tok}" is not written as NOTE+OCTAVE:BEATS')
            continue
        name, acc, octave, beats = m.group(1).upper(), m.group(2), m.group(3), float(m.group(4))
        beats = min(BEATS, key=lambda b: abs(b - beats))
        if name in ('R', 'REST'):
            notes.append((None, beats))
            continue
        if octave is None:
            problems.append(f'"{tok}" has no octave number')
            continue
        n = 12 * (int(octave) + 1) + NATURALS[name] + (1 if acc == '#' else -1 if acc == 'b' else 0)
        if not LOW <= n <= HIGH or (NAMES[n % 12] not in NATURALS and n - 1 < LOW):
            problems.append(f'{tok.split(":")[0].split("/")[0]} is outside the harp\'s strings (C3 to G5)')
            continue
        notes.append((n, beats))
        if len(notes) >= MAX_NOTES:
            problems.append(f'only the first {MAX_NOTES} notes fit on one sheet')
            break
    return notes, problems


def write(notes):
    return ' '.join(('R' if n is None else midi_name(n)) + f':{b:g}' for n, b in notes)


def difficulty(notes, tempo):
    sounded = [n for n, _ in notes if n is not None]
    if len(sounded) < 2:
        return .2
    leaps = sum(abs(string_of(a) - string_of(b)) for a, b in zip(sounded, sounded[1:])) / (len(sounded) - 1)
    shortest = min(b for _, b in notes)
    speed = tempo / 60 / shortest          # notes per second at the quickest
    levers = sum(1 for n in sounded if NAMES[n % 12] not in NATURALS) / len(sounded)
    return round(.4 + .12 * speed + .05 * leaps + .8 * levers, 3)


def perform(state, piece, fatigue, seed):
    """Play a piece once: which notes went astray, how even the time was. Deterministic for a seed."""
    m = ensure(state)
    notes = [tuple(x) for x in piece['notes']]
    rng = random.Random(seed)
    familiarity = 1 + .35 * piece.get('times_played', 0)
    slip_p = min(.45, .22 * difficulty(notes, piece['tempo']) / (1 + math.sqrt(m['hours'])) * (1 + .6 * fatigue) / math.sqrt(familiarity))
    wobble = .14 / (1 + math.sqrt(m['hours'])) * (1 + .5 * fatigue)
    played, slips = [], 0
    for n, b in notes:
        if n is not None and rng.random() < slip_p:
            strings = [s for s in range(LOW, HIGH + 1) if NAMES[s % 12] in NATURALS]
            i = strings.index(string_of(n))
            n = strings[max(0, min(len(strings) - 1, i + rng.choice((-1, 1))))]
            slips += 1
        played.append((n, round(max(.1, b * (1 + rng.gauss(0, wobble))), 3)))
    sounded = sum(1 for n, _ in notes if n is not None)
    evenness = 'steady' if wobble < .04 else 'mostly even' if wobble < .08 else 'uneven' if wobble < .12 else 'halting'
    return {'played': played, 'slips': slips, 'notes': sounded, 'timing': evenness}


def describe(piece, result):
    s = result['slips']
    went = 'every note landed' if not s else f'{s} of {result["notes"]} notes went astray onto a neighbouring string'
    return f'Played "{piece["title"]}" on the harp ({result["notes"]} notes at {piece["tempo"]} beats a minute): {went}; the timing was {result["timing"]}.'


def session(state, d, fatigue, seed, at):
    """Start a session at the harp: set up the piece and the performance that will be heard. Returns (piece, result, text) or raises."""
    m = ensure(state)
    mode = d.get('music_mode', 'practise')
    if mode in ('compose', 'revise'):
        notes, problems = parse(d.get('notes', ''))
        if not notes:
            raise ValueError('Nothing playable was written: ' + ('; '.join(problems[:3]) or 'no notes'))
        tempo = int(min(160, max(40, d.get('tempo') or 80)))
        if mode == 'compose':
            piece = {'id': m['next_piece'], 'title': (d.get('title') or 'Untitled').strip()[:80], 'notes': notes,
                     'tempo': tempo, 'by': 'Crow', 'source': 'composed', 'created': at, 'revisions': 0,
                     'times_played': 0, 'best_slips': None}
            m['next_piece'] += 1
            m['pieces'].append(piece)
        else:
            piece = next((p for p in m['pieces'] if p['id'] == d.get('piece_id')), None)
            if not piece:
                raise ValueError('There is no such piece to revise')
            piece.update(notes=notes, tempo=tempo, revisions=piece['revisions'] + 1, revised=at,
                         times_played=0 if piece['by'] == 'Crow' else piece['times_played'])
        note = (' Could not be played as written: ' + '; '.join(problems[:3]) + '.') if problems else ''
    elif mode == 'learn':
        tune = next((t for t in SONGBOOK if t['title'] == d.get('songbook')), None)
        if not tune or not m['songbook_seen']:
            raise ValueError('He has no sheet music for that')
        piece = next((p for p in m['pieces'] if p['title'] == tune['title'] and p['source'] == 'sheet music'), None)
        if piece is None:
            notes, _ = parse(tune['notes'])
            piece = {'id': m['next_piece'], 'title': tune['title'], 'notes': notes, 'tempo': tune['tempo'],
                     'by': tune['by'], 'source': 'sheet music', 'created': at, 'revisions': 0, 'times_played': 0, 'best_slips': None}
            m['next_piece'] += 1
            m['pieces'].append(piece)
        note = ''
    else:
        piece = next((p for p in m['pieces'] if p['id'] == d.get('piece_id')), None)
        if not piece:
            raise ValueError('There is no such piece in his repertoire')
        note = ''
    result = perform(state, piece, fatigue, seed)
    return piece, result, note


def finish(state, piece, result, seconds, fatigue):
    m = ensure(state)
    m['hours'] = round(m['hours'] + max(0, seconds) / 3600 / (1 + fatigue), 4)
    m['sessions'] += 1
    piece['times_played'] += 1
    piece['best_slips'] = result['slips'] if piece['best_slips'] is None else min(piece['best_slips'], result['slips'])
    piece['last_played'] = result['played']
    piece['last_slips'] = result['slips']
    piece['last_timing'] = result['timing']


def context(state):
    m = ensure(state)
    return {'notation': 'NOTE+OCTAVE:BEATS separated by spaces, rests R:BEATS, e.g. "C4:1 E4:0.5 G4:0.5 R:1"',
            'strings': '19 strings, C3 to G5; a lever raises a string a semitone (sharps)',
            'your_pieces': [{'id': p['id'], 'title': p['title'], 'source': p['source'], 'times_played': p['times_played'],
                             'last_slips': p.get('last_slips'), 'notes_written': write(p['notes'])[:400]} for p in m['pieces'][-8:]],
            'sheet_music_you_have_seen': [t['title'] for t in SONGBOOK] if m['songbook_seen'] else [],
            'hours_at_the_harp': round(m['hours'], 1)}


# Public-domain tunes on the shelf of sheet music in the reading cabin, in the harp's notation.
SONGBOOK = [
    {'title': 'Twinkle, Twinkle, Little Star (traditional French air)', 'by': 'traditional', 'tempo': 90,
     'notes': 'C4:1 C4:1 G4:1 G4:1 A4:1 A4:1 G4:2 F4:1 F4:1 E4:1 E4:1 D4:1 D4:1 C4:2 '
              'G4:1 G4:1 F4:1 F4:1 E4:1 E4:1 D4:2 G4:1 G4:1 F4:1 F4:1 E4:1 E4:1 D4:2 '
              'C4:1 C4:1 G4:1 G4:1 A4:1 A4:1 G4:2 F4:1 F4:1 E4:1 E4:1 D4:1 D4:1 C4:2'},
    {'title': 'Frère Jacques (traditional round)', 'by': 'traditional', 'tempo': 100,
     'notes': 'C4:1 D4:1 E4:1 C4:1 C4:1 D4:1 E4:1 C4:1 E4:1 F4:1 G4:2 E4:1 F4:1 G4:2 '
              'G4:0.5 A4:0.5 G4:0.5 F4:0.5 E4:1 C4:1 G4:0.5 A4:0.5 G4:0.5 F4:0.5 E4:1 C4:1 '
              'C4:1 G3:1 C4:2 C4:1 G3:1 C4:2'},
    {'title': 'Ode to Joy (Beethoven, Ninth Symphony)', 'by': 'Ludwig van Beethoven', 'tempo': 100,
     'notes': 'E4:1 E4:1 F4:1 G4:1 G4:1 F4:1 E4:1 D4:1 C4:1 C4:1 D4:1 E4:1 E4:1.5 D4:0.5 D4:2 '
              'E4:1 E4:1 F4:1 G4:1 G4:1 F4:1 E4:1 D4:1 C4:1 C4:1 D4:1 E4:1 D4:1.5 C4:0.5 C4:2'},
    {'title': 'Amazing Grace (traditional hymn tune)', 'by': 'traditional', 'tempo': 80,
     'notes': 'D4:1 G4:2 B4:0.5 G4:0.5 B4:2 A4:1 G4:2 E4:1 D4:2 D4:1 G4:2 B4:0.5 G4:0.5 B4:2 A4:0.5 B4:0.5 D5:3'},
    {'title': 'Scarborough Fair (traditional English ballad)', 'by': 'traditional', 'tempo': 90,
     'notes': 'D4:2 D4:1 A4:2 A4:1 E4:1.5 F4:0.5 E4:1 D4:3 R:1 A4:1 C5:1 D5:2 C5:1 A4:1 B4:1 G4:1 A4:3'},
]
