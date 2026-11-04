"""Where things are, said as a person would (v0.35.0): from where he stands and which way he faces, never in numbers.

"ahead of me", "to my left", "behind me and to the right"; "within reach", "a few steps away", "a short way off",
"a good way off", "far off". Bearings and distances are worked out from the world's numbers and then thrown away.
Heading: radians, 0 facing north (-z), increasing clockwise (east = pi/2), as layout.py stores it.
"""
import math


def bearing(x, z, tx, tz):
    """Direction from (x, z) to (tx, tz) in the same convention as a heading."""
    return math.atan2(tx - x, -(tz - z))


def relative(heading, x, z, tx, tz):
    """Angle of the thing from straight ahead, in degrees: negative to his left, positive to his right."""
    a = math.degrees(bearing(x, z, tx, tz) - heading)
    return (a + 180) % 360 - 180


def direction(rel):
    side = 'left' if rel < 0 else 'right'
    a = abs(rel)
    if a < 25:
        return 'ahead of me'
    if a < 70:
        return f'ahead of me and to my {side}'
    if a < 110:
        return f'to my {side}'
    if a < 155:
        return f'behind me and to my {side}'
    return 'behind me'


def distance(d):
    if d < 1.5:
        return 'within reach'
    if d < 4:
        return 'a few steps away'
    if d < 10:
        return 'a short way off'
    if d < 25:
        return 'a good way off'
    return 'far off'


def where(heading, x, z, tx, tz):
    """'ahead of me and to my left, a short way off'."""
    d = math.hypot(tx - x, tz - z)
    if d < 1.5:
        return 'within reach'
    return f'{direction(relative(heading, x, z, tx, tz))}, {distance(d)}'


def height(h):
    """A tree or a thing's height against his own (he is about one and three-quarter metres)."""
    if h < 1:
        return 'low'
    if h < 2.2:
        return 'about my height'
    if h < 4:
        return 'twice my height'
    if h < 7:
        return 'tall'
    return 'very tall'
