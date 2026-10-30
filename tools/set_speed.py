#!/usr/bin/env python3
"""Set how fast Crow lives, then restart him.

    python3 tools/set_speed.py 24     # like Pino: one real hour is one Crow day
    python3 tools/set_speed.py 1      # normal speed (he keeps his own calendar once he has one)

At a speed above 1 he gets his own calendar, starting at the present moment:
his sun, seasons and plants follow it rather than the real UK date. Activities,
digestion, sleep and fading memories all run at that speed while he is running;
nothing advances while he is paused or closed. Cloud spending rises with speed,
so the daily cap may need raising (tools/use_haiku.py --daily-budget 3).
"""
import json
import os
import sys
from pathlib import Path

CONFIG = Path(__file__).resolve().parents[1] / 'crow-config.json'


def main():
    if not (CONFIG.parent / 'crow-save.json').exists():
        sys.exit(f'No Crow save in {CONFIG.parent}. Run this from the folder where Crow lives: cd ~/Crows-Nest')
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    try:
        speed = float(sys.argv[1])
    except ValueError:
        sys.exit('Give a number, for example 24.')
    if not 1 <= speed <= 60:
        sys.exit('Choose a speed between 1 and 60.')
    settings = json.loads(CONFIG.read_text()) if CONFIG.exists() else {}
    settings['time_scale'] = speed
    tmp = CONFIG.with_suffix('.tmp')
    tmp.write_text(json.dumps(settings, indent=2))
    os.chmod(tmp, 0o600)
    tmp.replace(CONFIG)
    day = 24 / speed
    print(f'Saved: {speed:g}× speed (one Crow day every {day:g} real hours). Restart Crow for it to take effect.')


if __name__ == '__main__':
    main()
