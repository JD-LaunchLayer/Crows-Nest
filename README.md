# Crow's Nest

A local AI inhabitant in a walkable low-poly woodland world. Jordan provides
the environment and tools; Crow chooses his direction. See [DESIGN.md](DESIGN.md)
for the governing brief and the distinction between working and planned features.

## Run

Requires Python 3.12+, Ollama with `qwen3:4b`, and a WebGL2-capable browser.
No pip packages or paid AI APIs are required. Wikipedia reading uses the internet.

```bash
git clone https://github.com/JD-LaunchLayer/Crows-Nest.git ~/Crows-Nest
cd ~/Crows-Nest
python3 crow.py
```

Open http://127.0.0.1:8765 and click **Begin life**. Keep the terminal open.
Ctrl+C stops safely. Crow starts paused and resumes saved activity progress.

WASD moves, mouse looks, Esc releases the pointer. Arrow keys also move/turn.
Home returns to the entrance. **Find Crow** brings you near him.

## Move your existing Crow here once

Stop the old Crow with Ctrl+C. After cloning, run:

```bash
cd ~/Crows-Nest
python3 migrate_save.py ~/crow-world
python3 crow.py
```

The migration copies save files, event history, cached articles and any local
configuration. It does not delete the old folder and refuses to overwrite
existing destination data. Do not run two copies against the same save.

## Get future updates

Stop Crow with Ctrl+C, then:

```bash
cd ~/Crows-Nest
bash update.sh
python3 crow.py
```

The update script backs up local life state before a fast-forward-only pull.
It refuses tracked local edits. Refresh the browser with Ctrl+Shift+R after
updating. Your ignored save data remains local and is not published to GitHub.
Backups are under `backups/`; keep an additional copy elsewhere if important.

## iPhone / iPad access (same Wi-Fi)

Your PC remains the AI host. The phone displays the same world and shared save;
no progress is transferred or duplicated. The PC must remain on with Crow running.

Stop Crow with Ctrl+C before switching modes, then:

```bash
cd ~/Crows-Nest
python3 crow.py --lan
```

Open the complete **Phone link** printed in that terminal in Safari on your
phone, connected to the same Wi-Fi as the PC. Keep the `#token=...` part when
copying the link. The link grants access to Crow's private life state and
pause control, so keep it private. A new link is generated on each server start.
The desktop link printed in this mode includes the same token.

Use the left thumb pad to walk and drag the world to look around. **Journal**
opens the scrollable side panel; **Close** returns to the world. **Find Crow**
moves your observer camera near him. Your camera sends him no commands.

Optionally use Safari's Share menu to add the page to your Home Screen. This
is a browser interface, not local iPhone AI or an offline app. Access away
from home is not configured; it needs a private remote connection. Do not
forward port 8765 on your router. If the phone cannot connect, verify the
PC's Wi-Fi address and any existing firewall restrictions before changing them.

Without `--lan`, Crow remains accessible only on the PC as before. No local
save data is uploaded to GitHub.

## What is in this version

- Real UK clock and approximate seasonal daylight; real-duration sessions.
- Saved experiences, subjective reflections, interests, wishes and projects.
- A Wikipedia library with local article copies and source links.
- Simple sculptures, practice counters and a limited toolset.
- A reading cabin with shelves, warm light and a chair.
- Model-selected reading posture: chair, standing or floor; jointed movement,
  book pickup/return, sitting and page turning animate the chosen posture.

The mobile update adds touch movement/look, a collapsible journal and authenticated LAN access.

The chair is optional. The animation executes Crow's selected posture; it
does not choose a preference or assign a comfort response. A general dynamic
interactable world is the next architecture milestone, not implemented yet.

## Local data

Keep `crow-save.json`, `crow-events.jsonl`, `crow-reading/` and any
`crow-save-before-*.json` backups. They are ignored by Git.
Copy `crow-config.example.json` to `crow-config.json` to adjust session lengths.
Those are human-scale estimates, not an exact duration for every possible task.

The clock continues while the app is closed, but activities do not advance
offline. Emotions are simulated variables; adaptation is saved memory and
preferences, not model-weight training or evidence of consciousness.

## Checks

```bash
python3 tests/test_simulation.py
node tests/animation.mjs
python3 tests/test_mobile.py
node tests/touch.mjs
```

Tests cover backend state/timing and Three.js animation logic with a stub
renderer. They do not replace visual testing in Firefox on the running machine.
Three.js 0.170.0 is bundled under its [MIT licence](vendor/THREE-LICENSE.txt).
