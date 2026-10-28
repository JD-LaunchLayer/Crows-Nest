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
