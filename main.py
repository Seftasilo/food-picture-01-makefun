#!/usr/bin/env python3
"""Food picture entry (make.fun food-picture-01).

The art is the entry.png bundled beside this file: a wood-fired
margherita pizza, a hand lifting one slice with long strands of
molten mozzarella stretching from the pie, blistered crust, fresh
basil, glossy tomato sauce and a faint wisp of steam against the
warm glow of the oven's embers.

This program copies those exact bytes to /output/entry.png. It uses
only the Python standard library, touches no network, reads no
clock, and writes the same bytes on every run, so two runs are
byte-identical. Before writing it pins the source to its expected
SHA-256 digest, checks the JPEG start/end markers and a minimum
size, and writes atomically so an interrupted run never leaves a
partial file behind.
"""

import hashlib
import os
import sys

# SHA-256 of the bundled entry.png, pinned at authoring time. The copy
# is refused unless the source bytes match this digest exactly, so a
# swapped or truncated bundle can never be submitted silently.
EXPECTED_SHA256 = "e2aea9beed93ab91593eaf5ae1835484cd8af8021e8d671608a7f8c3dd786ef4"


def sha256_of(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    here = os.path.dirname(os.path.abspath(__file__))
    source = os.path.join(here, "entry.png")
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    target = os.path.join(out_dir, "entry.png")

    with open(source, "rb") as f:
        data = f.read()

    # Refuse an empty or implausibly small bundle: a truncated file
    # would still carry valid JPEG magic bytes, so size is checked too.
    if len(data) < 1024:
        print(f"entry.png: implausibly small ({len(data)} bytes)",
              file=sys.stderr)
        return 1

    # Refuse unless the source bytes are exactly the bundled art.
    if hashlib.sha256(data).hexdigest() != EXPECTED_SHA256:
        print("entry.png: source bytes do not match the pinned digest",
              file=sys.stderr)
        return 1

    # The bundled art must be a real JPEG: refuse anything else before
    # writing, so a wrong file can never be submitted silently.
    if data[:3] != b"\xff\xd8\xff" or data[-2:] != b"\xff\xd9":
        print("entry.png: not a complete JPEG file", file=sys.stderr)
        return 1

    os.makedirs(out_dir, exist_ok=True)
    # Write to a temp file in the same directory, then rename atomically:
    # an interrupted run never leaves a partial entry.png behind.
    tmp_target = target + ".tmp"
    with open(tmp_target, "wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp_target, target)

    # Confirm the copy is byte-identical, not just the same length: a
    # same-length but corrupted write must fail loudly, since the gate
    # scores the exact bytes written.
    written = os.path.getsize(target)
    digest = sha256_of(target)
    if written != len(data) or digest != sha256_of(source):
        print(f"entry.png: copy failed integrity check "
              f"(wrote {written} of {len(data)} bytes)",
              file=sys.stderr)
        return 1
    print(f"entry.png: {written} bytes -> {target} (sha256 {digest})",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
