#!/usr/bin/env python3
"""food-picture-01 entry.

Copies the validated ``entry.png`` (a JPEG image) next to this script to
``/output/entry.png``.

Validation (all stdlib only):
  * file size <= 1 MiB
  * starts with the JPEG magic bytes FF D8 FF and ends with FF D9
  * dimensions <= 1024 x 1024, parsed from the JPEG SOF marker
  * SHA-256 matches the expected digest

The copy is written atomically: data goes to a temporary file in the
destination directory, is fsynced, then moved into place with
``os.replace``.
"""

from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path

EXPECTED_SHA256 = "e2aea9beed93ab91593eaf5ae1835484cd8af8021e8d671608a7f8c3dd786ef4"
MAX_SIZE = 1_048_576  # 1 MiB
MAX_DIMENSION = 1024

SOURCE = Path(__file__).resolve().parent / "entry.png"
DEST = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")) / "entry.png"

# Start-of-frame markers that carry width/height (baseline, extended,
# progressive, lossless and their differential variants; 0xC4 DHT,
# 0xC8 JPG and 0xCC DAC are not SOF markers).
SOF_MARKERS = frozenset(
    {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
     0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}
)
# Markers with no length field after the marker code.
STANDALONE_MARKERS = frozenset({0x01, 0xD0, 0xD1, 0xD2, 0xD3,
                                0xD4, 0xD5, 0xD6, 0xD7, 0xD8, 0xD9})


def parse_dimensions(data: bytes) -> tuple[int, int]:
    """Return (width, height) from the first SOF segment of a JPEG."""
    if len(data) < 4 or data[0:2] != b"\xff\xd8":
        raise ValueError("not a JPEG: missing SOI marker (FFD8)")
    pos = 2
    end = len(data)
    while pos + 1 < end:
        if data[pos] != 0xFF:
            raise ValueError(f"bad JPEG marker at offset {pos}: "
                             f"expected 0xFF, got 0x{data[pos]:02x}")
        # Skip any 0xFF padding bytes; the marker code is the first
        # non-0xFF byte. A 0x00 byte here would be escaped entropy
        # data, which cannot appear outside a scan.
        while pos < end and data[pos] == 0xFF:
            pos += 1
        if pos >= end:
            break
        marker = data[pos]
        pos += 1
        if marker == 0x00:
            raise ValueError("unexpected 0xFF00 escape outside a scan")
        if marker == 0xD9:  # EOI: no SOF found before the end
            break
        if marker in STANDALONE_MARKERS:
            continue
        if marker == 0xDA:  # SOS: scan data follows; SOF must precede it
            raise ValueError("no SOF marker found before SOS")
        if pos + 2 > end:
            raise ValueError("truncated JPEG segment length")
        seg_len = int.from_bytes(data[pos:pos + 2], "big")
        if seg_len < 2 or pos + seg_len > end:
            raise ValueError("truncated JPEG segment")
        if marker in SOF_MARKERS:
            body = data[pos + 2:pos + seg_len]
            if len(body) < 5:
                raise ValueError("truncated SOF segment")
            height = int.from_bytes(body[1:3], "big")
            width = int.from_bytes(body[3:5], "big")
            if width == 0 or height == 0:
                raise ValueError("invalid SOF dimensions 0")
            return width, height
        pos += seg_len
    raise ValueError("no SOF marker found in JPEG")


def main() -> int:
    try:
        data = SOURCE.read_bytes()
    except FileNotFoundError:
        print(f"error: source image not found: {SOURCE}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"error: cannot read {SOURCE}: {exc}", file=sys.stderr)
        return 1

    if len(data) > MAX_SIZE:
        print(f"error: file too large: {len(data)} bytes "
              f"(limit {MAX_SIZE})", file=sys.stderr)
        return 1
    if len(data) < 4 or data[:3] != b"\xff\xd8\xff":
        print("error: not a JPEG: missing magic bytes FFD8FF",
              file=sys.stderr)
        return 1
    if data[-2:] != b"\xff\xd9":
        print("error: not a JPEG: missing end marker FFD9",
              file=sys.stderr)
        return 1

    digest = hashlib.sha256(data).hexdigest()
    if digest != EXPECTED_SHA256:
        print(f"error: SHA-256 mismatch: got {digest}, "
              f"expected {EXPECTED_SHA256}", file=sys.stderr)
        return 1

    try:
        width, height = parse_dimensions(data)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if width > MAX_DIMENSION or height > MAX_DIMENSION:
        print(f"error: dimensions {width}x{height} exceed "
              f"{MAX_DIMENSION}x{MAX_DIMENSION}", file=sys.stderr)
        return 1

    DEST.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = DEST.with_name(f".{DEST.name}.tmp.{os.getpid()}")
    try:
        with open(tmp_path, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_path, DEST)
        # Fsync the destination directory so the rename itself is durable.
        dir_fd = os.open(DEST.parent, os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    except OSError as exc:
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass
        print(f"error: cannot write {DEST}: {exc}", file=sys.stderr)
        return 1

    print(f"wrote {DEST} ({len(data)} bytes, {width}x{height}, "
          f"sha256={digest})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
