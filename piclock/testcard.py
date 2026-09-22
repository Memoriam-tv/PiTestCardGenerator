"""PM5544-style test card, rendered once into a static background surface."""

from __future__ import annotations

import pygame

from .layout import COLS, ROWS, Layout

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


def _row_span(layout: Layout, row: int) -> tuple[int, int, int, int]:
    """Pixel rect of interior grid row ``row``, spanning cols 1..16."""
    x0 = int(round(1.0 * layout.cw))
    x1 = int(round(16.0 * layout.cw))
    y0 = int(round(row * layout.ch))
    y1 = int(round((row + 1) * layout.ch))
    return x0, y0, x1 - x0, y1 - y0


def _draw_grid(surf: pygame.Surface, layout: Layout) -> None:
    lw = layout.line_w
    for col in range(COLS + 1):
        x = int(round(col * layout.cw)) - lw // 2
        surf.fill(WHITE, pygame.Rect(x, 0, lw, layout.h))
    for row in range(ROWS + 1):
        y = int(round(row * layout.ch)) - lw // 2
        surf.fill(WHITE, pygame.Rect(0, y, layout.w, lw))


def _draw_castellations(surf: pygame.Surface, layout: Layout) -> None:
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


def _draw_steps(surf: pygame.Surface, layout: Layout, row: int, levels) -> None:
    x, y, w, h = _row_span(layout, row)
    n = len(levels)
    for i, level in enumerate(levels):
        sx0 = x + int(round(i * w / n))
        sx1 = x + int(round((i + 1) * w / n))
        colour = level if isinstance(level, tuple) else (level, level, level)
        surf.fill(colour, pygame.Rect(sx0, y, sx1 - sx0, h))


def _draw_gratings(surf: pygame.Surface, layout: Layout, row: int) -> None:
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


def render(layout: Layout) -> pygame.Surface:
    """Return the opaque static background for ``layout``."""
    surf = pygame.Surface((layout.w, layout.h))
    surf.fill(GREY)
    _draw_grid(surf, layout)
    _draw_castellations(surf, layout)
    _draw_steps(surf, layout, 2, STAIRCASE)
    _draw_steps(surf, layout, 4, BARS)
    _draw_gratings(surf, layout, 8)
    pygame.draw.circle(
        surf,
        WHITE,
        (int(round(layout.cx)), int(round(layout.cy))),
        int(round(layout.card_radius)),
        max(2, int(round(layout.ch / 10.0))),
    )
    return surf
