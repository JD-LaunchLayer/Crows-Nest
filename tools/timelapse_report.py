#!/usr/bin/env python3
"""Summarise a time-lapse twin's life, month by simulated month.

    python3 tools/timelapse_report.py            # reads ~/crow-twin, writes ~/crow-twin/report.md

Everything here is counted from the twin's saved events and state. Short
quotations of his own reflections are included for texture; they are his
model-generated interpretations, not evidence of feelings. Read-only.
"""
import argparse
import collections
import json
from datetime import datetime
from pathlib import Path


def load_events(twin, start):
    events = []
    with (twin / 'crow-events.jsonl').open() as f:
        for line in f:
            try:
                e = json.loads(line)
            except ValueError:
                continue
            if e.get('at') and datetime.fromisoformat(e['at']) >= start:
                events.append(e)
    return events


def streak(seq):
    best, run, prev = 0, 0, None
    for x in seq:
        run = run + 1 if x == prev and x else 1
        prev = x
        best = max(best, run)
    return best


def short(text, n=150):
    text = ' '.join(str(text or '').split())
    return text if len(text) <= n else text[:n - 1] + '…'


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--twin', default='~/crow-twin')
    args = parser.parse_args()
    twin = Path(args.twin).expanduser()
    st = json.loads((twin / 'crow-save.json').read_text())
    meta = st.get('twin', {})
    start = datetime.fromisoformat(meta['started_virtual'])
    events = load_events(twin, start)
    by_id = {e['id']: e for e in events}
    when = {m['id']: m.get('at') for m in st.get('memories', [])}
    when.update({e['id']: e.get('at') for e in events})
    months = collections.defaultdict(list)
    for e in events:
        months[(datetime.fromisoformat(e['at']) - start).days // 30].append(e)
    out = []
    w = out.append
    now = datetime.fromisoformat(meta.get('virtual_now', meta['started_virtual']))
    w(f"# Time-lapse twin report\n")
    w(f"Simulated {start:%d %b %Y} → {now:%d %b %Y} ({(now - start).days} days). "
      f"{meta.get('model_calls', 0)} model calls, {meta.get('real_seconds', 0) / 3600:.1f} h of real processing, "
      f"{len(meta.get('errors', []))} recent errors recorded, {meta.get('near_limit_calls', 0)} calls near the context limit.\n")
    w('One run of one local model in an authored world; not a prediction of the real Crow.\n')
    w('| Month | Decisions | Main actions | Distinct intentions | Longest same-intention run | Cited a memory | Cited one >7 days old | Readings (not answered / repeats) | Failed searches | Observations (new details) | Carvings (met / mean error mm) |')
    w('|---|---|---|---|---|---|---|---|---|---|---|')
    for month in sorted(months):
        es = months[month]
        started = [e for e in es if e.get('kind') == 'started']
        actions = collections.Counter(e.get('action') for e in started)
        intentions = [(e.get('intention') or '').strip().casefold() for e in started]
        cited = [e for e in started if e.get('memory_ids_used')]
        old = 0
        for e in cited:
            t = datetime.fromisoformat(e['at'])
            if any(when.get(i) and (t - datetime.fromisoformat(when[i])).days > 7 for i in e['memory_ids_used']):
                old += 1
        reads = [e for e in es if e.get('kind') == 'experience' and e.get('action') == 'read']
        read_ids = {e['id'] for e in reads}
        log = [r for r in st.get('reading_log', []) if r['id'] in read_ids]
        unanswered = sum(r.get('answer_status') == 'not_answered' for r in log)
        repeats = sum(r.get('new_source_text') is False for r in log)
        misses = sum(e.get('kind') == 'research_feedback' for e in es)
        obs = [e for e in es if e.get('kind') == 'experience' and e.get('action') == 'observe']
        new = sum((e.get('world_result') or {}).get('new_details', 0) for e in obs)
        trials = [(e.get('world_result') or {}).get('trial') for e in es if e.get('action') == 'craft' and e.get('kind') == 'experience']
        trials = [t for t in trials if t]
        carve = f"{sum(t['goal_met'] for t in trials)}/{len(trials)} · {sum(t['actual_error_mm'] for t in trials) / len(trials):.1f}" if trials else '—'
        main = ', '.join(f'{a} {n}' for a, n in actions.most_common(4))
        w(f"| {month + 1} | {len(started)} | {main} | {len(set(intentions))} | {streak(intentions)} | "
          f"{len(cited)}/{len(started)} | {old} | {len(reads)} ({unanswered}/{repeats}) | {misses} | {len(obs)} ({new}) | {carve} |")

    w('\n## Intentions he spent most decisions on\n')
    counts = collections.Counter((e.get('intention') or '').strip() for e in events if e.get('kind') == 'started')
    for text, n in counts.most_common(8):
        w(f'- {n} × {short(text)}')
    w('\n## Projects\n')
    for p in st.get('projects', []):
        if p.get('created', '') >= meta['started_virtual'][:10] or p.get('status') != 'completed':
            w(f"- [{p.get('status')}] {short(p.get('title'), 120)} (milestone {p.get('progress')}/{p.get('target')} {p.get('target_action')})")
    w('\n## Wishes expressed during the run\n')
    for x in st.get('wishes', []):
        if x.get('at', '') >= meta['started_virtual']:
            w(f"- {short(x['text'], 120)} — mentioned {x.get('mentions')}×")
    w('\n## Self-observations (latest)\n')
    for n in st.get('personality_notes', [])[-6:]:
        w(f"- {short(n['text'])}")
    w('\n## Lessons (latest)\n')
    for x in st.get('long_term', [])[-6:]:
        w(f"- {short(x['interpretation'])}")
    w('\n## Strongest interest scores\n')
    for k, v in sorted(st.get('interests', {}).items(), key=lambda kv: -abs(kv[1]))[:8]:
        w(f'- {k}: {v}')
    w('\n## A reflection from the start and end of each month\n')
    diary = [d for d in st.get('diary', []) if d.get('at', '') >= meta['started_virtual']]
    by_month = collections.defaultdict(list)
    for d in diary:
        by_month[(datetime.fromisoformat(d['at']) - start).days // 30].append(d)
    for month in sorted(by_month):
        ds = by_month[month]
        w(f"- Month {month + 1}: “{short(ds[0]['text'], 140)}” … “{short(ds[-1]['text'], 140)}”")
    world = st.get('built_world', {})
    w('\n## World at the end\n')
    prov = st.get('provisions', {})
    w(f"- Ready food {prov.get('pantry', 0):.1f} servings, fruit {prov.get('berries', 0):.1f}, spring {prov.get('water_litres', 0):.1f} L")
    w(f"- Inventory: wood {st.get('materials', 0)} kg, stone {st.get('stone', 0)} kg; loose wood left {world.get('sources', {}).get('wood', {}).get('stock')} kg")
    w(f"- Trees felled: {sum(t['stage'] != 'standing' for t in world.get('trees', {}).values())}; carvings {len(st.get('creations', []))}; "
      f"built/planned objects {len(world.get('objects', {}))}/{len(world.get('plans', []))}")
    w(f"- Body now: {', '.join(st.get('body', {}) and [f'{k} {v:.1f}' for k, v in st['body'].items() if k != 'active_hours'])}")
    if meta.get('errors'):
        w('\n## Recent errors\n')
        common = collections.Counter(short(e['error'], 90) for e in meta['errors'])
        for text, n in common.most_common(5):
            w(f'- {n} × {text}')
    report = '\n'.join(out)
    (twin / 'report.md').write_text(report)
    print(report)


if __name__ == '__main__':
    main()
