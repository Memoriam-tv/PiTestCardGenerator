"""Static test card backgrounds: Philips PM5544 and BBC Test Card F styles."""

import math

import pygame

from . import layout as layout_mod
from .layout import COLS, ROWS, Layout

# A card image's middle circle is found by walking out from the centre until
# the flat field colour takes over for FIELD_RUN pixels in a row.
FIELD_TOL = 18
FIELD_RUN = 10
RAY_MIN = 24  # of the 72 rays cast, how many must agree on a circle

GREY = (128, 128, 128)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

STAIRCASE = (0, 51, 102, 153, 204, 255)

# EBU 75 % colour bars (75 % amplitude, 100 % saturation).
BARS = (
    (180, 180, 180),
    (180, 180, 0),
    (0, 180, 180),
    (0, 180, 0),
    (180, 0, 180),
    (180, 0, 0),
    (0, 0, 180),
)

# Stand-ins for the 0.8/1.8/2.8/3.8/4.8 MHz sine gratings: stripe periods are
# cw / f pixels, so frequency rises left to right.
GRATING_F = (3, 5, 8, 12, 18)


def _row_span(layout, row):
    """Pixel rect of interior grid row ``row``, spanning cols 1..16."""
    x0 = int(round(1.0 * layout.cw))
    x1 = int(round(16.0 * layout.cw))
    y0 = int(round(row * layout.ch))
    y1 = int(round((row + 1) * layout.ch))
    return x0, y0, x1 - x0, y1 - y0


def _draw_grid(surf, layout):
    lw = layout.line_w
    for col in range(COLS + 1):
        x = int(round(col * layout.cw)) - lw // 2
        surf.fill(WHITE, pygame.Rect(x, 0, lw, layout.h))
    for row in range(ROWS + 1):
        y = int(round(row * layout.ch)) - lw // 2
        surf.fill(WHITE, pygame.Rect(0, y, layout.w, lw))


def _draw_castellations(surf, layout):
    for row in range(ROWS):
        for col in range(COLS):
            if not (row in (0, ROWS - 1) or col in (0, COLS - 1)):
                continue
            x0 = int(round(col * layout.cw))
            x1 = int(round((col + 1) * layout.cw))
            y0 = int(round(row * layout.ch))
            y1 = int(round((row + 1) * layout.ch))
            colour = WHITE if (row + col) % 2 == 0 else BLACK
            surf.fill(colour, pygame.Rect(x0, y0, x1 - x0, y1 - y0))


def _draw_steps(surf, layout, row, levels):
    x, y, w, h = _row_span(layout, row)
    n = len(levels)
    for i, level in enumerate(levels):
        sx0 = x + int(round(i * w / n))
        sx1 = x + int(round((i + 1) * w / n))
        colour = level if isinstance(level, tuple) else (level, level, level)
        surf.fill(colour, pygame.Rect(sx0, y, sx1 - sx0, h))


def _draw_gratings(surf, layout, row):
    x, y, w, h = _row_span(layout, row)
    n = len(GRATING_F)
    for i, f in enumerate(GRATING_F):
        bx0 = x + int(round(i * w / n))
        bx1 = x + int(round((i + 1) * w / n))
        surf.fill(BLACK, pygame.Rect(bx0, y, bx1 - bx0, h))
        period = max(2, int(round(layout.cw / f)))
        half = max(1, period // 2)
        sx = bx0
        while sx < bx1:
            surf.fill(WHITE, pygame.Rect(sx, y, min(half, bx1 - sx), h))
            sx += period


def _draw_ring(surf, layout):
    pygame.draw.circle(
        surf,
        WHITE,
        (int(round(layout.cx)), int(round(layout.cy))),
        int(round(layout.card_radius)),
        max(2, int(round(layout.ch / 10.0))),
    )


def render_pm5544(layout):
    """Philips PM5544: white 17x13 grid over grey, patterns on whole rows."""
    surf = pygame.Surface((layout.w, layout.h))
    surf.fill(GREY)
    _draw_grid(surf, layout)
    _draw_castellations(surf, layout)
    _draw_steps(surf, layout, 2, STAIRCASE)
    _draw_steps(surf, layout, 4, BARS)
    _draw_gratings(surf, layout, 8)
    _draw_ring(surf, layout)
    return surf


# --- BBC Test Card F style -------------------------------------------------
#
# Layout follows the documented elements of Test Card F: no grid over the
# picture, 95 % colour bars in descending luminance along the top, the grey
# scale down the left of the central circle, the frequency-response gratings
# (1.5 .. 5.25 MHz) down the right, castellations round the perimeter with an
# overscan triangle at the middle of each edge, and a black-bar-on-white
# ringing patch either side of the ident box.  The photograph inside the circle
# is replaced by the clock dial, which covers that area anyway.

# 95 % saturation, descending luminance: white, yellow, cyan, green, magenta,
# red, blue, black.
_HI, _LO = 242, 12
BBC_BARS = (
    (_HI, _HI, _HI),
    (_HI, _HI, _LO),
    (_LO, _HI, _HI),
    (_LO, _HI, _LO),
    (_HI, _LO, _HI),
    (_HI, _LO, _LO),
    (_LO, _LO, _HI),
    (0, 0, 0),
)

# Stand-ins for the 1.5/2.5/3.5/4/4.5/5.25 MHz gratings, top to bottom.
BBC_GRATING_F = (3, 5, 8, 10, 13, 18)


def _fill_span(surf, span, y, h, colours):
    """Split a horizontal span into equal blocks of ``colours``."""
    x0, x1 = span
    n = len(colours)
    for i, colour in enumerate(colours):
        sx0 = x0 + int(round(i * (x1 - x0) / n))
        sx1 = x0 + int(round((i + 1) * (x1 - x0) / n))
        surf.fill(colour, pygame.Rect(sx0, y, sx1 - sx0, h))


def _margins(layout):
    """Picture area inside the castellations, and the free columns beside the circle."""
    x_left = int(round(layout.cw))
    x_right = int(round(16.0 * layout.cw))
    gap = layout.ch * 0.12
    return (
        x_left,
        int(round(layout.cx - layout.card_radius - gap)),
        int(round(layout.cx + layout.card_radius + gap)),
        x_right,
    )


def _stack_steps(surf, rect, levels):
    n = len(levels)
    for i, level in enumerate(levels):
        y0 = rect.y + int(round(i * rect.h / n))
        y1 = rect.y + int(round((i + 1) * rect.h / n))
        surf.fill((level, level, level), pygame.Rect(rect.x, y0, rect.w, y1 - y0))


def _stack_gratings(surf, layout, rect, freqs):
    n = len(freqs)
    for i, f in enumerate(freqs):
        y0 = rect.y + int(round(i * rect.h / n))
        y1 = rect.y + int(round((i + 1) * rect.h / n))
        surf.fill(BLACK, pygame.Rect(rect.x, y0, rect.w, y1 - y0))
        period = max(2, int(round(layout.cw / f)))
        half = max(1, period // 2)
        x = rect.x
        while x < rect.right:
            surf.fill(WHITE, pygame.Rect(x, y0, min(half, rect.right - x), y1 - y0))
            x += period


def _draw_overscan_triangles(surf, layout):
    """Black arrow in the middle castellation of each edge; all four are white."""
    cw, ch = layout.cw, layout.ch
    mid_col, mid_row = COLS // 2, ROWS // 2
    mx = (mid_col + 0.5) * cw
    my = (mid_row + 0.5) * ch
    tris = (
        ((mx - 0.30 * cw, 0.15 * ch), (mx + 0.30 * cw, 0.15 * ch), (mx, 0.85 * ch)),
        (
            (mx - 0.30 * cw, (ROWS - 0.15) * ch),
            (mx + 0.30 * cw, (ROWS - 0.15) * ch),
            (mx, (ROWS - 0.85) * ch),
        ),
        ((0.15 * cw, my - 0.30 * ch), (0.15 * cw, my + 0.30 * ch), (0.85 * cw, my)),
        (
            ((COLS - 0.15) * cw, my - 0.30 * ch),
            ((COLS - 0.15) * cw, my + 0.30 * ch),
            ((COLS - 0.85) * cw, my),
        ),
    )
    for tri in tris:
        pygame.draw.polygon(surf, BLACK, [(int(round(x)), int(round(y))) for x, y in tri])


def _draw_ringing_patch(surf, rect):
    """Black bar on white: shows ringing and reflections."""
    if rect.w < 8 or rect.h < 6:
        return
    surf.fill(WHITE, rect)
    bar_h = max(2, rect.h // 3)
    surf.fill(BLACK, pygame.Rect(rect.x, rect.centery - bar_h // 2, rect.w, bar_h))


def render_bbc(layout):
    """BBC Test Card F style: plain grey field, circle, bars along the top."""
    surf = pygame.Surface((layout.w, layout.h))
    surf.fill(GREY)
    _draw_castellations(surf, layout)
    _draw_overscan_triangles(surf, layout)

    x_left, x_inner_l, x_inner_r, x_right = _margins(layout)

    bars_y = int(round(layout.ch))
    bars_h = int(round(2.05 * layout.ch)) - bars_y
    _fill_span(surf, (x_left, x_right), bars_y, bars_h, BBC_BARS)

    strip_y0 = int(round(2.35 * layout.ch))
    strip_y1 = int(round(10.65 * layout.ch))
    left = pygame.Rect(x_left, strip_y0, x_inner_l - x_left, strip_y1 - strip_y0)
    right = pygame.Rect(x_inner_r, strip_y0, x_right - x_inner_r, strip_y1 - strip_y0)
    _stack_steps(surf, left, STAIRCASE)
    _stack_gratings(surf, layout, right, BBC_GRATING_F)

    tc = layout.tc_rect
    pad = int(round(0.25 * layout.cw))
    _draw_ringing_patch(surf, pygame.Rect(x_left, tc.y, tc.left - pad - x_left, tc.h))
    _draw_ringing_patch(surf, pygame.Rect(tc.right + pad, tc.y, x_right - tc.right - pad, tc.h))

    # The circle is large enough to reach into the colour bar band; clearing it
    # back to grey makes the bars stop at the circle instead of showing through
    # the translucent dial.
    pygame.draw.circle(
        surf, GREY, (int(round(layout.cx)), int(round(layout.cy))), int(round(layout.card_radius))
    )

    _draw_ring(surf, layout)
    return surf


def load_card_image(path, size):
    """Load a ready-made card and scale it to ``size``."""
    try:
        img = pygame.image.load(path)
    except (pygame.error, OSError) as exc:
        raise ValueError("cannot load card image %r: %s" % (path, exc)) from None
    if img.get_size() != size:
        img = pygame.transform.smoothscale(img, size)
    surf = pygame.Surface(size)
    surf.blit(img, (0, 0))
    return surf


def _field_colour(surf):
    """Median colour on a ring well outside the centre: the card's flat field."""
    w, h = surf.get_size()
    r = 0.42 * h
    samples = []
    for deg in range(0, 360, 5):
        a = math.radians(deg)
        x = int(round(w / 2.0 + r * math.sin(a)))
        y = int(round(h / 2.0 - r * math.cos(a)))
        if 0 <= x < w and 0 <= y < h:
            samples.append(surf.get_at((x, y))[:3])
    if not samples:
        return (128, 128, 128)
    return tuple(sorted(s[i] for s in samples)[len(samples) // 2] for i in range(3))


def _edge_along(surf, field, cx, cy, dx, dy, limit):
    """Distance from (cx, cy) at which the field colour takes over for good."""
    w, h = surf.get_size()
    run = 0
    for step in range(8, int(limit)):
        x = int(round(cx + dx * step))
        y = int(round(cy + dy * step))
        if not (0 <= x < w and 0 <= y < h):
            return float(step - run) if run else None
        if all(abs(a - b) <= FIELD_TOL for a, b in zip(surf.get_at((x, y))[:3], field)):
            run += 1
            if run >= FIELD_RUN:
                return float(step - run + 1)
        else:
            run = 0
    return None


def find_centre_circle(surf):
    """Measure the card's central circle: everything inside it differs from the field.

    Rays are cast every 5 degrees from the image centre.  Rays that never reach
    the field (they run along a white wedge or a bar all the way to the border)
    and rays that stop early inside the logo are discarded, then the centre and
    radius are averaged over the survivors.  Returns ``(cx, cy, r)`` in pixels,
    or ``None`` when no circle stands out.
    """
    w, h = surf.get_size()
    field = _field_colour(surf)
    cx0, cy0 = w / 2.0, h / 2.0
    limit = 0.48 * min(w, h)

    hits = []
    for deg in range(0, 360, 5):
        a = math.radians(deg)
        dx, dy = math.sin(a), -math.cos(a)
        edge = _edge_along(surf, field, cx0, cy0, dx, dy, limit)
        if edge is None or edge < 0.05 * h:
            continue
        hits.append((edge, (cx0 + dx * edge, cy0 + dy * edge)))
    if len(hits) < RAY_MIN:
        return None

    median = sorted(e for e, _ in hits)[len(hits) // 2]
    keep = [p for e, p in hits if abs(e - median) <= 0.1 * median]
    if len(keep) < RAY_MIN:
        return None

    cx = sum(p[0] for p in keep) / len(keep)
    cy = sum(p[1] for p in keep) / len(keep)
    r = sum(math.hypot(p[0] - cx, p[1] - cy) for p in keep) / len(keep)
    return cx, cy, r


def _is_field(colour, field):
    return all(abs(a - b) <= FIELD_TOL for a, b in zip(colour, field))


def find_ident_band(surf, cx, cy, r):
    """Tallest run of empty field rows below the circle: where the bar goes.

    Cards leave a plain strip under the picture for the station ident; finding
    it keeps the timecode off the grid and the patterns.  Returns a
    ``pygame.Rect`` of the empty area, or ``None`` if the card has no such gap.
    """
    w, h = surf.get_size()
    field = _field_colour(surf)
    probe0 = int(max(0, cx - 0.22 * w))
    probe1 = int(min(w, cx + 0.22 * w))

    def empty(y):
        for x in range(probe0, probe1, 8):
            if not _is_field(surf.get_at((x, y))[:3], field):
                return False
        return True

    runs = []
    start = None
    for y in range(int(cy + r) + 2, h):
        if empty(y):
            if start is None:
                start = y
        elif start is not None:
            runs.append((start, y - 1))
            start = None
    if start is not None:
        runs.append((start, h - 1))

    runs = [run for run in runs if run[1] - run[0] >= 0.02 * h]
    if not runs:
        return None
    top, bottom = max(runs, key=lambda run: run[1] - run[0])

    mid = (top + bottom) // 2
    left = int(cx)
    while left > 0 and _is_field(surf.get_at((left - 1, mid))[:3], field):
        left -= 1
    right = int(cx)
    while right < w - 1 and _is_field(surf.get_at((right + 1, mid))[:3], field):
        right += 1
    return pygame.Rect(left, top, right - left, bottom - top)


CARDS = {"pm5544": render_pm5544, "bbc": render_bbc}


def render(layout, card="pm5544", image=None):
    """Return the opaque static background and the layout it was drawn for.

    ``image`` wins over ``card``: a ready-made card file replaces the drawn one,
    and the returned layout is re-centred on that card's own middle circle, with
    the timecode bar dropped into the empty strip below it.  The card itself is
    left untouched: the dial is drawn over it, so a logo in the middle shows
    through the clock.
    """
    if image:
        surf = load_card_image(image, (layout.w, layout.h))
        circle = find_centre_circle(surf)
        if circle is not None:
            layout = layout_mod.with_circle(layout, *circle)
            band = find_ident_band(surf, *circle)
            if band is not None:
                layout = layout_mod.with_ident_band(layout, band)
        return surf, layout
    try:
        return CARDS[card](layout), layout
    except KeyError:
        raise ValueError("unknown card %r, expected one of %s" % (card, sorted(CARDS))) from None
