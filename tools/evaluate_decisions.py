#!/usr/bin/env python3
"""Read-only evaluation of Crow's decisions with the real local model.

Run on the PC that hosts Crow, from the checkout:

    python3 tools/evaluate_decisions.py --samples 6

What it does
- Copies crow-save.json (and the reading archive) into a temporary folder and
  works only on that copy. The live save, event log and running Crow are never
  written to. Nothing is executed in the world: no Wikipedia lookups, no
  actions are started, no reflections are saved.
- Measures the actual stage-one prompt Crow would receive, using Ollama's own
  token counts, and lists the memories recall would surface.
- Asks the real model for N stage-one decisions with recall, and N with older
  memory recall removed (recent events are still shown). Differences between
  the two sets are evidence about whether recalled memory reaches decisions.
  A handful of samples is suggestive, not statistically conclusive.
- Optional --perturb runs the same comparison after a changed circumstance in
  the copy (for example an empty pantry), to look for adaptation.

If Crow is running, Ollama serves both, so each call may be slower. Output
contains his private intentions and memories; share it only if you choose to.
"""
import argparse
import collections
import contextlib
import copy
import importlib.util
import io
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

PERTURBATIONS = {
    'none': 'No change.',
    'empty_pantry': 'Provisions chest and fruit bushes are empty in this copy.',
    'dry_spring': 'The spring basin holds no water in this copy.',
    'new_tool': 'A new portable object (a hand plane) has been placed at the workbench in this copy.',
}


def perturb(state, name):
    if name == 'empty_pantry':
        state['provisions'].update(pantry=0, berries=0)
    elif name == 'dry_spring':
        state['provisions']['water_litres'] = 0
    elif name == 'new_tool':
        import world_state
        objects = state['built_world']['objects']
        objects.setdefault('hand_plane', {'id': 'hand_plane', 'name': 'Hand plane', 'kind': 'tool', 'x': 1.2, 'z': 9.4,
                                          'portable': True, 'revision': 0,
                                          'parts': [world_state.part('body', 0, .9, 0, .25, .08, .07, '#6d5a3d')]})


def load_copy(save, workdir):
    shutil.copy(ROOT / 'crow.py', workdir / 'crow.py')
    if save.exists():
        shutil.copy(save, workdir / 'crow-save.json')
    reading = save.parent / 'crow-reading'
    if reading.is_dir():
        shutil.copytree(reading, workdir / 'crow-reading')
    spec = importlib.util.spec_from_file_location('crow_eval_copy', workdir / 'crow.py')
    app = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):
        spec.loader.exec_module(app)
    return app


def stage_one(app, recall_on):
    original = app.memory_recall.recall
    if not recall_on:
        app.memory_recall.recall = lambda *a, **k: []
    try:
        d, seconds = app.choose_action()
    finally:
        app.memory_recall.recall = original
    usage = app.runtime.get('model_usage', {}).get('choose_action', {})
    return {'action': d['action'], 'intention': d['intention'][:160], 'reason': d['reason'][:200],
            'memory_ids_used': d.get('memory_ids_used', []), 'recalled_ids': d.get('recalled_ids', []),
            'prompt_tokens': usage.get('prompt_tokens'), 'seconds': seconds}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--save', default=str(ROOT / 'crow-save.json'))
    parser.add_argument('--samples', type=int, default=5)
    parser.add_argument('--perturb', choices=list(PERTURBATIONS), default='none')
    parser.add_argument('--context-only', action='store_true', help='Measure context; do not sample decisions.')
    args = parser.parse_args()
    save = Path(args.save).expanduser().resolve()
    with tempfile.TemporaryDirectory() as temp:
        app = load_copy(save, Path(temp))
        perturb(app.state, args.perturb)
        app.state['paused'] = False  # in the copy only
        with app.LOCK:
            context = app.decision_context()
        report = {'save': str(save), 'save_found': save.exists(), 'version': app.APP_VERSION, 'model': app.MODEL,
                  'num_ctx': app.NUM_CTX, 'perturbation': PERTURBATIONS[args.perturb],
                  'memories_saved': len(app.state['memories']), 'lessons_saved': len(app.state['long_term']),
                  'readings_saved': len(app.state.get('reading_log', [])),
                  'context_chars_by_section': {k: len(json.dumps(v, ensure_ascii=False)) for k, v in context.items()},
                  'recalled': context['relevant_memories'], 'recent_pattern': context['recent_pattern']}
        if not args.context_only:
            runs = {'with_recall': [], 'without_recall': []}
            for i in range(args.samples):
                for key, on in (('with_recall', True), ('without_recall', False)):
                    try:
                        runs[key].append(stage_one(app, on))
                    except Exception as exc:  # a failed call is a result too
                        runs[key].append({'error': str(exc)[:300]})
                    print(f'  sample {i + 1}/{args.samples} {key}: {runs[key][-1].get("action", "error")}', file=sys.stderr)
            report['decisions'] = runs
            report['action_counts'] = {k: dict(collections.Counter(r.get('action', 'error') for r in v)) for k, v in runs.items()}
            cited = [r for r in runs['with_recall'] if set(r.get('memory_ids_used', [])) & set(r.get('recalled_ids', []))]
            report['with_recall_cited_a_recalled_memory'] = f'{len(cited)}/{len(runs["with_recall"])}'
            tokens = [r['prompt_tokens'] for v in runs.values() for r in v if r.get('prompt_tokens')]
            if tokens:
                report['prompt_tokens_max'] = max(tokens)
        print(json.dumps(report, indent=2, ensure_ascii=False))
    # The temporary copy is deleted here; the live save was only read.


if __name__ == '__main__':
    main()
