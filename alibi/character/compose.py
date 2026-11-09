"""THE ALIBI character kit: build a random suspect portrait from layered pixel parts.

    from compose import random_suspect
    img = random_suspect("2026-11-09", scale=8)   # same seed -> same suspect
    img.save("suspect.png")

CLI: python compose.py --seed 2026-11-09 --scale 8 --crt --out suspect.png
"""
import json, os, random, argparse, io
from functools import lru_cache
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
MAN = json.load(open(os.path.join(HERE, "manifest.json")))

def _load(cat, name, picks):
    info = MAN["parts"][cat][name]
    im = Image.open(os.path.join(HERE, info["file"])).convert("RGBA")
    px = im.load()
    swap = {}
    for r in info["recolor"]:
        new_main, new_shade = picks[r["group"]]
        swap[tuple(r["main"])] = tuple(new_main)
        swap[tuple(r["shade"])] = tuple(new_shade)
    if swap:
        for y in range(im.height):
            for x in range(im.width):
                p = px[x, y]
                if p[3] and p[:3] in swap:
                    px[x, y] = swap[p[:3]] + (255,)
    return im

def pick_traits(seed):
    rng = random.Random(str(seed))
    P, R = MAN["parts"], MAN["rules"]
    chance = R["chance_none"]
    t = {c: None for c in MAN["order"]}
    for c in ("base", "outfit", "nose", "eyes", "mouth"):
        t[c] = rng.choice(list(P[c]))
    if rng.random() > chance["hat"]:
        t["hat"] = rng.choice(list(P["hat"]))
    if rng.random() > chance["hair"]:
        pool = list(P["hair"])
        if t["hat"]:
            pool = [h for h in pool if h in R["hat_compatible_hair"]]
        t["hair"] = rng.choice(pool)
    if rng.random() > chance["beard"]:
        t["beard"] = rng.choice(list(P["beard"]))
    if rng.random() > chance["accessory"]:
        pool = list(P["accessory"])
        if t["eyes"] in R["glasses_conflict_eyes"]:
            pool = [a for a in pool if a != "round_glasses"]
        t["accessory"] = rng.choice(pool)
    colors = {g: rng.choice(MAN["palettes"][g]) for g in MAN["palettes"]}
    return t, colors

def build(traits, colors):
    size = MAN["canvas"]
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    for cat in MAN["order"]:
        name = traits.get(cat)
        if name:
            out.alpha_composite(_load(cat, name, colors))
    return out

def crt_filter(img):
    """Mild scanlines + dim edges so the portrait sits in the terminal look."""
    img = img.convert("RGBA"); px = img.load()
    for y in range(img.height):
        if y % 3 == 2:
            for x in range(img.width):
                r, g, b, a = px[x, y]
                px[x, y] = (int(r * .78), int(g * .82), int(b * .78), a)
    return img

def random_suspect(seed, scale=8, crt=False, background=None, with_traits=False):
    traits, colors = pick_traits(seed)
    img = build(traits, colors)
    if background:
        bg = Image.new("RGBA", img.size, background); bg.alpha_composite(img); img = bg
    img = img.resize((img.width * scale, img.height * scale), Image.NEAREST)
    if crt: img = crt_filter(img)
    return (img, traits) if with_traits else img

@lru_cache(maxsize=128)
def get_suspect_png_bytes(seed: str, scale: int = 6, crt: bool = True) -> bytes:
    """Generate and return in-memory PNG bytes for a suspect portrait."""
    img = random_suspect(seed, scale=scale, crt=crt)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def describe_traits(traits: dict) -> str:
    """Human-readable brief of suspect visual traits for dossiers."""
    items = []
    if traits.get("hat"):
        items.append(f"{traits['hat']} hat")
    if traits.get("hair"):
        items.append(f"{traits['hair']} hair")
    if traits.get("beard"):
        items.append(f"{traits['beard']} beard")
    if traits.get("accessory"):
        items.append(traits['accessory'].replace("_", " "))
    if traits.get("outfit"):
        items.append(f"{traits['outfit']} attire")
    return ", ".join(items) if items else "No distinctive markings"

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", default="2026-11-09"); ap.add_argument("--scale", type=int, default=8)
    ap.add_argument("--crt", action="store_true"); ap.add_argument("--out", default="suspect.png")
    a = ap.parse_args()
    img, t = random_suspect(a.seed, a.scale, a.crt, with_traits=True)
    img.save(a.out); print(a.out, t)
