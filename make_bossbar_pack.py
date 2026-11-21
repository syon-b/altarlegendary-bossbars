"""Generates the original AltarLegendaryWH boss-bar resource pack (frames drawn around the vanilla bar).
Glyph image 192x24, ascent 13 -> covers the title row and the 182x5 bar (image rows 15..19)."""
import io, json, sys, zipfile
from PIL import Image, ImageDraw

W, H = 192, 24
BAR_Y0, BAR_Y1 = 15, 19          # bar rows inside the image
WIN_X0, WIN_X1 = 4, 187          # transparent window over the bar (bar is 182 wide, +-1px slack)

# 5x7 pixel font (only the letters the names need)
FONT = {
 'A': ["01110","10001","10001","11111","10001","10001","10001"],
 'B': ["11110","10001","10001","11110","10001","10001","11110"],
 'C': ["01111","10000","10000","10000","10000","10000","01111"],
 'E': ["11111","10000","10000","11110","10000","10000","11111"],
 'F': ["11111","10000","10000","11110","10000","10000","10000"],
 'G': ["01111","10000","10000","10011","10001","10001","01111"],
 'H': ["10001","10001","10001","11111","10001","10001","10001"],
 'I': ["11111","00100","00100","00100","00100","00100","11111"],
 'K': ["10001","10010","10100","11000","10100","10010","10001"],
 'L': ["10000","10000","10000","10000","10000","10000","11111"],
 'M': ["10001","11011","10101","10101","10001","10001","10001"],
 'N': ["10001","11001","10101","10011","10001","10001","10001"],
 'O': ["01110","10001","10001","10001","10001","10001","01110"],
 'P': ["11110","10001","10001","11110","10000","10000","10000"],
 'Q': ["01110","10001","10001","10001","10101","10010","01101"],
 'R': ["11110","10001","10001","11110","10100","10010","10001"],
 'S': ["01111","10000","10000","01110","00001","00001","11110"],
 'T': ["11111","00100","00100","00100","00100","00100","00100"],
 'U': ["10001","10001","10001","10001","10001","10001","01110"],
 'W': ["10001","10001","10001","10101","10101","11011","10001"],
 'Y': ["10001","10001","01010","00100","00100","00100","00100"],
 ' ': ["000","000","000","000","000","000","000"],
}

def text(d, s, cx, y, fg, shadow):
    width = sum(len(FONT[c][0]) + 1 for c in s) - 1
    x = cx - width // 2
    for c in s:
        g = FONT[c]
        for r, row in enumerate(g):
            for k, bit in enumerate(row):
                if bit == '1':
                    d.point((x + k + 1, y + r + 1), fill=shadow)
                    d.point((x + k, y + r), fill=fg)
        x += len(g[0]) + 1
    return width

def hexc(h, a=255):
    h = h.lstrip('#'); return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)

def frame(name, outline, dark, mid, light, accent, txt, style):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    O, D, M, L, A, T = map(hexc, (outline, dark, mid, light, accent, txt))
    # bar frame (rows 13..21)
    d.rectangle((1, 13, W - 2, 21), fill=O)
    d.rectangle((2, 14, W - 3, 20), fill=M)
    d.line((2, 14, W - 3, 14), fill=L)
    d.line((2, 20, W - 3, 20), fill=D)
    # name plaque (rows 0..13), centered
    tw = sum(len(FONT[c][0]) + 1 for c in name) - 1
    pw = tw + 18
    px0 = W // 2 - pw // 2
    px1 = px0 + pw
    d.rectangle((px0, 0, px1, 13), fill=O)
    d.rectangle((px0 + 1, 1, px1 - 1, 12), fill=D)
    d.line((px0 + 1, 1, px1 - 1, 1), fill=M)
    d.point((px0 + 1, 1), fill=L); d.point((px1 - 1, 1), fill=L)
    # theme ornaments
    if style == "castle":      # crenellations along the plaque top
        for x in range(px0 - 6, px0, 3):
            d.rectangle((x, 9, x + 1, 13), fill=O)
        for x in range(px1 + 1, px1 + 7, 3):
            d.rectangle((x, 9, x + 1, 13), fill=O)
        for cx in (8, W - 9):  # swords at the ends
            d.line((cx, 8, cx, 13), fill=L); d.line((cx - 2, 11, cx + 2, 11), fill=A)
    elif style == "rock":      # jagged rocks + lava cracks
        for x in range(4, W - 4, 7):
            h = 2 + (x * 7) % 3
            d.polygon([(x, 13), (x + 3, 13 - h), (x + 6, 13)], fill=M if (x // 7) % 2 else D)
        for x in (px0 + 3, px1 - 3):
            d.line((x, 3, x, 10), fill=A)
        d.line((10, 17, 30, 17), fill=A); d.line((W - 31, 17, W - 11, 17), fill=A)
    elif style == "ship":      # gold rope trim + red pennants
        for x in range(2, W - 2, 2):
            d.point((x, 13), fill=A); d.point((x + 1, 21), fill=A)
        for cx in (6, W - 7):
            d.polygon([(cx - 3, 4), (cx + 3, 4), (cx, 10)], fill=hexc("#a82424"))
            d.line((cx, 2, cx, 12), fill=O)
    elif style == "holy":      # gold crosses + gilded corners
        for cx in (px0 - 7, px1 + 7, 9, W - 10):
            d.line((cx, 4, cx, 12), fill=A); d.line((cx - 2, 6, cx + 2, 6), fill=A)
        d.rectangle((1, 13, 4, 21), fill=A); d.rectangle((W - 5, 13, W - 2, 21), fill=A)
    elif style == "web":       # cobweb corners + resin drips
        for (x0, s) in ((1, 1), (W - 2, -1)):
            for i in range(7):
                d.point((x0 + s * i, 13 - i), fill=L)
            d.line((x0, 13, x0 + s * 6, 13), fill=L)
            d.line((x0, 13, x0, 7), fill=L)
        for x in range(12, W - 12, 17):
            d.line((x, 21, x, 22 + (x % 2)), fill=A)
    # plaque accent ticks + name
    d.line((px0 + 3, 12, px1 - 3, 12), fill=A)
    text(d, name, W // 2, 3, T, L if style == "holy" else O)
    # transparent window over the vanilla bar
    d.rectangle((WIN_X0, BAR_Y0, WIN_X1, BAR_Y1), fill=(0, 0, 0, 0))
    d.rectangle((WIN_X0 - 1, BAR_Y0 - 1, WIN_X1 + 1, BAR_Y0 - 1), fill=O)
    d.rectangle((WIN_X0 - 1, BAR_Y1 + 1, WIN_X1 + 1, BAR_Y1 + 1), fill=O)
    return im

BOSSES = [
 ("fallen_knight",    "", "THE FALLEN KNIGHT",   ("#14121a", "#2b2836", "#4a4658", "#8f8aa3", "#7b4cc2", "#e9e3ff"), "castle"),
 ("quarry_breaker",   "", "THE QUARRY BREAKER",  ("#1c120a", "#3d2a1b", "#6b4a2f", "#a6825a", "#ff8a2a", "#ffe2b8"), "rock"),
 ("captain",          "", "CAPTAIN BLACKMARROW", ("#140b05", "#3b2414", "#6a4325", "#9c6b3c", "#d4a63a", "#ffe9b0"), "ship"),
 ("heretic_bishop",   "", "THE HERETIC BISHOP",  ("#2e281c", "#b6af9e", "#d9d3c4", "#f4f1e8", "#d8b03c", "#3a2e12"), "holy"),
 ("hollow_matriarch", "", "THE HOLLOW MATRIARCH",("#1d1d1b", "#5f605b", "#8e8f8a", "#cfd0ca", "#d9772b", "#f6f4ee"), "web"),
]

def main(out):
    providers = []
    z = zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED)
    for key, ch, name, pal, style in BOSSES:
        im = frame(name, *pal, style)
        buf = io.BytesIO(); im.save(buf, "PNG")
        info = zipfile.ZipInfo(f"assets/altarlegendary/textures/font/bossbar_{key}.png", date_time=(2026, 1, 1, 0, 0, 0))
        z.writestr(info, buf.getvalue())
        providers.append({"type": "bitmap", "file": f"altarlegendary:font/bossbar_{key}.png", "ascent": 13, "height": H, "chars": [ch]})
        im.resize((W * 4, H * 4), Image.NEAREST).save(out.replace(".zip", f"_{key}_preview.png"))
    meta = {"pack": {"description": "§6AltarLegendaryWH §7boss bars", "min_format": 84, "max_format": 97.1}}
    for path, data in (("pack.mcmeta", json.dumps(meta, indent=2)),
                       ("assets/altarlegendary/font/bossbars.json", json.dumps({"providers": providers}, indent=2))):
        z.writestr(zipfile.ZipInfo(path, date_time=(2026, 1, 1, 0, 0, 0)), data)
    z.close()

if __name__ == "__main__":
    main(sys.argv[1])
