"""Time-of-day timecode: HH:MM:SS:FF derived from the wall clock.

The frame field comes from the fractional second, never from a free-running
counter, so the timecode cannot drift and a non-integer HDMI rate (59.94) just
repeats or skips an ``FF`` value now and then - correct for TOD timecode.
"""

import math
import time

import pygame

DIGITS = "0123456789:"
TC_COLOUR = (235, 235, 235)
FONT_NAMES = "dejavusansmono,menlo,couriernew,monospace"


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


def _load_font(size):
    path = pygame.font.match_font(FONT_NAMES, bold=True)
    if path:
        return pygame.font.Font(path, size)
    return pygame.font.Font(None, size)


def cell_advance(font):
    """Fixed per-glyph advance: widest digit plus a little tracking."""
    widest = max(font.size(d)[0] for d in "0123456789")
    return widest + max(1, int(round(font.get_height() * 0.05)))


def fit_font(max_w, max_h, cells=11):
    """Largest bold font whose ``cells`` fixed advances fit in ``max_w``."""
    best = None
    for size in range(max(8, int(max_h * 1.6)), 5, -1):
        font = _load_font(size)
        if cells * cell_advance(font) <= max_w and font.get_height() <= max_h:
            return font
        best = font
    return best if best is not None else _load_font(6)


class DigitAtlas(object):
    """Pre-rendered glyphs blitted on a fixed advance.

    ``font.render`` never runs in the render loop: the string changes every
    frame and per-frame rasterisation is unaffordable on a Pi.
    """

    def __init__(self, font, colour=TC_COLOUR):
        self.font = font
        self.advance = cell_advance(font)
        self.height = font.get_height()
        self.glyphs = dict((ch, font.render(ch, True, colour)) for ch in DIGITS)

    def text_rect(self, text, rect):
        total_w = self.advance * len(text)
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
                dest.blit(glyph, (x + (self.advance - glyph.get_width()) // 2, out.y))
            x += self.advance
        return out
