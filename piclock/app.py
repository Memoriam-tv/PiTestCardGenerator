"""Display setup, HDMI rate detection and the dirty-rect render loop."""

from __future__ import annotations

import math
import os
import signal
import statistics
import time
from dataclasses import dataclass

import pygame

from . import dial, layout as layout_mod, testcard, timecode

# Rates an HDMI mode may plausibly report.
KNOWN_RATES = (
    23.976,
    24.0,
    25.0,
    29.97,
    30.0,
    47.952,
    48.0,
    50.0,
    59.94,
    60.0,
    72.0,
    75.0,
    100.0,
    120.0,
)

FALLBACK_FPS = 25
PROBE_FRAMES = 40
PROBE_DISCARD = 10

IDENT_BG = (0, 0, 0)
IDENT_BORDER = (255, 255, 255)


@dataclass
class Config:
    size: tuple[int, int] | None = None
    windowed: bool = False
    fps: int | None = None
    frames: int | None = None
    dump_frames: str | None = None
    log_tc: bool = False
    stats: bool = False


@dataclass
class _Stop:
    flag: bool = False


def setup_display(cfg: Config) -> pygame.Surface:
    pygame.display.init()
    pygame.font.init()

    if cfg.windowed:
        size = cfg.size or (1280, 720)
        flags = 0
    else:
        size = cfg.size or (0, 0)
        flags = pygame.FULLSCREEN

    try:
        screen = pygame.display.set_mode(size, flags, vsync=1)
    except (TypeError, pygame.error):
        screen = pygame.display.set_mode(size, flags)

    pygame.mouse.set_visible(False)
    pygame.display.set_caption("piclock")
    return screen


def _snap(hz: float) -> float | None:
    """Nearest standard rate within 5 %, else None."""
    best = min(KNOWN_RATES, key=lambda rate: abs(hz - rate) / rate)
    return best if abs(hz - best) / best < 0.05 else None


def _measure(screen: pygame.Surface, background: pygame.Surface | None) -> float:
    stamps = []
    for _ in range(PROBE_FRAMES):
        if background is not None:
            screen.blit(background, (0, 0))
        pygame.display.flip()
        stamps.append(time.perf_counter())
    intervals = [b - a for a, b in zip(stamps[PROBE_DISCARD:], stamps[PROBE_DISCARD + 1 :])]
    median = statistics.median(intervals) if intervals else 0.0
    return 1.0 / median if median > 0 else 0.0


def detect_fps(
    screen: pygame.Surface,
    override: int | None = None,
    background: pygame.Surface | None = None,
) -> tuple[int, float]:
    """Return (nominal fps, measured Hz) for the active display mode."""
    measured = _measure(screen, background)

    if override:
        return int(override), measured

    fn = getattr(pygame.display, "get_current_refresh_rate", None)
    if fn is not None:
        try:
            reported = int(fn())
        except (pygame.error, TypeError, ValueError):
            reported = 0
        if reported > 0:
            return reported, measured

    snapped = _snap(measured) if measured > 0 else None
    if snapped is not None:
        return int(round(snapped)), measured

    print("fps: fallback %d" % FALLBACK_FPS, flush=True)
    return FALLBACK_FPS, measured


def build_background(lay: layout_mod.Layout) -> pygame.Surface:
    """Test card + dial face + ident bar chrome: every static pixel, once."""
    background = testcard.render(lay)
    face, topleft = dial.render_face(lay)
    background.blit(face, topleft)
    background.fill(IDENT_BG, lay.tc_rect)
    pygame.draw.rect(background, IDENT_BORDER, lay.tc_rect, 2)
    # Blitting the translucent dial disc leaves zero alpha behind in the
    # 32-bit background.  The scanout ignores alpha, but pygame.image.save and
    # any compositing X server do not, so force the whole surface opaque once.
    background.fill((0, 0, 0, 255), None, pygame.BLEND_RGBA_MAX)
    return background


def _pace_to_next_frame(fps: int) -> None:
    """Sleep until the wall clock crosses into the next 1/fps frame bucket.

    Used only when the flip does not block on vblank.  Pacing against the wall
    clock rather than elapsed frame time keeps exactly one rendered frame per
    timecode bucket, so ``FF`` never repeats and never skips.
    """
    target = (math.floor(time.time() * fps) + 1) / fps
    while True:
        remaining = target - time.time()
        if remaining <= 0:
            return
        time.sleep(min(remaining, 0.002))


def run(cfg: Config) -> int:
    screen = setup_display(cfg)
    lay = layout_mod.compute(screen.get_size())
    background = build_background(lay)

    fps, measured = detect_fps(screen, cfg.fps, background)
    vsync_ok = measured > 0 and abs(measured - fps) / fps < 0.02
    print(
        "piclock: %dx%d fps=%d measured=%.2fHz vsync=%s"
        % (lay.w, lay.h, fps, measured, "yes" if vsync_ok else "no"),
        flush=True,
    )

    font = timecode.fit_font(lay.tc_rect.w - 8, lay.tc_rect.h - 6)
    atlas = timecode.DigitAtlas(font)
    tc_text_rect = atlas.text_rect("00:00:00:00", lay.tc_rect).inflate(8, 8)

    if cfg.dump_frames:
        os.makedirs(cfg.dump_frames, exist_ok=True)

    stop = _Stop()

    def _signal(_sig, _frm):
        stop.flag = True

    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            signal.signal(sig, _signal)
        except ValueError:  # not on the main thread
            pass

    prev_rects: list[pygame.Rect] = []
    full_repaint = True
    frame = 0
    durations: list[float] = []
    dropped = 0
    last_report = time.perf_counter()
    prev_start = None

    while not stop.flag:
        start = time.perf_counter()
        if prev_start is not None and (start - prev_start) > 1.5 / fps:
            dropped += 1
        prev_start = start

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                stop.flag = True
            elif event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_q):
                stop.flag = True
            elif event.type == pygame.VIDEOEXPOSE:
                full_repaint = True

        now = time.time()
        tc = timecode.from_epoch(now, fps)

        if full_repaint:
            screen.blit(background, (0, 0))
        else:
            for r in prev_rects + [tc_text_rect]:
                screen.blit(background, r, r)

        cur_rects = dial.draw_hands(screen, lay, now)
        atlas.blit(screen, tc.text(), lay.tc_rect)

        if full_repaint:
            pygame.display.flip()
            full_repaint = False
        else:
            pygame.display.update(cur_rects + prev_rects + [tc_text_rect])
        prev_rects = cur_rects

        if cfg.log_tc:
            print(tc.text(), flush=True)
        if cfg.dump_frames:
            pygame.image.save(
                screen, os.path.join(cfg.dump_frames, "frame_%04d.png" % frame)
            )

        durations.append((time.perf_counter() - start) * 1000.0)
        frame += 1

        if cfg.stats and (time.perf_counter() - last_report) >= 1.0:
            print(
                "frame ms avg=%.2f max=%.2f | fps nominal=%d measured=%.2f | dropped=%d"
                % (
                    sum(durations) / len(durations),
                    max(durations),
                    fps,
                    measured,
                    dropped,
                ),
                flush=True,
            )
            durations = []
            last_report = time.perf_counter()

        if cfg.frames is not None and frame >= cfg.frames:
            break
        if not vsync_ok:
            _pace_to_next_frame(fps)

    pygame.display.quit()
    pygame.quit()
    return 0
