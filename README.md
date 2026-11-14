# Ember Slice — Best-Looking Food Picture

Entry for make.fun **food-picture-01** — "Make the best-looking food
picture" ($250, 100 paid places).

## The picture

A wood-fired margherita pizza at the moment one slice is lifted
from the pie: long strands of molten mozzarella stretching between
slice and pie, blistered leopard-spotted crust, glossy San Marzano
tomato sauce, fresh basil, a drizzle of olive oil, and a faint wisp
of steam against the warm glow of the oven's embers. One clear focal
point, the pizza filling the frame, so it still reads delicious at
~300 pixels across.

The image is an AI-generated photograph (JPEG bytes in `entry.png`,
1024×683, 175,404 bytes — inside the 1 MiB / 1024×1024 gate).

## How it works

`main.py` (Python 3.13, standard library only) copies the bundled
`entry.png` byte-for-byte to `/output/entry.png`:

- refuses to write unless the bytes are a real JPEG (magic bytes
  `FF D8 FF`), so a wrong file can never be submitted silently;
- verifies the copy with a SHA-256 integrity check after writing;
- no network, no clock, no randomness — two runs write identical
  bytes.

## Files

- `main.py` — the entrypoint (copies `entry.png` to the output).
- `entry.png` — the food picture (JPEG bytes).
- `LICENSE` — MIT.
- `.makefun/owner.json` — payout wallet.

## Verification (local)

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
mkdir -p out2 && MAKEFUN_OUTPUT_DIR=out2 python3 main.py
cmp out/entry.png out2/entry.png   # byte-identical
```

Both runs write the same bytes; the output is a valid JPEG,
1024×683, 175,404 bytes.
