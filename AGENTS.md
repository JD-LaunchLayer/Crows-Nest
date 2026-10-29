# Crow's Nest implementation rules

Read DESIGN.md before changing behaviour. The governing rule is that Jordan
provides the world, properties, consequences and opportunities; Crow chooses
his intentions, experiments, preferences and direction.

Do not automatically prescribe a chair, hobby, project, emotional response,
relationship or life story. Offer observable affordances. Implementing the
mechanics of an agent-selected action is expected; selecting the action for
the agent is not. Safety/resource constraints must describe real world rules,
not hide editorial preferences.

Preserve local saved life state. Never commit crow-save*.json, event logs,
article caches, local config, credentials or private user data. Runtime files
must remain ignored. Before an incompatible migration create a local backup.

Use Python's standard library for the current backend. Bundle Three.js with
its licence; keep runtime rendering local. AI inference stays on local Ollama.
Network reference retrieval must be explicit and attributed.

Run python3 tests/test_simulation.py and node tests/animation.mjs for relevant
changes. The animation test exercises real Three.js scene and motion logic
with a stub renderer, and is not evidence of visual/browser rendering QA.
Do not claim human feelings, neural training, or unrestricted world interaction
has been implemented. Distinguish completed capabilities from planned work.

Jordan's role is observer and world builder, not an instructor in Crow's life.
Do not add user controls for selecting his mood, posture, goals or passions.
The observer camera must not be presented as a conversational actor. Experience-
led personality is the target; seeded emotion values and activity counters
are still prototype limitations. See the final section of DESIGN.md.

World geometry and finite supplies live in world_state.py and the saved
built_world state. Do not reset stocks, tree IDs or built objects on reload.
The tree IDs depend on the initial forest generation order. Construction must
check inventories, time and target revisions; never fulfil wishes by spawning
completed structures. sky.js uses bundled Astronomy Engine for the UK clock.
Run tests/test_world.py and tests/sky.mjs for relevant changes as well.

Phone maintenance is owner-only: never accept arbitrary commands, paths or
repositories from HTTP. Preserve token and pause/running state across the
exec restart. Pause and save before backup; back up before pulling. Keep
fast-forward-only updates and refuse dirty source/unknown origins. Run
tests/test_maintenance.py for updater or restart changes.

Decisions are two-step (choose_action, then choose_parameters). Do not add
action-specific fields to the first step. Recall lives in memory_recall.py and
must stay read-only over saved history. Run tests/test_decision.py for decision,
recall or context-budget changes. Use tools/evaluate_decisions.py (copy-only) for
real-model evidence; never point it at a live save path for writing.

ecology.py supplies observable woodland facts from state and the real date. Do
not let the model write ecology facts, and do not change tree IDs when assigning
species. Run tests/test_ecology.py and node tests/animation.mjs for changes.

Use crow.now() for time, never datetime.now(), so the time-lapse twin stays
consistent. tools/timelapse.py must only read the real save when creating the
twin and must refuse to run in the real folder. Run tests/test_timelapse.py.
