"""Clock dial: static face rendered once, hands drawn per frame.

No ``pygame.transform.rotate`` anywhere — rotation blits are the Pi 2 budget
killer.  Hands are polygons recomputed from the angle each frame and drawn with
``pygame.gfxdraw``.
"""

from __future__ import annotations

import math
import time

import pygame
import pygame.gfxdraw

from .layout import Layout

DISC = (0, 0, 0, 160)
RING = (255, 255, 255)
MINOR_TICK = (235, 235, 235)
MAJOR_TICK = (255, 255, 255)
HAND_LIGHT = (245, 245, 245)
HAND_SECOND = (220, 40, 40)
OUTLINE = (0, 0, 0)

FACE_PAD = 4

# (length_f, half_w_f, half_w_min_px, tail_f, colour)
HOUR = (0.55, 0.030, 3, 0.10, HAND_LIGHT)
MINUTE = (0.82, 0.020, 2, 0.12, HAND_LIGHT)
SECOND = (0.90, 0.007, 2, 0.20, HAND_SECOND)


def _polar(cx: float, cy: float, r: float, angle_deg: float) -> tuple[float, float]:
    a = math.radians(angle_deg)
    return cx + r * math.sin(a), cy - r * math.cos(a)


def render_face(layout: Layout) -> tuple[pygame.Surface, tuple[int, int]]:
    """Return the static dial face surface and its blit top-left."""
    r = layout.dial_radius
    size = int(round(2 * (r + FACE_PAD)))
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    c = size / 2.0

    pygame.draw.circle(surf, DISC, (int(round(c)), int(round(c))), int(round(r)))
    pygame.draw.circle(
        surf,
        RING,
        (int(round(c)), int(round(c))),
        int(round(r)),
        max(2, int(round(r / 90.0))),
    )

    minor_w = max(2, int(round(r / 120.0)))
    for i in range(60):
        if i % 5 == 0:
            continue
        a = i * 6.0
        pygame.draw.line(
            surf, MINOR_TICK, _polar(c, c, 0.90 * r, a), _polar(c, c, 0.97 * r, a), minor_w
        )

    major_w = max(4, int(round(r / 45.0)))
    for i in range(12):
        a = i * 30.0
        pygame.draw.line(
            surf, MAJOR_TICK, _polar(c, c, 0.82 * r, a), _polar(c, c, 0.97 * r, a), major_w
        )

    topleft = (int(round(layout.cx - c)), int(round(layout.cy - c)))
    return surf, topleft


def hand_points(
    layout: Layout,
    angle_deg: float,
    length_f: float,
    half_w_f: float,
    tail_f: float,
) -> list[tuple[float, float]]:
    """Quad outlining a hand; all factors are multiples of the dial radius."""
    r = layout.dial_radius
    length = length_f * r
    half_w = half_w_f * r
    tail = tail_f * r
    a = math.radians(angle_deg)
    dx, dy = math.sin(a), -math.cos(a)
    px, py = math.cos(a), math.sin(a)
    cx, cy = layout.cx, layout.cy
    tip = (cx + dx * length, cy + dy * length)
    end = (cx - dx * tail, cy - dy * tail)
    return [
        (tip[0] + px * half_w, tip[1] + py * half_w),
        (tip[0] - px * half_w, tip[1] - py * half_w),
        (end[0] - px * half_w, end[1] - py * half_w),
        (end[0] + px * half_w, end[1] + py * half_w),
    ]


def _bounds(points, inflate: int = 6) -> pygame.Rect:
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    rect = pygame.Rect(
        int(math.floor(min(xs))),
        int(math.floor(min(ys))),
        int(math.ceil(max(xs) - min(xs))) + 1,
        int(math.ceil(max(ys) - min(ys))) + 1,
    )
    return rect.inflate(inflate * 2, inflate * 2)


def _draw_hand(dest: pygame.Surface, layout: Layout, angle: float, spec) -> pygame.Rect:
    length_f, half_w_f, half_w_min, tail_f, colour = spec
    r = layout.dial_radius
    length = length_f * r
    half_w = max(float(half_w_min), half_w_f * r)
    tail = tail_f * r

    outline = hand_points(layout, angle, (length + 2) / r, (half_w + 2) / r, (tail + 2) / r)
    body = hand_points(layout, angle, length / r, half_w / r, tail / r)

    for pts, col in ((outline, OUTLINE), (body, colour)):
        ipts = [(int(round(x)), int(round(y))) for x, y in pts]
        pygame.gfxdraw.filled_polygon(dest, ipts, col)
        pygame.gfxdraw.aapolygon(dest, ipts, col)

    return _bounds(outline)


def draw_hands(dest: pygame.Surface, layout: Layout, now: float) -> list[pygame.Rect]:
    """Draw hour/minute/second hands plus hub; return the dirty rects."""
    local = now + time.localtime(now).tm_gmtoff
    hour_a = ((local % 43200.0) / 43200.0) * 360.0
    min_a = ((local % 3600.0) / 3600.0) * 360.0
    sec_a = ((local % 60.0) / 60.0) * 360.0

    rects = [
        _draw_hand(dest, layout, hour_a, HOUR),
        _draw_hand(dest, layout, min_a, MINUTE),
        _draw_hand(dest, layout, sec_a, SECOND),
    ]

    r = layout.dial_radius
    cx, cy = int(round(layout.cx)), int(round(layout.cy))
    hub_r = max(4, int(round(0.035 * r)))
    pin_r = max(2, int(round(0.015 * r)))
    pygame.draw.circle(dest, (255, 255, 255), (cx, cy), hub_r)
    pygame.draw.circle(dest, HAND_SECOND, (cx, cy), pin_r)
    rects.append(pygame.Rect(cx - hub_r, cy - hub_r, 2 * hub_r, 2 * hub_r).inflate(12, 12))

    return rects
