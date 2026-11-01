# Experience, methods and a persistent world — 0.16.0

Crow still runs on the Linux host. Closing a phone/browser tab does not stop
the server's simulation. No hosting migration, new inference provider or fee
has been introduced. The existing provider, time-scale and pause settings are
preserved. Stopping the host still stops active experience; no offline life is
invented when it restarts.

## What this builds on

The current repository already had protected relevance-ranked memory, separate
action/parameter decisions, sleep-time consolidation, a time-lapse twin, web
research, trade, Edda, building practice and tool wear. Those systems remain.
This update does not replace them with an unrelated framework.

Architectural references: [Generative Agents](https://github.com/joonspk-research/generative_agents)
for recall/reflection, [Voyager](https://github.com/MineDojo/Voyager) for tested
reusable procedures, [Mindcraft](https://github.com/mindcraft-bots/mindcraft) for
action execution, and [Bunnyland](https://github.com/thalismind/bunnyland-server)
and [CYMONIA](https://github.com/SignalLayerLabs/CYMONIA) for authoritative world
consequences. The new code is an original bounded implementation for Crow;
none of their runtimes or personalities is installed.

## Memory continuity

Existing keyword relevance, importance and recency ranking is retained. It is
not semantic embedding search. New physical attempts and reported interest
episodes are recallable with their actual source IDs. A source, an observation
and an interpretation are not collapsed just because they share wording. A
conservative polarity guard preserves otherwise similar notes containing a
negation. This is not a general contradiction detector.

Relevant memory is also supplied to the chosen action's details call, using
the intention he just chose instead of only his previous intention. Generic
action selection does not acquire carving, posture or geometry fields.
Consolidated skill notes are explicitly interpretations, not certified skills.
The stale instruction that no people/shop/currency existed is removed; the
actual current world's information is authoritative.

## Physical operations

Crow can choose `interact`, then a primitive and its targets/method:

| Primitive | Actual result | Constraints / authored time |
|---|---|---|
| `shape` | A paid, measured solid made from inventory, with his name and dimensions | Available blades currently work wood; 0.1–20 kg; box/cylinder/cone/sphere/wedge/arch; nominal 30 min/kg, at least 30 min |
| `split` | Two independent solids, with the original ID retained for one | A loose single wooden box-shaped blank, axe required, each width at least 3 cm; 20 min |
| `stack` | A saved arrangement containing both original solids | Two loose portable objects; a suitable flat face; no overhang/obstruction; total at most 20 kg; 10 min |
| `place_on` | An object rests at a real face's height, remains independently movable | Portable object, flat unobstructed face, no overhang; 3 min |
| `sit` / `lie` | Chosen posture on a particular object face | Reachable face with enough support area; 15 min |

These are transparent simulation estimates. Existing fatigue, darkness and
tool-wear rules slow relevant work. Sitting/lying receive resting effort, not
an automatic emotional reward. Long work still offers Crow a continuation
decision. Quick Wikipedia research remains quick.

Shaping chooses a mass, width and depth; height is derived from the material
density and shape volume. Width deviation depends on actual motor practice,
fatigue, blade condition and the chosen support/passes. Height compensates for
width deviation to conserve the paid mass. No reading or reflection adds motor
practice. There is no staged unlock of favourite shapes.

Dividing and stacking preserve material in visible solids rather than adding
free inventory. Absorbed objects retain empty records with a `consumed_by` link;
loading must not regenerate them. Transformed/absorbed carvings cannot be sold
as additional intact carvings. Failed operations commit no partial geometry or
material changes. Target revisions are checked again at completion.

Objects resting on a support must be moved off before the support is carried
or supporting geometry is removed. Carrying a supported object elsewhere puts
it on the ground instead of leaving it at its old table height.

The reading chair, bed and workbench replace their existing static renderings
with saved geometry once. Existing matching objects are preserved. The chair
can be moved; reading animation follows its position. Other furnishings and
some scenery remain static. Geometry-derived properties do not make every
conceivable object interaction supported.

Stacking is an arrangement, not a simulated adhesive, fastener or structural
joint. There is no arbitrary mesh editing, full gravity, chemistry, cooking,
ore processing or general tool invention in this update. Spatial actions still
use timed macros and structured state, not full motor control or pixel vision.

## Reusable methods

Before work, the decision can include his hypothesis, predicted outcome and
an existing procedure ID. Only a procedure's parameters are reused; new target
IDs come from his current decision and are revalidated. Each executor outcome
records the exact parameters, success/failure, geometry/material measurements
where available, affected object IDs and source event ID.

The same parameters accumulate evidence across actual attempts. A successful
method can later fail if materials run out, a surface changes or a new target
does not fit. Failed attempts remain visible. Existing carving and building
practice are retained; basic woodworking shares motor practice with carving.

This is a library of typed single-operation procedures. Crow can combine them
by choosing subsequent actions. It is not a self-written multi-step program,
arbitrary code execution, model-weight training or proof of general learning.

## Developing interests without declaring passions

`interest_history` holds up to 48 topic trails and 80 episodes per topic. The
full event log remains separate. Each episode records:

- His reported feeling/enjoyment, which can be positive, neutral or negative.
- The actual source event, chosen action, intention and original choice ID.
- Whether the source/observation supplied new evidence.
- Whether a physical operation succeeded or failed, separately from enjoyment.

The decision context and journal present those observations instead of bare
interest scores. Repeated reading is labelled even if his reported response
changes. A return does not automatically mean passion: he might be frustrated,
curious, stuck, practising or passing time. No threshold prescribes an action,
interest or personality. Earlier scores/notes are retained; missing history is
not retrospectively invented.

## Observation over days

The read-only owner report is available at authenticated `/api/behaviour` or:

```bash
python3 tools/behaviour_report.py --days 7
```

The command reads the save and available event log; it never changes either,
invokes a model or creates another Crow. It reports daily choices, memory
citations, repeated sources, attempted/reused methods, failures and real object
changes. Within-method width measurements make changes observable. Topic
trails separate reported feeling from return behaviour and physical results.
Indexes are bounded, so the report identifies its coverage. It contains private
history; it is not committed or automatically uploaded anywhere.

For actual-model comparisons the existing `tools/evaluate_decisions.py` works
on a temporary copy. The separate `tools/timelapse.py` can observe a divergent
copy over simulated days; it must not overwrite the real Crow. Neither should
be run implicitly against a person's live life. Mechanical tests use fixed
responses/fixtures and do not demonstrate spontaneous interests or sustained
real-model autonomy. Those need assessment on the running host over time.

## Upgrade and checks

Before converting an older save, startup writes its original bytes to
`crow-save-before-v0.16.json`. Saves, pending work, material stocks, creations,
memories and private configuration are retained. Migration does not fabricate
past procedure measurements or interest trails. The existing phone updater
also backs up before pulling and preserves the running/paused state.

Tests cover atomic failures, material conservation, changed-target refusal,
reusable methods on real targets, finite stock, posture without an emotional
bonus, dependency-aware placement, save/reload progress, migration backup,
contradictory recall, interest trails across dated fixtures and read-only
reporting. Scene tests exercise real Three.js with a stub renderer; they do not
replace visual testing on the Linux PC and iPhone.
