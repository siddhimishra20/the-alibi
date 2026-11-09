# THE ALIBI character kit

32x32 transparent pixel parts, stacked in this order:
base, outfit, nose, beard, eyes, mouth, accessory, hair, hat
(files: parts/<category>/<category>_<name>.png)

Use it:
    from compose import random_suspect
    img = random_suspect("2026-11-09", scale=8, crt=True)  # same seed = same suspect
    img, traits = random_suspect(seed, with_traits=True)   # traits dict for the LLM prompt

Skin, hair, hat and outfit colours are recoloured from muted palettes in manifest.json.
To add a part: draw a 32x32 PNG, drop it in the right folder, add an entry in manifest.json.
Draw hair, beard and brows with the default colours (90,58,40) and (60,38,26) so they recolour.
