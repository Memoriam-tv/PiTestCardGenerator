"""Command line entrypoint: ``python3 -m piclock``."""

from __future__ import annotations

import argparse
import sys

from .app import DEFAULT_CARD_IMAGE, Config, run
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
        default=None,
        help="draw a card instead of the shipped image: %s" % ", ".join(sorted(CARDS)),
    )
    p.add_argument(
        "--card-image",
        metavar="PATH",
        default=None,
        help="use another card image (default: %s)" % DEFAULT_CARD_IMAGE,
    )
    p.add_argument("--windowed", action="store_true", help="run in a window (dev mode)")
    p.add_argument("--frames", type=int, default=None, help="exit after N frames")
    p.add_argument("--dump-frames", metavar="DIR", default=None, help="save every frame as PNG")
    p.add_argument("--log-tc", action="store_true", help="print the timecode of every frame")
    p.add_argument("--stats", action="store_true", help="print frame-time stats each second")
    a = p.parse_args(argv)
    # Bare invocation gets the shipped card image; naming a drawn card opts out.
    image = a.card_image
    if image is None and a.card is None:
        image = DEFAULT_CARD_IMAGE
    return Config(
        size=a.size,
        card_image=image,
        card=a.card or "pm5544",
        windowed=a.windowed,
        fps=a.fps,
        frames=a.frames,
        dump_frames=a.dump_frames,
        log_tc=a.log_tc,
        stats=a.stats,
    )


def main(argv: list[str] | None = None) -> int:
    try:
        return run(parse_args(argv))
    except ValueError as exc:
        print("piclock: %s" % exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
