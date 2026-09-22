"""Geometry for piclock.

Single source of truth: every ratio used by the test card, the dial and the
timecode bar is derived here from the PM5544 grid of 17 columns x 13 rows.
Other modules MUST take a :class:`Layout` and never recompute ``w / 17``.
"""

from __future__ import annotations

from dataclasses import dataclass

import pygame

COLS = 17
ROWS = 13


@dataclass(frozen=True)
class Layout:
    w: int
    h: int
    cw: float  # cell width  = w / 17
    ch: float  # cell height = h / 13
    cx: float  # circle/dial centre x
    cy: float  # circle/dial centre y (above geometric centre)
    card_radius: float  # white ring of the test card
    dial_radius: float  # clock dial
    tc_rect: pygame.Rect  # ident bar carrying the timecode
    line_w: int  # grid line width

    def cell(self, col: float, row: float) -> tuple[float, float]:
        """Top-left pixel of grid cell (col, row), fractional cells allowed."""
        return col * self.cw, row * self.ch


def compute(size: tuple[int, int]) -> Layout:
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
