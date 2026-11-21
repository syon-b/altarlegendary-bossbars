"""AltarLegendaryWH boss-bar pack v2 — original art, 4x detail.

Each boss gets a font glyph that is drawn as the boss bar's title. The glyph is 200 x 32 GUI pixels
(image 800 x 128, i.e. 4 image pixels per GUI pixel) and is positioned (ascent 16) so that a transparent
window lines up exactly over the vanilla 182 x 5 bar. Usage: make_bossbar_pack_v2.py <out.zip> <min_format> <max_format>
"""
import io, json, math, random, sys, zipfile
from PIL import Image, ImageDraw, ImageFilter, ImageChops

S = 4                     # image pixels per GUI pixel
GW, GH = 218, 32          # glyph size in GUI pixels (bar + room for the end-cap emblems)
W, H = GW * S, GH * S
ASCENT = 16               # bar (title row + 9) then sits at GUI rows 18..22 of the glyph
BAR_Y0, BAR_Y1 = 18, 22   # bar rows (GUI) inside the glyph
WIN_X0, WIN_X1 = 18, 200  # transparent window (GUI) - bar is 182 wide, starting at GUI x 18.5

FONT = {
 'A': ["01110","10001","10001","11111","10001","10001","10001"], 'B': ["11110","10001","10001","11110","10001","10001","11110"],
 'C': ["01111","10000","10000","10000","10000","10000","01111"], 'E': ["11111","10000","10000","11110","10000","10000","11111"],
 'F': ["11111","10000","10000","11110","10000","10000","10000"], 'G': ["01111","10000","10000","10011","10001","10001","01111"],
 'H': ["10001","10001","10001","11111","10001","10001","10001"], 'I': ["111","010","010","010","010","010","111"],
 'K': ["10001","10010","10100","11000","10100","10010","10001"], 'L': ["10000","10000","10000","10000","10000","10000","11111"],
 'M': ["10001","11011","10101","10101","10001","10001","10001"], 'N': ["10001","11001","10101","10011","10001","10001","10001"],
 'O': ["01110","10001","10001","10001","10001","10001","01110"], 'P': ["11110","10001","10001","11110","10000","10000","10000"],
 'Q': ["01110","10001","10001","10001","10101","10010","01101"], 'R': ["11110","10001","10001","11110","10100","10010","10001"],
 'S': ["01111","10000","10000","01110","00001","00001","11110"], 'T': ["11111","00100","00100","00100","00100","00100","00100"],
 'U': ["10001","10001","10001","10001","10001","10001","01110"], 'W': ["10001","10001","10001","10101","10101","11011","10001"],
 'Y': ["10001","10001","01010","00100","00100","00100","00100"], ' ': ["00","00","00","00","00","00","00"],
}

def hx(h, a=255):
    h = h.lstrip('#'); return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)

def lerp(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(4))

def g(v):  # GUI -> image coordinate
    return int(round(v * S))

# ----------------------------------------------------------------------------------------- material fills
def fill_material(img, box, kind, pal, rng):
    """box in GUI coords (x0, y0, x1, y1) inclusive."""
    x0, y0, x1, y1 = g(box[0]), g(box[1]), g(box[2] + 1) - 1, g(box[3] + 1) - 1
    px = img.load()
    hgt = max(1, y1 - y0)
    for y in range(y0, y1 + 1):
        t = (y - y0) / hgt
        base = lerp(pal[0], pal[1], t)
        for x in range(x0, x1 + 1):
            if not (0 <= x < W and 0 <= y < H):
                continue
            c = base
            if kind == "stone":
                n = rng.random()
                c = lerp(c, pal[2], 0.35) if n < 0.12 else (lerp(c, pal[1], 0.4) if n > 0.9 else c)
            elif kind == "metal":
                spec = math.exp(-((t - 0.28) ** 2) / 0.006)
                c = lerp(c, pal[2], spec * 0.8)
                if (x + y * 3) % 23 == 0: c = lerp(c, pal[2], 0.25)
            elif kind == "wood":
                grain = 0.5 + 0.5 * math.sin(y * 0.9 + math.sin(x * 0.045) * 3 + (x // 64) * 1.7)
                c = lerp(c, pal[2], grain * 0.35)
                if (x % 64) < 2: c = lerp(c, (0, 0, 0, 255), 0.55)  # plank seams
            elif kind == "marble":
                vein = abs(math.sin(x * 0.03 + math.sin(y * 0.15) * 2.0 + math.sin(x * 0.011) * 4))
                c = lerp(c, pal[2], max(0, 0.9 - vein * 6) * 0.7)
            elif kind == "bark":
                stripe = 0.5 + 0.5 * math.sin(x * 0.35 + math.sin(y * 0.4) * 1.2)
                c = lerp(c, pal[2], stripe * 0.3 * (0.6 + rng.random() * 0.4))
            elif kind == "velvet":
                c = lerp(c, pal[2], 0.15 * rng.random())
            px[x, y] = c

def bevel(d, box, light, dark, width=1):
    x0, y0, x1, y1 = g(box[0]), g(box[1]), g(box[2] + 1) - 1, g(box[3] + 1) - 1
    for i in range(width * 2):
        d.line((x0 + i, y0 + i, x1 - i, y0 + i), fill=light)
        d.line((x0 + i, y0 + i, x0 + i, y1 - i), fill=light)
        d.line((x0 + i, y1 - i, x1 - i, y1 - i), fill=dark)
        d.line((x1 - i, y0 + i, x1 - i, y1 - i), fill=dark)

def outline_rect(d, box, color, width=1):
    x0, y0, x1, y1 = g(box[0]), g(box[1]), g(box[2] + 1) - 1, g(box[3] + 1) - 1
    for i in range(width * S):
        d.rectangle((x0 + i, y0 + i, x1 - i, y1 - i), outline=color)

def glow(img, shape_fn, color, radius):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    shape_fn(ImageDraw.Draw(layer), color)
    blurred = layer.filter(ImageFilter.GaussianBlur(radius))
    img.alpha_composite(blurred)

def drop_shadow(img, mask_img, offset=(0, 6), radius=6, alpha=150):
    a = mask_img.split()[3].point(lambda v: alpha if v > 0 else 0)
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sh.putalpha(a.filter(ImageFilter.GaussianBlur(radius)))
    shifted = Image.new("RGBA", img.size, (0, 0, 0, 0))
    shifted.paste(sh, offset)
    return Image.alpha_composite(shifted, img)

# ----------------------------------------------------------------------------------------- lettering
def text_width(s):
    return sum(len(FONT[c][0]) + 1 for c in s) - 1

def draw_text(img, s, cx, y, top, bottom, outline):
    """Pixel lettering at GUI size 7 (4x4 image pixels per font pixel), gradient fill, outline, highlight."""
    w = text_width(s)
    x = cx - w / 2
    mask = Image.new("L", img.size, 0)
    md = ImageDraw.Draw(mask)
    pos = x
    for ch in s:
        for r, row in enumerate(FONT[ch]):
            for k, bit in enumerate(row):
                if bit == '1':
                    md.rectangle((g(pos + k), g(y + r), g(pos + k + 1) - 1, g(y + r + 1) - 1), fill=255)
        pos += len(FONT[ch][0]) + 1
    # outline: dilate the mask by 1 GUI pixel
    ol = mask.filter(ImageFilter.MaxFilter(2 * S + 1))
    olimg = Image.new("RGBA", img.size, outline)
    img.paste(olimg, (0, 0), ol)
    grad = Image.new("RGBA", img.size)
    gd = ImageDraw.Draw(grad)
    for yy in range(g(y), g(y + 7)):
        t = (yy - g(y)) / max(1, g(7))
        gd.line((0, yy, W, yy), fill=lerp(top, bottom, t))
    img.paste(grad, (0, 0), mask)
    # 1-image-px highlight on the top edge of every letter stroke
    hl = ImageChops.subtract(mask, ImageChops.offset(mask, 0, 2))
    img.paste(Image.new("RGBA", img.size, (255, 255, 255, 110)), (0, 0), hl)

# ----------------------------------------------------------------------------------------- emblems
def emblem(d, kind, cx, cy, pal):
    X = lambda v: g(cx + v)
    Y = lambda v: g(cy + v)
    if kind == "knight":   # kite shield with a crescent moon
        d.polygon([(X(-6), Y(-7)), (X(6), Y(-7)), (X(6), Y(1)), (X(0), Y(8)), (X(-6), Y(1))], fill=pal["dark"], outline=pal["edge"])
        d.polygon([(X(-5), Y(-6)), (X(5), Y(-6)), (X(5), Y(1)), (X(0), Y(7)), (X(-5), Y(1))], fill=pal["mid"])
        d.ellipse((X(-3), Y(-4), X(3), Y(2)), fill=pal["accent"])
        d.ellipse((X(-1.5), Y(-4.5), X(4), Y(1.5)), fill=pal["mid"])
        d.line((X(-5), Y(-6), X(5), Y(-6)), fill=pal["light"], width=S)
    elif kind == "quarry":  # pickaxe over a lava-veined boulder
        d.ellipse((X(-7), Y(-1), X(7), Y(9)), fill=pal["dark"], outline=pal["edge"], width=S)
        d.ellipse((X(-5), Y(0), X(4), Y(5)), fill=pal["mid"])
        d.line((X(-4), Y(6), X(-1), Y(3), X(2), Y(6), X(4), Y(4)), fill=pal["accent"], width=S)
        d.line((X(-3), Y(7), X(5), Y(-7)), fill=pal["wood"], width=2 * S)
        d.polygon([(X(-1), Y(-9)), (X(4), Y(-6)), (X(9), Y(-5)), (X(9), Y(-4)), (X(4), Y(-4)), (X(2), Y(-3)), (X(-2), Y(-8))], fill=pal["light"], outline=pal["edge"])
    elif kind == "pirate":  # skull and crossbones on a red medallion
        d.ellipse((X(-8), Y(-8), X(8), Y(8)), fill=pal["accent"], outline=pal["edge"], width=S)
        d.ellipse((X(-7), Y(-7), X(7), Y(7)), outline=pal["gold"], width=S)
        d.line((X(-5), Y(5), X(5), Y(-5)), fill=pal["bone"], width=2 * S)
        d.line((X(-5), Y(-5), X(5), Y(5)), fill=pal["bone"], width=2 * S)
        d.ellipse((X(-4), Y(-5), X(4), Y(2)), fill=pal["bone"])
        d.rectangle((X(-2.5), Y(1), X(2.5), Y(4)), fill=pal["bone"])
        d.ellipse((X(-3), Y(-3), X(-0.5), Y(-0.5)), fill=pal["edge"])
        d.ellipse((X(0.5), Y(-3), X(3), Y(-0.5)), fill=pal["edge"])
    elif kind == "holy":   # radiant cross with halo
        for i in range(16):
            a = i * math.pi / 8
            d.line((X(math.cos(a) * 4), Y(math.sin(a) * 4), X(math.cos(a) * 9), Y(math.sin(a) * 9)), fill=pal["glowc"], width=S)
        d.ellipse((X(-6), Y(-6), X(6), Y(6)), outline=pal["gold"], width=S)
        d.rectangle((X(-1.5), Y(-8), X(1.5), Y(8)), fill=pal["gold"], outline=pal["edge"])
        d.rectangle((X(-5.5), Y(-4), X(5.5), Y(-1)), fill=pal["gold"], outline=pal["edge"])
        d.rectangle((X(-0.5), Y(-7), X(0.5), Y(7)), fill=pal["light"])
    elif kind == "spider":  # pale spider with glowing eyes
        for side in (-1, 1):
            for j, (ax, ay) in enumerate(((7, -6), (8, -2), (8, 3), (6, 7))):
                d.line((X(side * 1.5), Y(-1 + j), X(side * ax * 0.6), Y(ay * 0.5 - 2)), fill=pal["dark"], width=S)
                d.line((X(side * ax * 0.6), Y(ay * 0.5 - 2), X(side * ax), Y(ay)), fill=pal["dark"], width=S)
        d.ellipse((X(-4), Y(-1), X(4), Y(8)), fill=pal["mid"], outline=pal["dark"], width=S)
        d.ellipse((X(-3), Y(-6), X(3), Y(0)), fill=pal["mid"], outline=pal["dark"], width=S)
        for (ex, ey) in ((-1.6, -4), (1.6, -4), (-0.7, -2.8), (0.7, -2.8)):
            d.ellipse((X(ex - 0.6), Y(ey - 0.6), X(ex + 0.6), Y(ey + 0.6)), fill=pal["accent"])
        d.line((X(0), Y(1), X(0), Y(7)), fill=pal["accent"], width=S)

# ----------------------------------------------------------------------------------------- one boss
def build(boss, rng):
    pal = {k: (hx(v) if isinstance(v, str) else v) for k, v in boss["pal"].items()}
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    name = boss["name"]
    tw = text_width(name)
    px0, px1 = int(GW / 2 - tw / 2 - 11), int(GW / 2 + tw / 2 + 11)

    # --- bar band
    band = (12, 15, GW - 13, 27)
    fill_material(img, band, boss["band"], (pal["bandA"], pal["bandB"], pal["bandC"]), rng)
    bevel(d, band, pal["light"], pal["dark"])
    outline_rect(d, band, pal["edge"])
    # recessed slot around the bar
    slot = (WIN_X0 - 2, BAR_Y0 - 2, WIN_X1 + 2, BAR_Y1 + 2)
    d.rectangle((g(slot[0]), g(slot[1]), g(slot[2] + 1) - 1, g(slot[3] + 1) - 1), fill=pal["edge"])
    d.rectangle((g(slot[0] + 1), g(slot[1] + 1), g(slot[2]) - 1, g(slot[3]) - 1), fill=lerp(pal["edge"], pal["dark"], 0.5))
    # band trim per theme
    if boss["style"] == "knight":
        for x in range(20, GW - 20, 16):
            for yy in (16.5, 25.5):
                d.ellipse((g(x) - 5, g(yy) - 5, g(x) + 5, g(yy) + 5), fill=pal["light"], outline=pal["edge"])
    elif boss["style"] == "quarry":
        for x0 in range(22, GW - 28, 23):
            pts = [(g(x0), g(16)), (g(x0 + 3), g(16.8)), (g(x0 + 5), g(16.2)), (g(x0 + 9), g(16.9))]
            d.line(pts, fill=pal["accent"], width=S)
            glow(img, lambda dd, c, p=pts: dd.line(p, fill=c, width=2 * S), hx("#ff7a18", 200), 6)
            pts = [(g(x0 + 6), g(26)), (g(x0 + 10), g(25.2)), (g(x0 + 13), g(26))]
            d.line(pts, fill=pal["accent"], width=S)
    elif boss["style"] == "pirate":
        for x in range(12, GW - 12):     # rope twist top + bottom
            for yy in (15, 27):
                c = pal["rope1"] if ((x + (yy // 2)) % 3) else pal["rope2"]
                d.rectangle((g(x), g(yy), g(x + 1) - 1, g(yy + 1) - 1), fill=c)
        for x in range(34, GW - 34, 37):   # brass bands
            d.rectangle((g(x), g(16), g(x + 2) - 1, g(27) - 1), fill=pal["gold"], outline=pal["edge"])
    elif boss["style"] == "holy":
        d.line((g(13), g(16.2), g(GW - 13), g(16.2)), fill=pal["gold"], width=S)
        d.line((g(13), g(25.8), g(GW - 13), g(25.8)), fill=pal["gold"], width=S)
        for x in range(18, GW - 18, 12):
            d.polygon([(g(x), g(15)), (g(x + 2), g(13.5)), (g(x + 4), g(15))], fill=pal["gold"])
    elif boss["style"] == "spider":
        for x in range(18, GW - 18, 13):  # resin drips under the band
            ln = 2 + (x * 7) % 4
            d.rounded_rectangle((g(x), g(27), g(x + 1.6), g(27 + ln)), radius=S, fill=pal["accent"])
            d.ellipse((g(x) - 1, g(27 + ln) - 2, g(x + 1.6) + 1, g(27 + ln + 1.5)), fill=pal["accent"])
            d.point((g(x) + 1, g(27.5)), fill=(255, 255, 255, 200))
        for x in range(14, GW - 14, 21):   # moss tufts on top
            d.ellipse((g(x), g(14.2), g(x + 6), g(16.4)), fill=pal["moss"])

    # --- name plaque
    plaque = (px0, 1, px1, 15)
    fill_material(img, plaque, boss["plaque"], (pal["plA"], pal["plB"], pal["plC"]), rng)
    inner = (px0 + 2, 3, px1 - 2, 13)
    bevel(d, plaque, pal["light"], pal["dark"])
    outline_rect(d, plaque, pal["edge"])
    d.rectangle((g(inner[0]), g(inner[1]), g(inner[2] + 1) - 1, g(inner[3] + 1) - 1), outline=lerp(pal["gold"] if "gold" in pal else pal["light"], pal["edge"], 0.3), width=2)
    if boss["style"] == "knight":   # battlements on the plaque
        for x in range(px0, px1 - 2, 6):
            d.rectangle((g(x), g(-0.01), g(x + 3) - 1, g(1.5)), fill=pal["bandB"], outline=pal["edge"])
    elif boss["style"] == "holy":   # gothic pointed arch top
        mid = (px0 + px1) / 2
        d.polygon([(g(px0 + 6), g(1)), (g(mid), g(-0.01)), (g(px1 - 6), g(1))], fill=pal["gold"])
    elif boss["style"] == "quarry":  # chipped corners
        for (cx, cy) in ((px0, 1), (px1, 1)):
            d.polygon([(g(cx) - 4, g(cy) - 4), (g(cx) + 10, g(cy) - 4), (g(cx) - 4, g(cy) + 10)], fill=(0, 0, 0, 0))
    draw_text(img, name, GW / 2, 4.5, pal["textTop"], pal["textBot"], pal["edge"])

    # --- end caps with emblems (glow behind)
    for cx in (8, GW - 9):
        glow(img, lambda dd, c, cx=cx: dd.ellipse((g(cx - 9), g(12), g(cx + 9), g(30)), fill=c), pal["glow"], 10)
        emblem(ImageDraw.Draw(img), boss["emblem"], cx, 21, pal)

    # --- soft drop shadow under everything, then punch the bar window
    img = drop_shadow(img, img.copy(), offset=(0, 5), radius=5, alpha=120)
    d = ImageDraw.Draw(img)
    d.rectangle((g(WIN_X0), g(BAR_Y0), g(WIN_X1 + 1) - 1, g(BAR_Y1 + 1) - 1), fill=(0, 0, 0, 0))
    return img

BOSSES = [
 dict(key="fallen_knight", ch="", name="THE FALLEN KNIGHT", style="knight", emblem="knight", band="metal", plaque="velvet",
      pal=dict(bandA="#3b3846", bandB="#1d1b24", bandC="#c9c3e0", plA="#3b1f5c", plB="#1f1033", plC="#5d3a8c", light="#8f88a8", dark="#0e0c14",
               edge="#07060b", accent="#b07cff", mid="#4a4658", gold="#c0b8de", glow=(150, 90, 255, 150), textTop="#f4efff", textBot="#b89cff")),
 dict(key="quarry_breaker", ch="", name="THE QUARRY BREAKER", style="quarry", emblem="quarry", band="stone", plaque="stone",
      pal=dict(bandA="#6b4a2f", bandB="#3a2617", bandC="#8f6a46", plA="#7a5a3a", plB="#4a321e", plC="#a07a52", light="#b89366", dark="#22150c",
               edge="#150c06", accent="#ff9a2e", mid="#6b4a2f", wood="#8a5a2b", gold="#e6b25a", glow=(255, 120, 30, 140), textTop="#ffe6b0", textBot="#ff8a2a")),
 dict(key="captain", ch="", name="CAPTAIN BLACKMARROW", style="pirate", emblem="pirate", band="wood", plaque="wood",
      pal=dict(bandA="#6a4325", bandB="#3b2414", bandC="#8f5f35", plA="#5a3820", plB="#2e1b0d", plC="#7d5230", light="#a87a4a", dark="#1a0e06",
               edge="#0f0803", accent="#9c1f1f", gold="#e2b443", bone="#efe6cf", rope1="#c9a46a", rope2="#7a5a2e", glow=(255, 70, 40, 120),
               textTop="#fff1c4", textBot="#e2b443")),
 dict(key="heretic_bishop", ch="", name="THE HERETIC BISHOP", style="holy", emblem="holy", band="marble", plaque="velvet",
      pal=dict(bandA="#f1ede4", bandB="#cfc8b8", bandC="#8a8174", plA="#5c1020", plB="#2c0610", plC="#7a1a30", light="#ffffff", dark="#8a8174",
               edge="#2a2216", accent="#d8b03c", gold="#e7c25a", glowc="#fff1b0", glow=(255, 230, 140, 170), textTop="#fff6d6", textBot="#e7c25a")),
 dict(key="hollow_matriarch", ch="", name="THE HOLLOW MATRIARCH", style="spider", emblem="spider", band="bark", plaque="bark",
      pal=dict(bandA="#b9bab4", bandB="#8a8b85", bandC="#5d5e59", plA="#9fa09a", plB="#6f706b", plC="#4a4b47", light="#e4e5df", dark="#3c3d39",
               edge="#1e1f1c", accent="#f08a2c", mid="#cfd0ca", moss="#a7ad8f", gold="#d9772b", glow=(255, 140, 50, 130),
               textTop="#ffffff", textBot="#f2a25a")),
]

def main(out, min_format, max_format):
    providers = []
    z = zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED)
    previews = []
    for b in BOSSES:
        img = build(b, random.Random(hash(b["key"]) & 0xffff))
        buf = io.BytesIO(); img.save(buf, "PNG", optimize=True)
        z.writestr(zipfile.ZipInfo(f"assets/altarlegendary/textures/font/bossbar_{b['key']}.png", date_time=(2026, 1, 1, 0, 0, 0)), buf.getvalue())
        providers.append({"type": "bitmap", "file": f"altarlegendary:font/bossbar_{b['key']}.png", "ascent": ASCENT, "height": GH, "chars": [b["ch"]]})
        previews.append((b, img))
    meta = {"pack": {"description": "§6§lAltarLegendary §r§7Boss Bars v2", "min_format": min_format, "max_format": max_format}}
    for path, data in (("pack.mcmeta", json.dumps(meta, indent=2, ensure_ascii=False)),
                       ("assets/altarlegendary/font/bossbars.json", json.dumps({"providers": providers}, indent=2))):
        z.writestr(zipfile.ZipInfo(path, date_time=(2026, 1, 1, 0, 0, 0)), data.encode("utf-8"))
    # pack icon
    icon = Image.new("RGBA", (128, 128), hx("#1a1424"))
    icon.alpha_composite(previews[0][1].resize((W // 4, H // 4), Image.LANCZOS).crop((0, 0, 128, 32)).resize((128, 32)), (0, 48))
    ib = io.BytesIO(); icon.save(ib, "PNG")
    z.writestr(zipfile.ZipInfo("pack.png", date_time=(2026, 1, 1, 0, 0, 0)), ib.getvalue())
    z.close()
    return previews

def preview(previews, path):
    colors = {"fallen_knight": (175, 90, 240), "quarry_breaker": (240, 220, 60), "captain": (230, 60, 60), "heretic_bishop": (245, 245, 245), "hollow_matriarch": (90, 220, 90)}
    rowh = 40 * S
    canvas = Image.new("RGBA", ((GW + 20) * S, rowh * len(previews)), (52, 76, 112, 255))
    for i, (b, img) in enumerate(previews):
        layer = Image.new("RGBA", ((GW + 20) * S, rowh), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        bx = g(10 + WIN_X0 + 0.5); by = g(4 + BAR_Y0)
        d.rectangle((bx, by, bx + g(182) - 1, by + g(5) - 1), fill=(30, 30, 30, 255))
        d.rectangle((bx, by, bx + g(120) - 1, by + g(5) - 1), fill=colors[b["key"]] + (255,))
        layer.alpha_composite(img, (g(10), g(4)))
        canvas.alpha_composite(layer, (0, i * rowh))
    canvas.save(path)

if __name__ == "__main__":
    num = lambda v: int(float(v)) if float(v).is_integer() else float(v)
    pv = main(sys.argv[1], num(sys.argv[2]), num(sys.argv[3]))
    if len(sys.argv) > 4:
        preview(pv, sys.argv[4])
