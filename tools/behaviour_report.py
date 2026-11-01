#!/usr/bin/env python3
"""Read-only report of actual choices and physical outcomes, with no model calls.

    python3 tools/behaviour_report.py --days 7

Uses the save and, when available, the complete event log beside it. Prints to
the terminal; it never changes Crow, runs a twin or awards an autonomy score.
The report contains private history, so share it only if you choose to.
"""
import argparse
import json
import sys
from datetime import datetime,timedelta
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import experience


def build(save, days=7):
    state=json.loads(save.read_text())
    log=save.parent/'crow-events.jsonl'
    events={m['id']:m for m in state.get('memories',[])}
    if log.exists():
        with log.open() as f:
            for line in f:
                try:
                    m=json.loads(line);events.setdefault(m['id'],m)
                except (ValueError,KeyError,TypeError):continue
    dated=[m.get('at','')[:10] for m in events.values() if m.get('at')]
    since=(datetime.fromisoformat(max(dated))-timedelta(days=days-1)).date().isoformat() if dated else ''
    state['memories']=sorted((m for m in events.values() if m.get('at','')[:10]>=since),key=lambda m:m['id'])
    state['reading_log']=[r for r in state.get('reading_log',[]) if r.get('at','')[:10]>=since]
    state['interest_history']={k:{**v,'episodes':[e for e in v['episodes'] if e.get('at','')[:10]>=since]}
                               for k,v in state.get('interest_history',{}).items()}
    state['procedures']={**state.get('procedures',{}),'attempts':[
        a for a in state.get('procedures',{}).get('attempts',[]) if a.get('at','')[:10]>=since]}
    report=experience.report(state)
    report.update(version='0.16.0',since=since,requested_days=days,
                  coverage='events from save and available event log; procedure/interest trails from bounded save indexes',
                  note='Choices and citations are observations. Reported enjoyment is interpretation. No score proves autonomy.')
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--save',type=Path,default=ROOT/'crow-save.json')
    parser.add_argument('--days',type=int,default=7)
    args=parser.parse_args()
    if args.days<1:parser.error('--days must be positive')
    save=args.save.expanduser().resolve()
    if not save.is_file():parser.error('No saved life found at '+str(save))
    print(json.dumps(build(save,args.days),indent=2,ensure_ascii=False))


if __name__=='__main__':main()
