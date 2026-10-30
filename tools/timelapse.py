#!/usr/bin/env python3
"""Time-lapse twin: a separate copy of Crow living on a fast-forward clock.

    python3 tools/timelapse.py --days 14      # pilot: two simulated weeks
    python3 tools/timelapse.py --days 548     # carry on to about 18 months

What it is
- A COPY of Crow's save, in its own folder (default ~/crow-twin), living with
  the same code, body, world, memory and local model as the real Crow. The real
  Crow, his save and his event log are only read once, when the twin is created.
- Its clock jumps forward as each activity's time is used up, instead of
  waiting in real time. Model inference still takes real time, and that time
  also passes for the twin, as it does for the real Crow.
- Nobody adds resources or opportunities during the run. Wikipedia lookups are
  real.

It is resumable: stop it with Ctrl+C at any time and run the same command
again to continue. Run tools/timelapse_report.py for a summary.

What it is not: a prediction of the real Crow. It is one run of one small
model in this world. The twin's life diverges from his as soon as it starts.
"""
import argparse
import contextlib
import http.client
import socket
import urllib.error
import importlib.util
import io
import json
import shutil
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUTAGE = (urllib.error.URLError, ConnectionError, http.client.RemoteDisconnected, socket.timeout, TimeoutError)


class ModelOutage(Exception):
    """The model server (not Wikipedia, not his own choices) could not be reached."""


def create(twin, source):
    """Copy the real life once. Never writes to the source folder."""
    twin.mkdir(parents=True, exist_ok=True)
    src = source.parent
    if not source.exists():
        raise SystemExit(f'No save found at {source}.')
    shutil.copy2(source, twin / 'crow-save.json')
    for name in ['crow-events.jsonl', 'crow-config.json']:
        if (src / name).exists():
            shutil.copy2(src / name, twin / name)
    if (src / 'crow-reading').is_dir():
        shutil.copytree(src / 'crow-reading', twin / 'crow-reading', dirs_exist_ok=True)


def load(twin):
    # The twin always runs the current code from this checkout, against its own saved life.
    shutil.copy2(ROOT / 'crow.py', twin / 'crow.py')
    # Owner settings (model provider, key) follow the real checkout; his life does not.
    if (ROOT / 'crow-config.json').exists():
        shutil.copy2(ROOT / 'crow-config.json', twin / 'crow-config.json')
    spec = importlib.util.spec_from_file_location('crow_twin', twin / 'crow.py')
    app = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):
        spec.loader.exec_module(app)
    return app


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--twin', default='~/crow-twin', help='Folder for the twin (created if missing).')
    parser.add_argument('--from-save', default=str(ROOT / 'crow-save.json'), help='Real save to copy when creating the twin.')
    parser.add_argument('--days', type=float, required=True, help='Run until this many simulated days after the twin began.')
    parser.add_argument('--max-errors', type=int, default=25, help='Stop after this many consecutive failures.')
    parser.add_argument('--max-spend', type=float, default=40., help='Cloud-model spend limit in US dollars for the whole twin (then local Qwen).')
    args = parser.parse_args()
    run(Path(args.twin).expanduser().resolve(), Path(args.from_save).expanduser().resolve(), args.days, args.max_errors,
        max_spend=args.max_spend)


def run(twin, source, days, max_errors=25, model=None, max_spend=40.):
    """Advance the twin until `days` simulated days after it began. `model` replaces Ollama in tests."""
    if twin == source.parent or twin == ROOT or ROOT in twin.parents:
        raise SystemExit('The twin folder must be separate from the real Crow and from this checkout.')
    if not (twin / 'crow-save.json').exists():
        create(twin, source)
        print(f'Created a twin of {source} in {twin}. The real Crow is not affected.')
    app = load(twin)
    st = app.state
    meta = st.setdefault('twin', {})
    if not meta:
        meta.update(started_virtual=datetime.now(app.TZ).isoformat(), source=str(source),
                    created_real=datetime.now(app.TZ).isoformat(), model_calls=0, errors=[], near_limit_calls=0,
                    real_seconds=0.)
    clock = {'now': datetime.fromisoformat(meta.get('virtual_now') or meta['started_virtual'])}
    app.CLOCK_OVERRIDE = lambda: clock['now']
    start = datetime.fromisoformat(meta['started_virtual'])
    end = start + timedelta(days=days)

    original_call = model or app.model_call

    # The twin has its own whole-run budget instead of the real Crow's daily one.
    app.DAILY_BUDGET = float('inf')

    def counted(*a, **k):
        if app.PROVIDER == 'anthropic' and st.get('model_spend', {}).get('total_usd', 0) >= max_spend:
            app.PROVIDER = 'ollama'
            print(f'Cloud spend reached ${max_spend:.2f}; continuing on the local model.', flush=True)
        try:
            result = original_call(*a, **k)
        except OUTAGE as exc:
            raise ModelOutage(str(exc)) from exc
        meta['model_calls'] += 1
        purpose = a[3] if len(a) > 3 else k.get('purpose', 'other')
        if app.runtime.get('model_usage', {}).get(purpose, {}).get('near_context_limit'):
            meta['near_limit_calls'] += 1
        return result
    app.model_call = counted

    def save():
        meta['virtual_now'] = clock['now'].isoformat()
        app.persist()

    def thinking(seconds):
        # Inference time passes for him too, without counting towards the activity in progress.
        clock['now'] += timedelta(seconds=seconds)
        app.life.advance(st, seconds, 'reflect')

    st['paused'] = False
    generation = app.runtime['generation']
    failures = 0
    outage_started = None
    last_report_day = None
    run_started = time.monotonic()
    print(f'Twin clock {clock["now"]:%d %b %Y %H:%M}; running until {end:%d %b %Y %H:%M}. Ctrl+C stops safely.')
    try:
        while clock['now'] < end:
            pending = st['pending']
            if pending and pending['remaining'] > 0:
                # Work may go slower than the clock (tiredness, darkness); step by clock time, not work left.
                step = pending['remaining'] / max(.05, app.life.work_rate(st, pending['decision']['action']))
                reviewable = pending['decision']['action'] in app.REVIEWABLE
                if reviewable:
                    step = min(step, max(1, pending.get('review_in', 900)))
                clock['now'] += timedelta(seconds=step)
                app.tick(step)
                if reviewable and st['pending'] is pending and pending['remaining'] > 0 and pending['review_in'] <= 0:
                    t0 = time.monotonic()
                    try:
                        app.review_work(pending)
                    except Exception as exc:
                        # He keeps working; the next check-in comes after another 15 minutes.
                        pending['review_in'] = 900
                        meta['errors'] = (meta['errors'] + [{'at': clock['now'].isoformat(), 'error': 'review: ' + str(exc)[:280]}])[-60:]
                    finally:
                        thinking(time.monotonic() - t0)
                continue
            t0 = time.monotonic()
            try:
                memory = None
                if pending:
                    geometry = app.draft_geometry(pending) if pending['decision']['action'] == 'plan' else None
                    memory = app.finish_action(geometry)
                    if memory.get('action') == 'sleep':
                        app.consolidate_after_sleep()
                elif st.get('reflection_pending') is not None:
                    memory = next((m for m in st['memories'] if m['id'] == st['reflection_pending']), None)
                    if memory is None:
                        st['reflection_pending'] = None
                if memory is not None:
                    app.reflect(memory)
                app.decide_and_start(generation)
                failures = 0
                outage_started = None
            except ModelOutage as exc:
                # Ollama or the network being down is not part of his life: wait in real time, keep the twin's clock still.
                outage_started = outage_started or time.monotonic()
                if time.monotonic() - outage_started > 1800:
                    print(f'Stopping: the model server has been unreachable for 30 minutes ({exc}). Run the command again later.')
                    break
                print(f'  Waiting for Ollama / the network ({exc}); the twin is not ageing meanwhile…', flush=True)
                time.sleep(30)
                t0 = time.monotonic()  # the wait is not processing time for him
                continue
            except Exception as exc:  # a failure is recorded as part of the run, not hidden
                failures += 1
                meta['errors'] = (meta['errors'] + [{'at': clock['now'].isoformat(), 'error': str(exc)[:300]}])[-60:]
                st['paused'] = False
                clock['now'] += timedelta(seconds=60)
                app.life.advance(st, 60, 'reflect')
                if failures >= max_errors:
                    print(f'Stopping: {failures} consecutive failures. Last: {exc}')
                    break
            finally:
                spent = time.monotonic() - t0
                meta['real_seconds'] += spent
                thinking(spent)
                save()
            day = (clock['now'] - start).days
            if day != last_report_day:
                last_report_day = day
                elapsed = time.monotonic() - run_started
                done = (clock['now'] - start).total_seconds() / max(1, (end - start).total_seconds())
                print(f'Simulated day {day} ({clock["now"]:%a %d %b %Y}) · {st["decisions"]} decisions · '
                      f'{meta["model_calls"]} model calls · {len(meta["errors"])} errors · '
                      f'{elapsed / 3600:.1f} h this session', flush=True)
    except KeyboardInterrupt:
        print('\nStopped by you. Run the same command to continue.')
    finally:
        save()
    print(f'Twin clock now {clock["now"]:%d %b %Y %H:%M}. Report: python3 tools/timelapse_report.py --twin {twin}')
    return app


if __name__ == '__main__':
    main()
