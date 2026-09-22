"""Time-of-day timecode: HH:MM:SS:FF on a drawn seven-segment display.

The frame field comes from the fractional second, never from a free-running
counter, so the timecode cannot drift and a non-integer HDMI rate (59.94) just
repeats or skips an ``FF`` value now and then - correct for TOD timecode.

Glyphs are seven-segment shapes built from polygons once at startup, not text
from a font file: it is the look real timecode displays have, it needs no font
installed, and nothing is rasterised in the render loop.
"""

import math
import time

import pygame

DIGITS = "0123456789:"

LIT = (255, 72, 48)  # lit segment, red LED
DIM = (48, 14, 10)  # unlit segment, just visible against the black bar
BG = (0, 0, 0)  # the ident bar the glyphs are blitted onto

# Which of the seven segments each glyph lights.
#   A top, B upper right, C lower right, D bottom, E lower left, F upper left,
#   G middle.
SEGMENTS = {
    "0": "ABCDEF",
    "1": "BC",
    "2": "ABDEG",
    "3": "ABCDG",
    "4": "BCFG",
    "5": "ACDFG",
    "6": "ACDEFG",
    "7": "ABC",
    "8": "ABCDEFG",
    "9": "ABCDFG",
}

SLANT = 0.09  # shear, as a fraction of glyph height, like a real LED module
GAP = 0.12  # gap between neighbouring segments, as a fraction of thickness


class Timecode(object):
    __slots__ = ("h", "m", "s", "f")

    def __init__(self, h, m, s, f):
        self.h = h
        self.m = m
        self.s = s
        self.f = f

    def text(self):
        return "%02d:%02d:%02d:%02d" % (self.h, self.m, self.s, self.f)

    def __eq__(self, other):
        if not isinstance(other, Timecode):
            return NotImplemented
        return (self.h, self.m, self.s, self.f) == (other.h, other.m, other.s, other.f)

    def __repr__(self):
        return "Timecode(%s)" % self.text()


def from_epoch(now, fps):
    """Time-of-day timecode for epoch second ``now`` at ``fps``."""
    lt = time.localtime(now)
    frac = now - math.floor(now)
    f = min(fps - 1, int(frac * fps))
    return Timecode(lt.tm_hour, lt.tm_min, lt.tm_sec, f)


def _horizontal(x, y, length, t):
    """Mitred horizontal bar: the classic seven-segment hexagon."""
    return [
        (x, y + t / 2.0),
        (x + t / 2.0, y),
        (x + length - t / 2.0, y),
        (x + length, y + t / 2.0),
        (x + length - t / 2.0, y + t),
        (x + t / 2.0, y + t),
    ]


def _vertical(x, y, length, t):
    return [
        (x + t / 2.0, y),
        (x + t, y + t / 2.0),
        (x + t, y + length - t / 2.0),
        (x + t / 2.0, y + length),
        (x, y + length - t / 2.0),
        (x, y + t / 2.0),
    ]


def _segment_shapes(w, h, t):
    """Polygon for each segment of a glyph ``w`` x ``h`` with thickness ``t``."""
    gap = t * GAP
    inner = (h - t) / 2.0  # length of one vertical run, centre bar included
    bar = w - t - 2 * gap  # length of a horizontal run
    v_len = inner - gap
    return {
        "A": _horizontal(t / 2.0 + gap, 0.0, bar, t),
        "G": _horizontal(t / 2.0 + gap, (h - t) / 2.0, bar, t),
        "D": _horizontal(t / 2.0 + gap, h - t, bar, t),
        "F": _vertical(0.0, t / 2.0 + gap, v_len, t),
        "B": _vertical(w - t, t / 2.0 + gap, v_len, t),
        "E": _vertical(0.0, (h + t) / 2.0 + gap - t / 2.0, v_len, t),
        "C": _vertical(w - t, (h + t) / 2.0 + gap - t / 2.0, v_len, t),
    }


class SevenSegAtlas(object):
    """Pre-drawn seven-segment glyphs blitted on a fixed advance.

    Every glyph carries its unlit segments too, so one blit paints a whole
    cell and the dirty rect stays the same every frame.
    """

    def __init__(self, advance, height, lit=LIT, dim=DIM, bg=BG):
        self.advance = int(advance)
        self.height = int(height)
        self.glyphs = {}

        # Digits fill their cell: the bar spans the card's empty strip and the
        # display stretches with it.
        digit_w = self.advance * 0.82
        thickness = max(2.0, self.height / 8.0)
        slant = self.height * SLANT
        self.pad = int(math.ceil(slant)) + 2
        self._xoff = (self.advance - digit_w) / 2.0 + self.pad / 2.0
        self._slant = slant
        shapes = _segment_shapes(digit_w, float(self.height), thickness)

        for ch in DIGITS:
            # Opaque, not SRCALPHA: the glyphs land on the black ident bar, so
            # carrying its colour turns eleven alpha blends per frame into
            # eleven straight copies.
            surf = pygame.Surface((self.advance + self.pad, self.height))
            surf.fill(bg)
            if ch == ":":
                self._draw_colon(surf, digit_w, thickness)
            else:
                on = SEGMENTS[ch]
                for name, points in sorted(shapes.items()):
                    colour = lit if name in on else dim
                    pygame.draw.polygon(surf, colour, self._shear(points))
            self.glyphs[ch] = surf

    def _shear(self, points):
        """Lean the glyph right, like a real LED module."""
        out = []
        for x, y in points:
            lean = self._slant * (1.0 - y / float(self.height))
            out.append((int(round(x + lean + self._xoff)), int(round(y))))
        return out

    def _draw_colon(self, surf, digit_w, thickness):
        size = thickness
        x = digit_w / 2.0 - size / 2.0
        for frac in (0.3, 0.7):
            y = self.height * frac - size / 2.0
            square = [(x, y), (x + size, y), (x + size, y + size), (x, y + size)]
            pygame.draw.polygon(surf, LIT, self._shear(square))

    def text_rect(self, text, rect):
        # The last glyph leans past its advance, so the covered rect is one
        # pad wider than the sum of the advances.
        total_w = self.advance * len(text) + self.pad
        return pygame.Rect(
            rect.x + (rect.w - total_w) // 2,
            rect.centery - self.height // 2,
            total_w,
            self.height,
        )

    def blit(self, dest, text, rect):
        out = self.text_rect(text, rect)
        x = out.x
        for ch in text:
            glyph = self.glyphs.get(ch)
            if glyph is not None:
                dest.blit(glyph, (x, out.y))
            x += self.advance
        return out


def fit_atlas(max_w, max_h, cells=11):
    """Seven-segment display filling the bar: ``cells`` across, as tall as fits."""
    advance = max(6, int(max_w // cells))
    return SevenSegAtlas(advance, max(6, int(max_h)))
