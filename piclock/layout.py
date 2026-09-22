"""Geometry for piclock.

Single source of truth: every ratio used by the test card, the dial and the
timecode bar is derived here from the PM5544 grid of 17 columns x 13 rows.
Other modules MUST take a :class:`Layout` and never recompute ``w / 17``.

The whole package targets Python 3.4 and pygame 1.9 (that is what the Pi 1 it
runs on can install): no dataclasses, no f-strings, no variable annotations.
"""

import pygame

COLS = 17
ROWS = 13

DIAL_FIT = 0.93  # dial radius as a fraction of the circle it sits in


class Layout(object):
    """Fixed geometry for one screen size."""

    __slots__ = (
        "w",
        "h",
        "cw",
        "ch",
        "cx",
        "cy",
        "card_radius",
        "dial_radius",
        "tc_rect",
        "line_w",
    )

    def __init__(self, w, h, cw, ch, cx, cy, card_radius, dial_radius, tc_rect, line_w):
        self.w = w  # screen width
        self.h = h  # screen height
        self.cw = cw  # cell width  = w / 17
        self.ch = ch  # cell height = h / 13
        self.cx = cx  # circle/dial centre x
        self.cy = cy  # circle/dial centre y
        self.card_radius = card_radius  # white circle of the test card
        self.dial_radius = dial_radius  # clock dial
        self.tc_rect = tc_rect  # ident bar carrying the timecode
        self.line_w = line_w  # grid line width

    def cell(self, col, row):
        """Top-left pixel of grid cell (col, row), fractional cells allowed."""
        return col * self.cw, row * self.ch


def compute(size):
    """Layout for a screen of ``size``, straight off the 17 x 13 grid."""
    w, h = int(size[0]), int(size[1])
    cw = w / COLS
    ch = h / ROWS
    cx = w / 2.0
    cy = 6.0 * ch

    tc_w = 9.0 * cw
    tc_top = 11.05 * ch
    tc_bottom = 11.95 * ch
    tc_rect = pygame.Rect(
        int(round(cx - tc_w / 2.0)),
        int(round(tc_top)),
        int(round(tc_w)),
        max(1, int(round(tc_bottom - tc_top))),
    )

    return Layout(
        w=w,
        h=h,
        cw=cw,
        ch=ch,
        cx=cx,
        cy=cy,
        card_radius=5.0 * ch,
        dial_radius=4.55 * ch,
        tc_rect=tc_rect,
        line_w=max(1, int(round(h / 540.0))),
    )


def with_circle(layout, cx, cy, r):
    """Re-centre the dial on a circle measured somewhere else (a card image).

    The dial fills that circle and the ident bar moves to just below it, so a
    ready-made card keeps its own geometry instead of the 17 x 13 grid's.
    """
    tc_w = 9.0 * layout.cw
    tc_h = 0.9 * layout.ch
    tc_top = min(cy + r + 0.15 * layout.ch, layout.h - 1.1 * layout.ch - tc_h)
    tc_rect = pygame.Rect(
        int(round(cx - tc_w / 2.0)),
        int(round(tc_top)),
        int(round(tc_w)),
        max(1, int(round(tc_h))),
    )
    return Layout(
        w=layout.w,
        h=layout.h,
        cw=layout.cw,
        ch=layout.ch,
        cx=cx,
        cy=cy,
        card_radius=r,
        dial_radius=r * DIAL_FIT,
        tc_rect=tc_rect,
        line_w=layout.line_w,
    )
