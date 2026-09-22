"""Command line entrypoint: ``python3 -m piclock``."""

from __future__ import annotations

import argparse
import sys

from .app import Config, run
from .testcard import CARDS


def _size(text: str) -> tuple[int, int]:
    part = text.lower().split("x")
    if len(part) != 2:
        raise argparse.ArgumentTypeError("size must look like 1280x720")
    try:
        w, h = int(part[0]), int(part[1])
    except ValueError:
        raise argparse.ArgumentTypeError("size must look like 1280x720") from None
    if w <= 0 or h <= 0:
        raise argparse.ArgumentTypeError("size must be positive")
    return w, h


def parse_args(argv: list[str] | None = None) -> Config:
    p = argparse.ArgumentParser(prog="piclock", description=__doc__)
    p.add_argument("--fps", type=int, default=None, help="override detected HDMI rate")
    p.add_argument("--size", type=_size, default=None, help="force resolution, e.g. 1280x720")
    p.add_argument(
        "--card",
        choices=sorted(CARDS),
        default="pm5544",
        help="background test card style (default: pm5544)",
    )
    p.add_argument("--windowed", action="store_true", help="run in a window (dev mode)")
    p.add_argument("--frames", type=int, default=None, help="exit after N frames")
    p.add_argument("--dump-frames", metavar="DIR", default=None, help="save every frame as PNG")
    p.add_argument("--log-tc", action="store_true", help="print the timecode of every frame")
    p.add_argument("--stats", action="store_true", help="print frame-time stats each second")
    a = p.parse_args(argv)
    return Config(
        size=a.size,
        card=a.card,
        windowed=a.windowed,
        fps=a.fps,
        frames=a.frames,
        dump_frames=a.dump_frames,
        log_tc=a.log_tc,
        stats=a.stats,
    )


def main(argv: list[str] | None = None) -> int:
    return run(parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())
