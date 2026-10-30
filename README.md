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
for t in tests/test_*.py; do python3 "$t"; done
for t in tests/*.mjs; do node "$t"; done
```

Tests cover backend state/timing and Three.js animation logic with a stub
renderer. They do not replace visual testing in Firefox on the running machine.
Three.js 0.170.0 is bundled under its [MIT licence](vendor/THREE-LICENSE.txt).

## v0.4 — persistent world editing and time-based sky

Creations are now saved world objects with stable IDs and positions. Existing
carvings keep their locations beside the workbench. Crow can choose to inspect
an object, carry a portable creation to another location, prepare construction
plans, or work on a plan. These are model-selected tools, not assigned projects.
His elf appearance no longer supplies a personality or preferred hobby.

A construction plan contains actual bounded solid geometry, a site, a material
bill and an estimated work duration. Planning does not create the object. Crow
must choose to construct, have enough material, and spend the work time. Larger
jobs use sessions of at most two real hours with saved progress. Materials are
charged once when the plan completes. He can choose other activities between
sessions. Plans may create objects, add parts to an existing structure or remove
a part. The library shell is editable geometry; a real wall can be removed to
make an opening. Removing a part recovers half its modelled material mass.

Wood and stone supplies are finite. Initial world opportunities are loose wood,
loose stone and an axe; providing these does not direct Crow to use them. Each
standing tree has an individual finite yield. Felling with the axe takes a
90-minute session and leaves a stump plus timber at the site. Gathering takes
material from that source into inventory. Trees do not instantly respawn or
regrow. Existing wood units migrate as kilograms, and legacy carvings are sized
as small one-kilogram works. Construction density is modelled as wood 500 kg/m³
or stone 2200 kg/m³. These are transparent gameplay estimates, not engineering
validation or exact durations for every real-world tree/build.

The sky uses the local PC clock and Wickford's approximate coordinates
(51.61 N, 0.52 E). Sun and moon positions are calculated using bundled Astronomy
Engine 2.1.19; sunrise, sunset and lunar phase follow date/time. Twilight and
moon phase shading are rendered locally. Celestial disc sizes are exaggerated
for visibility. Stars are decorative, not a star catalogue. No online sky API
or additional AI fees are involved. See vendor/ASTRONOMY-LICENSE.txt.

### Limits of this milestone

This is bounded geometry and resource accounting, not unrestricted world physics.
Available building materials are wood and stone, and plans use up to eight
basic solid parts at a time. Additional parts can be added in further plans.
The renderer supports collision changes, but not structural load calculations,
falling/unsupported structures, weather damage or a general crafting chemistry.
Some furnishings remain static scene props. Observation is area-based structured
state, not pixel vision. Carrying/building is a timed macro with basic poses,
not a full physical animation of every step. Construction is not guaranteed
useful, stable or aesthetically good merely because geometry is valid.

Session milestones in reading/planning no longer claim a larger physical goal
is complete. Existing historical project records are preserved. The broader
experience-led personality/learning architecture remains development work;
this release provides concrete world effects and resources for it to build on.

Updates create crow-save-before-v0.4.json before migration. New state remains
inside the ignored crow-save.json; nothing about Crow's private life is uploaded.

Additional checks:

```bash
python3 tests/test_world.py
node tests/sky.mjs
```

These include material conservation, tool requirements, tree stock/stumps,
insufficient-material refusal, resumable construction, double-spend prevention,
placement collision, library editing/salvage, state persistence and astronomical
position/scene calculations. Browser shader rendering and model-generated v0.4
decision quality still need validation on the running PC and phone.


## v0.4.1 — phone maintenance

In the phone's **Journal**, **Maintenance → Back up and update** pauses Crow,
saves his current activity progress, copies his life files into `backups/`,
and pulls `origin/main` with fast-forward-only Git. If code changed, the same
Python process is replaced by the updated program and the previous pause/running
state is restored. The phone token survives this automatic restart, so existing
links remain valid. The page reconnects and reloads when the app version changes.
A normal manual restart still generates a new token as before.

The control requires the authenticated `--lan` mode and a valid token. It accepts
no commands, repository URLs or file paths from the browser. The updater checks
that the process runs at the checkout root, on `main`, with the configured
Crows-Nest origin and no tracked source edits. Diverged histories and local edits
are refused, not reset or overwritten. Multiple requests cannot run two updates.

If something fails, Crow remains running but paused, with the error shown in the
journal. His backup path is recorded in the ignored `crow-update-status.json`.
Inspect the problem on the PC before retrying. This backs up life data; it does
not promise an automatic source-code rollback if a future release cannot start.
The owner phone link now grants update access as well as pause access; keep it
private and use it only on your private home network.

**One initial Terminal update is necessary to install this feature:** stop Crow,
run `bash update.sh`, then `python3 crow.py --lan`. Keep that terminal or process
running. Grok with actual local shell access can perform this setup; a chat
without machine tools cannot. Updating a remote Git repository alone does not
update the running PC.

Check the maintenance path with:

```bash
python3 tests/test_maintenance.py
```

Tests exercise a real local Git remote and backups, refusal paths, authenticated
HTTP requests, update exclusivity and the restart token/resume contract. Full
self-restart and reconnect still need verification on the running PC/phone.


## v0.4.2 — quick research and a clearer journal

Crow can choose quick research, which waits only for Wikipedia retrieval and
local model processing, or leisurely reading, which uses the configured read
session duration. The UK clock and physical work durations are unchanged. A
saved older reading session without a mode becomes a quick lookup on upgrade;
its retrieved source is preserved.

The Journal now includes a **Reading notebook**: article links, the research
question and purpose, Crow's source summary, his personal note, whether he
thinks the question was answered, and a tentative next step. **View excerpt**
shows the saved text; new processed entries identify the exact excerpt length
supplied to the model. **Load earlier reading** opens older history. Old cached
sources are recovered without fabricating summaries or future plans.

The current activity shows its source/question or target object, construction
plan, material bill, work progress, and start time when applicable. **Tentative
next step** is Crow's own revisable intention, not a queued instruction. The
activity feed also records his stated aim and reason. Processing a completed
experience survives pause/restart and is not applied twice on retry. These are
observer views, with no controls for choosing his interests or behaviour.

Notes remain model-generated interpretations. Researching a topic does not
grant practical skill or finish a physical project. Article selection still
uses Wikipedia's first search result. Quick research need not prevent Crow
from choosing further research; there is no forced activity schedule.

The proposed [master prompt and life-system brief](docs/CROW_MASTER_PROMPT.md)
are included for review and future implementation. That document is not loaded
as the runtime prompt in this release; hunger, food, cooking and the richer
emotion/learning architecture described there are not yet implemented.

Additional checks:

```bash
python3 tests/test_research.py
node tests/journal.mjs
```


## v0.5.0 — a first causal learning and bodily-needs loop

This milestone connects actual attempts, predictions, fatigue and future choices.
It is deliberately limited to a measurable carving domain, not general human
learning, consciousness or unrestricted physical simulation. The compact runtime
policy now starts Crow curious and kind, without assigning a hobby or occupation.

- Food, hydration, digestion, sleep pressure and exertion advance from active
  elapsed time and effort. A finite provisions chest, slowly renewing fruit
  bushes and a replenishing spring basin are present before needs are enabled.
  Their objects appear in the 3D world. Crow chooses whether and when to eat,
  drink, rest or sleep; no needs threshold assigns an activity.
- Long physical activities get a model-selected continuation review every 15
  minutes. Crow can pause with progress saved and choose `resume_work` later.
  Pausing for maintenance or closing the program advances no bodily needs,
  supplies, learning or emotional decay.
- Before a new carving attempt Crow can choose a hypothesis, predicted success,
  expected width error, tolerance and working method. If the main choice omits
  that prediction, a short local model call supplies it before work starts.
- Working support, pass type, direction, accumulated motor practice and current
  fatigue determine a bounded width deviation. The actual saved workpiece has
  that width; its height compensates to preserve the paid kilogram. A missed
  tolerance still leaves a real rough workpiece and spends its material.
- Tested parameterised carving methods retain outcomes, source event IDs and
  shapes tested. Crow can choose to reuse them on another supported shape.
  Practical control improves through performed work; reading never increments
  it. Legacy session counters are retained as history, not certified expertise.
- Reflections appraise the particular outcome against Crow's own concern.
  Valence/arousal signals retain their event references and fade over active
  time. The old fixed happiness baselines and activity-specific emotional
  bonuses are not used by the new process. Generated interpretations remain
  subjective model reports, not proof of human feelings.
- The Journal adds body signals, available provisions, current predictions,
  measured results, possible corrections, paused work and tested-method evidence.
  These views offer no owner controls for his decisions or personality.

Existing saves migrate in place with `crow-save-before-v0.5.json` saved first.
Old objects, resources, memories, wishes and partial work are retained. No past
prediction or measured skill is invented for older activities.

See [the mechanics and limits](docs/LIFE_LOOP.md). The expanded master-prompt
brief remains a target; this implements only a first portion of it. Cooking,
cleaning, injury/illness, structural physics, arbitrary tool invention and
self-written general action programs are not implemented. AI inference stays
on local Ollama; no new pip packages or paid APIs are needed.

New checks:

```bash
python3 tests/test_life.py
node tests/life_view.mjs
```


### Repeated research and irrelevant search results

Wikipedia now returns up to five search candidates for Crow to assess against
his actual question. He can reject them all; a no-match records honest feedback
instead of pretending reading succeeded or completing a milestone. Task questions
use quick lookup even if the model also selected leisure timing. Genuine leisurely
reading with no task question remains available.

The decision context shows source consultation counts, latest answers and failed
search feedback. Repeated excerpts have content fingerprints and are labelled
in the notebook. Their interpretations remain visible, but the same source text
cannot repeatedly boost interest scores or add fresh long-term lessons. Existing
history is retained. Older completed read/plan projects are annotated as research
milestones, not claimed physical completion. These changes address a feedback
loop; they do not assign a different hobby or force a particular next activity.

```bash
python3 tests/test_research_loop.py
```

## v0.6.0 — two-step decisions and protected memory

**Why.** On a long-running life the 0.5 decision prompt trimmed recalled
memories, lessons, recent events, personality notes and projects *first*
whenever it grew past its character limit. Measured on a synthetic save with
500 events, 120 lessons and 40 readings (`tests/lived_fixture.py`, not Crow's
real save), all five were cut to zero while the world description was kept.
Every decision also had to fill 27 fields (carving shape, reading posture,
build coordinates…) even when he chose to sleep.

**What changed.**

- Deciding happens in two steps. First Crow chooses his action, intention,
  reason, optional wish, project choice and next step (9 fields, 320 output
  tokens). Only then is he asked for details of that one action, with only the
  context it needs: carving method and prediction for `craft`, search terms
  and posture for `read`, a tree for `fell_tree`, and so on. Rest, sleep,
  observe, reflect, explore and practice need no second call. The details step
  cannot change the chosen action.
- `memory_recall.py` ranks his whole saved history — outcome events, lessons,
  appraisals, processed readings, measured trials and failed searches — by
  shared rare words with his current intention, next step and active project,
  plus small importance and recency bonuses. Each item keeps its source ID and
  a type label (event, reading, lesson, appraisal, trial, search_miss).
  Identical texts are recalled once. This is keyword relevance, not semantic
  search: a paraphrase with no shared words can still be missed.
- The decision context has a priority order. Body, intention, recent events
  and recalled memories are trimmed last; nearby-object lists, interests and
  wishes are trimmed first. On the same synthetic save the first-step prompt is
  about 6,700 characters (roughly 2,100 tokens by estimate) and keeps every
  protected section.
- `recent_pattern` reports counts of recent choices, how many decisions share
  the current intention, and how many recent readings did not answer or
  repeated an excerpt. These are observations only; no threshold triggers
  anything.
- Actions the world cannot currently carry out are not offered: `construct`
  with no open blueprint, `resume_work` with no paused job, `move_object` with
  nothing portable (and, as before, `craft` without wood).
- Crow may list `memory_ids_used`. Only IDs that were actually shown are kept,
  and they are saved on the "started" event together with `recalled_ids`. This
  is a self-report of citation, not proof that memory caused the choice.
- Reflections receive related memories from the same recall rather than the
  three most recent lessons.
- Every model call records Ollama's real `prompt_eval_count`/`eval_count` in
  `runtime.model_usage`, with a flag if prompt plus output limit approaches
  `num_ctx`. `CROW_NUM_CTX`, `CROW_CONTEXT_CHARS` and `CROW_MEMORY_CHARS` can
  be set in the environment.

Saved history is not rewritten. Older pending decisions keep working, because
the two steps are merged into the same decision format as before.

### Measuring it with the real model (read-only)

```bash
python3 tools/evaluate_decisions.py --context-only        # sizes and what recall surfaces
python3 tools/evaluate_decisions.py --samples 6           # Qwen decisions with vs without recall
python3 tools/evaluate_decisions.py --samples 6 --perturb empty_pantry
```

The script copies the save to a temporary folder. It never writes to the live
save or event log, starts no actions and fetches nothing from Wikipedia. A few
samples are suggestive, not statistically conclusive.

```bash
python3 tests/test_decision.py
```

## v0.7.0 — a woodland that can actually be observed

**Why.** Real-model evaluation on Jordan's PC (v0.6.0) showed Crow choosing to
observe the woodland to find "visible plant interactions" for a sculpture. In
0.6 that action only recorded "Spent time watching the woodland without
collecting anything": there was nothing in the world to notice.

**What changed.**

- `ecology.py` gives the existing trees species (oak, hornbeam, silver birch,
  hazel, ash, holly), assigned once from their IDs without changing IDs, stocks
  or positions, and adds plants: ivy, bramble, bracken, bluebell, wood anemone,
  male fern, moss, nettles, honeysuckle, holly seedlings, fly agaric and grass.
  It is an authored south-east English mixed woodland, like the spring and fruit
  bushes, not an ecological simulation.
- What is visible follows the real UK date: leaf colour and fall, ivy flowering
  with insects in autumn, bluebells only above ground from late winter to early
  summer, toadstools in autumn, and so on. Dates are typical UK approximations.
- Ground light is calculated from the actual standing trees and their seasonal
  leaf cover. Felling a tree really opens the canopy there, and ivy on a felled
  tree is reported lying on the stump.
- `observe` now asks where to look (grove, woodland edge, spring side or
  clearing) and an optional focus. Things matching his focus are likelier to be
  noticed, but one incidental detail outside it is always included, and in the
  dark little can be seen. Each finding is marked new or already seen.
  Observations describe what is visible, not causes; interpreting is his job.
- `inspect` also works on trees and plants by ID.
- Each finding is separately recallable (`observed` memories). Recall now
  merges reworded near-duplicates and limits how many items of one type appear.
- The 3D view colours tree crowns by species and season, thins them as leaves
  fall, and shows simple low-poly clumps for visible ground plants.

**Not yet:** plants do not grow, spread or respond to his actions over time
(apart from light), there are no animals beyond the insects on ivy flowers, and
weather/temperature are not simulated.

```bash
python3 tests/test_ecology.py
```

## v0.8.0 — long-life memory and the time-lapse twin

- The save now keeps the latest 3,000 events (was 500), 400 lessons and 400
  appraisals (were 120/100), so recall can reach months of history. Older
  events keep their source reference, but their copy of a Wikipedia excerpt is
  dropped once it is safely in `crow-reading/`, keeping the save small.
- `crow.py` reads time through one `now()` function. The live Crow always uses
  the real UK clock; only the twin replaces it.

### Time-lapse twin (separate copy, fast-forward clock)

```bash
python3 tools/timelapse.py --days 14          # pilot: two simulated weeks
python3 tools/timelapse_report.py             # month-by-month summary → ~/crow-twin/report.md
python3 tools/timelapse.py --days 548         # continue to about 18 months (resumable with Ctrl+C)
```

The twin is created once from a copy of the real save in `~/crow-twin` and
never writes to the real Crow. Its clock jumps forward as activities finish;
model inference takes real time and that time passes for the twin too. Nobody
adds resources during the run; Wikipedia lookups are real. On a GTX 1060 with
qwen3:4b, expect very roughly 15–20 minutes of processing per simulated day
(about a week for 18 months); it shares Ollama with the real Crow.

The report counts, per simulated month: decisions and main actions, distinct
intentions and the longest same-intention run, how often he cited a memory and
how often that memory was more than a week old, unanswered/repeated readings,
failed searches, new observation details, carving results, projects, wishes,
self-observations, lessons, interests and world resources. It is one run of
one small model, not a prediction of the real Crow.

```bash
python3 tests/test_timelapse.py
```

## v0.8.1 — no lessons from nothing new

The first twin pilot started at dusk. Crow observed eleven times in the dark,
noticed nothing new each time, and still recorded six reworded lessons and
self-observations praising darkness ("darkness enhances minimalist focus…").

- An observation that produced no new detail is saved as an event and still
  appraised, but, like a repeated reading excerpt, it cannot add long-term
  lessons, interest score or self-observations.
- Lessons, self-observations and project titles are compared by shared words,
  so reworded duplicates are not stored again; a reworded project title
  continues the existing project.
- The decision context states whether it is dark, dim or daylight outside, and
  `recent_pattern` counts recent observations that found nothing new.
- The twin waits in real time when Ollama or the network is unreachable, without
  ageing him or counting it as his failure; it gives up after 30 minutes.
  The live Crow still pauses with an error in that case.

Earlier entries are left as they were.

## v0.9.0 — sleep consolidation and an optional cloud mind

### Memory rewritten while he sleeps

Adapted from the approach published for Pino (pinos.world). After each sleep,
the model rereads that day's actual events against what Crow already holds, in
three sections of at most 24 memories: what mattered and what he believes, how
to do things, and what the world allows. It may add, revise, reinforce or
contradict; `consolidation.py` decides what is admitted:

- every new memory or revision must cite a real event from that day;
- reworded duplicates reinforce the existing memory instead of being stored;
- one word may anchor at most four memories in a section, one pair of words at
  most two (this is what would have stopped the six "darkness" lessons);
- strength halves every three weeks of active life unless reinforced; paused or
  closed time does not fade anything;
- a full section only admits something stronger than its weakest memory, which
  is moved to a visible "forgotten" archive; revisions keep earlier wording.

The event log and per-event lessons are untouched. Held memories reach
decisions (the strongest few always, others by relevance) and reflections. The
journal shows "What he holds in mind", what is closest to fading and what was
recently forgotten. A consolidation failure is recorded and never stops him.

### Claude Haiku 5.5 as his mind (optional), with local fallback

```bash
python3 tools/use_haiku.py        # asks for an Anthropic API key, tests it, saves it privately
python3 tools/use_haiku.py --off  # back to local Qwen
```

Restart Crow afterwards. The key lives only in the git-ignored
`crow-config.json` (readable only by your user), never in his save or the
browser view. With Haiku his decision context is larger. Every call records
real token counts and cost (at $0.10/$0.50 per million input/output tokens).
Real Crow has a daily cap (default $1, set with `--daily-budget`); past it, or
whenever the cloud is unreachable or answers badly, that call uses local Qwen
instead. The journal shows today's spend. The time-lapse twin uses the same
settings with its own whole-run limit (`--max-spend`, default $40) and waits
out local-model outages without ageing.

```bash
python3 tests/test_consolidation.py
python3 tests/test_provider.py
```

## v0.9.1 — Haiku request fix and retry of cut-off local replies

The first live Haiku call was rejected by Anthropic with "400 Bad Request";
Crow correctly fell back to Qwen, whose reply was then cut off mid-answer and
paused him. Requests no longer send a sampling temperature (newer Claude
models reject it), the full reason for any cloud fallback is recorded in
`model_spend.last_fallback`, and a cut-off local reply is retried once with
more room instead of pausing his life.

### Watching the twin

```bash
python3 tools/twin_viewer.py          # then open http://127.0.0.1:8766
python3 tools/twin_viewer.py --lan     # also from your phone (prints a private link)
```

A read-only window onto the twin, using the same 3D world and journal. It
re-reads the twin's save on every refresh, shows the twin's fast-forward clock,
refuses every change (pause, update) and never touches the real Crow on 8765.

## v0.10.0 — his journal, a clearer side panel, a new look

- **Tab opens his journal** (Escape or Tab closes it; "His journal" button on
  phones). It opens with a plain summary assembled by fixed rules from his
  saved state: what he is doing, his mood and body in words, his aim and next
  step, what he has mostly been choosing, and his latest wish. Then his recent
  reflections (each linked to the event it followed), wishes, what draws or
  puts him off, his self-observations, what he holds in mind, projects,
  lessons, reading notebook, practical attempts, methods, things made and
  world objects. Everything is read-only.
- **The side panel now keeps only what is happening now**: activity, aim and
  next step, body, feelings, recent events and maintenance.
- **Activities happen where they are about**: observing goes to the chosen
  area, inspecting and gathering go to the named tree, plant or object, with
  simple inspect and gather poses. In the twin viewer he appears directly at
  each activity instead of endlessly walking, since the twin's clock outruns
  any walk.
- **A new, original elf model**: slimmer proportions, face with eyes, brows and
  nose, silver hair tied back, long ears, teal tunic, rust sash, slate cloak
  and boots. Appearance stays cosmetic and assigns no hobby.

```bash
node tests/diary_view.mjs
```

## v0.11.0 — a steady, faster life (optional), and keeping the twin

```bash
python3 tools/set_speed.py 24        # one real hour per Crow day, like Pino; restart Crow afterwards
python3 tools/promote_twin.py        # with Crow stopped: make the twin's life his life (backup first)
```

At a speed above 1 Crow keeps his own calendar, starting from the present: his
sun, seasons, plants, body, activities and memory fading all follow it while he
runs. Nothing advances while he is paused or closed, and his calendar is never
wound back (setting speed 1 later keeps his own date at normal pace). The
header shows "Crow's time (24× speed)". Cloud spend rises with speed; raise the
cap with `python3 tools/use_haiku.py --daily-budget 3` (answer "N" to replacing
the key).

`promote_twin.py` backs up the real save, events and reading archive to
`backups/before-twin-<time>/`, copies the twin's life in, keeps the twin's date
as his clock, keeps the real-world spending record, and adds an event stating
that his life continued from the twin.

```bash
python3 tests/test_speed.py
```

## v0.12.0 — an internet café, a trading post, and a few unexplained things

- **Internet café** (north of the clearing). `browse` runs a real web search
  (DuckDuckGo's HTML page, or the Brave Search API if `brave_api_key` is set in
  `crow-config.json`), lets Crow choose a result or none, reads the page and lets
  him follow one link. Pages are stored like library readings (mode "web") with
  their URL. Only public internet addresses on ordinary ports are opened, also
  after redirects (never this PC or the home network); robots.txt is respected;
  pages are capped in size and treated as untrusted text. The library stays
  Wikipedia-only. DuckDuckGo may refuse automated visitors; that shows as an
  honest failed search, and a Brave key is the fix.
- **Trading post** (unattended, with posted rates and a credit ledger). `trade`
  can buy stock, sell wood (3 kg = 1 credit), stone (5 kg = 1) or his carvings
  (1–3 by quality), do a posted job (30 or 60 minutes of work for 1 or 2
  credit), or ask for something to be stocked. Starting stock: provisions
  bundles (+4 servings), an oil lantern (lets him make out a little detail when
  observing or inspecting in the dark) and a whetstone (narrows carving error).
  Requests are recorded, not fulfilled. Restock while he runs:

  ```bash
  python3 tools/stock_shop.py                       # stock, his credit, his requests
  python3 tools/stock_shop.py add sketchbook "Sketchbook and pencils" 5 2 possession:sketchbook
  ```

  Effects are `pantry:N` or `possession:NAME`; possessions without a built-in
  use are simply owned, with nothing invented about them.
- **Unexplained things**: a weathered stone figure, a bronze dial on a plinth,
  a ring of standing stones and hanging tubes on a frame. Inspecting them gives
  only what can be seen (the dial's shadow position follows his clock); what
  they are or mean is for him to work out.
- The journal has an "At the trading post" section: credit, possessions, his
  requests and the last transaction.

```bash
python3 tests/test_town.py
```

## v0.12.1 — steadier with the cloud model

From the first Haiku twin run (5 simulated days, 60 form errors):

- Haiku's structured answers are fitted to the requested form: small slips
  (a missing note, a null project number, an unknown project choice) get
  neutral values; answers that cannot be fitted fall back to local Qwen.
- The live Crow retries after a bad answer or brief outage instead of pausing;
  only eight failures in a row pause him, with the error shown.
- Reworded interest topics strengthen the existing interest instead of
  splitting into near-duplicates.
- `promote_twin.py`, `set_speed.py` and `use_haiku.py` refuse to run outside
  the folder where Crow's save lives.

## v0.13.0 — furnished buildings, Edda Thorne, and work that tires

- **Furnished interiors.** The café has a counter, cups, a table and chairs, and
  a desk with a lit screen and keyboard; the trading post has a counter,
  stocked shelves, crates, a barrel and a slate board. Existing saves are
  furnished once. Furniture is ordinary geometry: he can change it like any
  other structure.
- **Edda Thorne keeps the trading post** (an original character: warm, chatty,
  fair-minded but shrewd, with her own small worries). `talk` is a short
  conversation (up to three exchanges). Edda speaks from her own persona and
  her own memory of Crow, never his thoughts. She may propose one deal at a
  time, which the world checks before Crow even hears it: selling stock (no
  lower than 70% of the board), buying goods he really has (no more than 130% of
  the posted value), a favour (15–180 minutes, pay in line with posted jobs,
  done later as a job) or, rarely, a small gift (≤1 credit, once a day). An
  accepted deal is settled when the talk ends. The journal shows their last
  conversation, how Edda seems to feel about him and her notes about him.
- **Tiredness, hunger and darkness slow work.** Physical work (felling,
  gathering, building, exploring, carving, practice, carrying, jobs) slows
  once he is noticeably impaired, and outdoor work goes at half pace in the dark
  without a lantern; carving by starlight is also less accurate. Resting,
  reading, eating, talking and browsing are unaffected. These are world
  consequences, not points, and they are not explained to him.

```bash
python3 tests/test_keeper.py
```

## v0.14.0 — building skill that grows with practice

Nothing unlocks. Every shape can be attempted from the start — box, cylinder,
cone, sphere, and now **wedge** (a sloped triangular block) and **arch** (a half
ring) — but how true a finished part comes out depends on:

- practice with that kind of shape (straight, turned, angled, curved), with some
  carry-over from building in general; practice accrues only from real time
  spent constructing, more slowly when tired;
- fatigue at the moment of finishing, and darkness without a lantern.

Each part comes out fine, fair or rough, slightly off true in position and
tilt, and a part that is too far off does not hold: half its material is
recoverable as offcuts, half is lost. Typical results from the authored
model: a beginner's arch almost always falls (~19 cm off); after many hours of
curved building most hold (~7 cm); boxes hold from the start (~5 cm, improving
to ~2 cm). Crow sees only his own record — attempts, how many held and how far
off they were, by shape — never the difficulty figures. Construction reports
what held and what came apart.

```bash
python3 tests/test_building.py
```

## v0.15.0 — blades that dull, a whetstone to discover, a lantern you can see

- **Tools wear.** His axe dulls with felling (and a little with gathering and
  building) and his carving knife with carving. A dull axe makes felling and
  chopping slower; a dull knife makes carving rougher. Work results mention
  what he would notice ("the axe kept skidding instead of biting"), and
  inspecting a tool describes its edge, but nothing explains the cause.
- **`use_item`** lets him use anything he owns, on one of his tools or on
  nothing, in his own words. Only real mechanics change anything: a whetstone
  used on a blade restores its edge after 20 minutes of work; used on nothing,
  nothing happens. Owning a whetstone no longer helps by itself. Inspecting it
  shows only a flat, fine-grained grey stone.
- **Edda knows what her goods are for** (light after dark; sharpening dulled
  blades; food that keeps). Crow is never told; he can ask her.
- **The lantern** lights automatically when it is dark and he owns one: he
  carries it, and it casts real light in the 3D scene. Its effect on outdoor
  work and on seeing detail is unchanged and still unexplained to him.
- **Sleeping and resting in the cabin.** He walks into the cabin and lies down
  in his bed under a blanket, breathing slowly, instead of vanishing; resting
  sits him on the edge of the bed. Opening the page mid-activity now shows him
  where he already is rather than walking there.

```bash
python3 tests/test_tools.py
```
