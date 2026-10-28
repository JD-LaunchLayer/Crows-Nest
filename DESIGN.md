# Crow's world

Jordan provides the world. Crow chooses his life within it.

## Governing requirement

Crow should perceive a changing, interactable environment and choose what to
try. The environment should supply properties, constraints and consequences,
not instructions about which objects to use or which ambitions to have.

An unfamiliar chair is an object to notice, inspect, test or ignore. Comfort
is something Crow may evaluate through experience. Reading must not imply
sitting in a chair. The world may support sitting, standing or sitting on the
floor; his model chooses. Animation carries out a chosen action, rather than
making the choice. Do not silently label the chair as a favourite or award
happiness simply because the developer expects him to like it.

This principle applies across the world, not just to the library. Jordan may
introduce opportunities in response to Crow's wishes, without forcing him to
use them. His initial elf identity does not fix his future hobbies.

## Intended architecture

- A persistent world state describes objects, locations, physical properties,
  condition, resources and changes over time.
- Perception gives Crow observations grounded in that state. Nearby objects
  expose inspectable properties; unfamiliar objects need not disclose all
  their uses immediately.
- General tools allow inspection, movement, manipulation and experimentation.
  The model selects targets, actions and intentions. The execution engine
  enforces constraints and records actual results, including failures.
- Memory separates observed events from beliefs and subjective interpretations.
  A belief can be uncertain, revised or contradicted by later experience.
- Interests, emotional state, projects and wishes influence choices without
  supplying a predetermined narrative. Projects can be revised or abandoned.
- Wishes may concern things outside current capabilities. Expressing a wish
  does not create an object or pretend an unavailable action succeeded.
- Visual behaviour reflects actual chosen actions and outcomes. Real time,
  effort and resources matter. Activity durations are transparent estimates.

The same world is explorable by Jordan in first person. Visual detail stays
simple and low-poly; a more accurate Crow likeness can come later. Runtime
clock is Europe/London with real day/night. Local inference uses Ollama.

## Current implementation: 0.3.1

A walkable low-poly clearing; local model decisions; UK clock; real-duration
sessions; saved wishes, intentions, session-based projects and reflective
memory; simulated emotional variables; Wikipedia excerpts; simple sculptures.
The reading cabin adds shelves, a lamp and a chair. A new reading decision
explicitly chooses chair, standing or floor. The rig reaches for a book and
animates that selection. Earlier saved reading decisions without a posture
remain standing rather than being silently assigned a chair.

## Not implemented yet

The current action vocabulary and environment description are still mostly
fixed in Python. A general dynamic object registry, perception, experimental
object use, multi-step project verification, awareness of Jordan's presence,
conversation and unrestricted creative tools are not implemented. These are
architectural work ahead, not features implied by the visuals.

Wikipedia currently uses its top search result, which can be irrelevant.
Research needs candidate selection, article relevance checking and correction.
Projects currently count matching sessions; completing research does not
prove a sculpture or larger goal has been completed. Do not present those
counters as general goal verification.

Simulated emotion and memory-based adaptation are not proof of subjective
experience. Local model weights are not retrained. No claim is made that
Crow reproduces Pino's private implementation.

## Observer role and experience-led development (Jordan's clarification)

Jordan observes Crow and can add to the world. He does not select Crow's
posture, mood, interests, passions, goals or projects, and is not a character
giving Crow instructions. Walking around is an observer camera. Wishes are
visible so Jordan can choose whether to introduce an opportunity; introducing
something neither orders Crow to use it nor fulfils a desire by declaration.

Crow's developing personality must be grounded in his own accumulated world
experiences: what he notices, tries, revisits, succeeds at, struggles with and
remembers. Do not author personal likes/dislikes or prescribe an emotional
response to an object or activity. A chair provides physical support; whether
Crow likes it is not a designer-assigned reward. Learning and changing his
mind should be possible, without a predetermined story or end state.

Biological-style needs and world mechanics are authored constraints. Any
starting neutral internal state, model prior or emotional update rule must
be acknowledged as a modelling choice. Do not claim a blank mind, feelings
free of model influence, or fully emergent personality merely because the
model generates a reflection. The existing seeded emotional baselines and
small fixed toolset are prototype limitations to address, not the target.

Future observer interfaces should show expressed wishes, actual actions and
optional evidence/history. They should not offer controls for choosing his
preferences or directing his life. Technical pause/backup controls are for
maintenance, not behavioural coaching.
