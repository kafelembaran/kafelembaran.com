"""Style "Meja Kopitiam" (design direction v2, docs section 12).
Kopitiam wall tiles, a marble table that holds the panel, the headline written on an order slip that
slaps down once per scene, a wall clock, left-aligned subtitles. Hard cuts between scenes."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import kl
from kl import W, H, F, text_w, ease_out, back_out, cup_img, asset
import panels

GREEN = (22, 84, 80, 255); TILE = (18, 74, 70, 255); MARBLE = (236, 232, 225, 255); CHIT = (243, 230, 181, 255)
RED = (184, 50, 43, 255); KOPI = (59, 38, 24, 255); CREAM = (247, 241, 232, 255); MUTED = (150, 140, 128, 255); DIM = (205, 199, 188, 255)
# Safe zones: TikTok/Reels/Shorts cover the top ~150 px (search bar), the bottom ~480 px (name, caption)
# and the right ~140 px (like/comment buttons). Everything that must be read stays inside SAFE_*.
SAFE_TOP, SAFE_BOTTOM, SAFE_RIGHT = 150, 1440, 930
SUB_BOTTOM = 1490   # subtitles may sit 50 px lower than SAFE_BOTTOM: TikTok's name starts ~1650, Reels/Shorts ~1540
TABLE_Y = 600; TABLE_H = H - TABLE_Y
PANEL_SCALE, PANEL_Y = 0.88, 640
SLIP_SCALE, SLIP_Y = 0.82, 275
LAND = 0.55
rng = np.random.default_rng(3)

def _marble(w, h):
    y, x = np.mgrid[0:h, 0:w] / 260.0
    n = sum(np.sin(x * f + 1.7 * np.sin(y * f * 0.7 + k) + k * 2) / f for k, f in enumerate([1.0, 2.3, 4.9, 9.7]))
    v = np.abs(np.sin(n * 3.0 + x * 0.9)) ** 0.12; a = (1 - v)[..., None] * 0.38 + rng.normal(0, 0.01, (h, w, 1))
    img = np.array(MARBLE[:3], float) * (1 - a) + np.array([150, 150, 148], float) * a
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert("RGBA")

def _tiles():
    im = Image.new("RGBA", (W, H), GREEN); d = ImageDraw.Draw(im)
    for x in range(0, W, 90): d.line([(x, 0), (x, H)], fill=TILE, width=3)
    for y in range(0, H, 90): d.line([(0, y), (W, y)], fill=TILE, width=3)
    return im

def _banner():
    b = Image.new("RGBA", (W, 256), CREAM); d = ImageDraw.Draw(b)
    b.alpha_composite(asset("logo300.png").resize((150, 150)), (60, 53))
    d.text((240, 70), "Kafe Lembaran", font=F("lora", 64, 700), fill=GREEN)
    d.text((242, 160), "kafelembaran.com     @kafe.lembaran", font=F("inter", 34, 500), fill=(60, 90, 86, 255))
    return b

TILES = _tiles(); MARB = _marble(W, TABLE_H); BANNER = _banner()
SCENE_BG = TILES.copy(); SCENE_BG.alpha_composite(MARB, (0, TABLE_Y))
SHADE_Y = 1210
SHADE = Image.new("RGBA", (W, 360), (0, 0, 0, 0))
_sd = ImageDraw.Draw(SHADE)
for _y in range(360): _sd.line([(0, _y), (W, _y)], fill=(10, 25, 23, int(175 * min(1, _y / 90, (360 - _y) / 60))))

def theme_panels():
    """Panels are drawn straight onto the marble in kopi-brown ink with menu-board red accents."""
    panels.set_theme({"FG": KOPI, "GOLD": RED, "ORANGE": RED, "RED": RED, "MUTED": MUTED, "DIM": DIM, "GRID": DIM,
                      "OFF_TXT": MUTED, "PANEL_BG": (0, 0, 0, 0), "INK_ON": CREAM, "TEAL_D": (0, 0, 0, 0)})

def frame_panel(im, is_clip):
    """No box: footage gets a thin kopi-brown edge and soft shadow; diagrams sit on the marble as they are."""
    if not is_clip: return im
    out = Image.new("RGBA", im.size, (0, 0, 0, 0)); out.paste(im, (0, 0))
    ImageDraw.Draw(out).rectangle([0, 0, im.width - 1, im.height - 1], outline=KOPI, width=3)
    return out

# ---------------- order slip ----------------
def _fnt(font, size):
    return F(font, size, 600 if font == "inter" else None)

def slip(lines, rot=-2.5, maxw=960):
    """lines: [(text, size, font, colour)]. Auto-sized to the text, tilted, torn bottom edge, soft shadow."""
    fixed = []
    for t, sz, fn, c in lines:
        while text_w(_fnt(fn, sz), t) > maxw - 150 and sz > 20: sz -= 4
        fixed.append((t, sz, fn, c))
    def lh(t, sz, fn):
        b = _fnt(fn, sz).getbbox(t or "Ag"); return b[3] - min(b[1], 0) + (18 if fn == "anton" else 14)
    w = int(min(maxw, max(text_w(_fnt(fn, sz), t) for t, sz, fn, c in fixed) + 150)); hgt = 46 + sum(lh(*l[:3]) for l in fixed) + 20
    im = Image.new("RGBA", (w, hgt + 30), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.polygon([(0, 0), (w, 0), (w, hgt)] + [(w - i * 20, hgt + (10 if i % 2 else 0)) for i in range(w // 20 + 1)] + [(0, hgt)], fill=CHIT)
    for y in range(60, hgt - 10, 44): d.line([(24, y), (w - 24, y)], fill=(170, 190, 215, 120), width=2)
    d.line([(70, 0), (70, hgt)], fill=(210, 120, 120, 150), width=2)
    y = 36
    for t, sz, fn, c in fixed:
        f = _fnt(fn, sz); b = f.getbbox(t or "Ag"); d.text((96, y - b[1]), t, font=f, fill=c); y += lh(t, sz, fn)
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); sh.putalpha(im.getchannel("A").point(lambda v: v // 3)); sh = sh.filter(ImageFilter.GaussianBlur(8))
    out = Image.new("RGBA", (im.width + 30, im.height + 30), (0, 0, 0, 0)); out.alpha_composite(sh, (14, 16)); out.alpha_composite(im, (0, 0))
    return out.rotate(rot, resample=Image.BICUBIC, expand=True)

def head_slip(Hd, i):
    k = Hd["kind"]
    if k == "count": big = f"{Hd.get('prefix', '')}{Hd['value']}{Hd.get('suffix', '')}"
    elif k == "stamp": big = None
    else: big = str(Hd["text"])
    lines = ([(big, 190 if len(big) <= 8 else 130, "anton", RED)] if big else [])
    if Hd.get("sub"): lines.append((Hd["sub"], 46, "inter", KOPI))
    if not lines: lines = [(" ", 46, "inter", KOPI)]
    im = slip(lines, rot=(-2.5, 2.0, -1.5, 2.5)[i % 4])
    return im.resize((int(im.width * SLIP_SCALE), int(im.height * SLIP_SCALE)), Image.LANCZOS)

def stamp_img(text):
    f = F("anton", 120); tw = text_w(f, text); st = Image.new("RGBA", (int(tw) + 80, 190), (0, 0, 0, 0)); sd = ImageDraw.Draw(st)
    sd.rounded_rectangle([6, 6, st.width - 6, 184], radius=10, outline=RED, width=10); sd.text((st.width / 2, 98), text, font=f, fill=RED, anchor="mm")
    return st.rotate(8, expand=True, resample=Image.BICUBIC)

def place_slap(fr, img, x, y, age, delay=0.0):
    """The one motion per scene: the slip drops onto the table with a small bounce."""
    a = age - delay
    if a < 0: return
    p = min(1, a / 0.22); sc = 1.18 - 0.18 * ease_out(p); bounce = math.sin(min(1, max(0, (a - 0.22) / 0.18)) * math.pi) * 6
    im = img if sc == 1 else img.resize((int(img.width * sc), int(img.height * sc)), Image.BICUBIC)
    if p < 1: im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * min(1, p * 1.6))))
    fr.alpha_composite(im, (int(x - (im.width - img.width) / 2), int(y - (im.height - img.height) / 2 - bounce)))

# ---------------- clock, subtitles ----------------
def clock(fr, secs, frozen=False):
    d = ImageDraw.Draw(fr); cx, cy, r = 112, 210, 52
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=CREAM, outline=KOPI, width=5)
    for k in range(12):
        a = 2 * math.pi * k / 12; d.line([(cx + 40 * math.cos(a), cy + 40 * math.sin(a)), (cx + 46 * math.cos(a), cy + 46 * math.sin(a))], fill=KOPI, width=3)
    a = -math.pi / 2 + 2 * math.pi * (secs % 60) / 60
    d.line([(cx, cy), (cx + 40 * math.cos(a), cy + 40 * math.sin(a))], fill=RED, width=5); d.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=KOPI)
    d.text((190, 166), f"{int(secs // 60)}:{int(secs % 60):02d}", font=F("anton", 64), fill=(242, 193, 78, 255) if frozen else CREAM)
    d.text((192, 242), "antara dua hirupan kopi", font=F("inter", 30, 500), fill=(220, 230, 225, 255))

def subtitle(fr, txt, age):
    txt = txt.replace("*", ""); f = F("inter", 54, 700); rows, cur = [], ""
    for w in txt.split():
        if cur and text_w(f, cur + " " + w) > SAFE_RIGHT - 110: rows.append(cur); cur = w
        else: cur = (cur + " " + w).strip()
    rows.append(cur); y0 = SUB_BOTTOM - 70 * len(rows); d = ImageDraw.Draw(fr)
    for j, r in enumerate(rows): d.text((70, y0 + j * 70), r, font=f, fill=(255, 255, 255, 255), stroke_width=6, stroke_fill=(20, 30, 28, 255))

# ---------------- opening / closing ----------------
class Intro:
    def __init__(self, t1, t2, length, line_a, line_b):
        self.L, self.a, self.b = length, line_a, line_b
        self.slip = slip([(t1, 150, "anton", RED), (t2, 150, "anton", KOPI), ("Dua hirupan kopi", 40, "inter", KOPI)], rot=-3)
        self.bg = TILES.copy(); self.bg.alpha_composite(_marble(W, 700), (0, 1220)); self.cup = cup_img(400, GREEN)
    def frame(self, t):
        fr = self.bg.copy(); fr.alpha_composite(self.cup, (340, 1300)); d = ImageDraw.Draw(fr)
        for j, x0 in enumerate((480, 540, 600)):
            pts = [(x0 + 12 * math.sin(i * 0.35 + t * 3 + j * 2.1) * (i / 22 + 0.3), 1290 - i * 8) for i in range(14)]
            for i in range(13): d.line([pts[i], pts[i + 1]], fill=(255, 255, 255, int(140 * (1 - i / 14))), width=5)
        place_slap(fr, self.slip, 50, 220, t, 0.4)
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay); fq = F("lora", 58, 500)
        ka, kb = ease_out((t - self.a) / 0.4), ease_out((t - self.b) / 0.4)
        if ka > 0: ld.text((70, 880), "“Biar saya terangkan isu ini…", font=fq, fill=CREAM[:3] + (int(255 * ka),))
        if kb > 0: ld.text((70, 960), "di antara dua hirupan kopi.”", font=fq, fill=CREAM[:3] + (int(255 * kb),))
        fr.alpha_composite(lay); return fr

class Outro:
    LAND = LAND
    def __init__(self, book_lines, author, clock_secs):
        self.secs = clock_secs; self.bg = TILES.copy(); self.bg.alpha_composite(_marble(W, 1100), (0, 560))
        self.cup = cup_img(260, GREEN)
        if book_lines:
            lines = [("Baca buku ini", 46, "inter", KOPI)] + [(b, 120, "anton", RED) for b in book_lines] + [(author, 44, "inter", KOPI), ("Link buku kat bio", 56, "inter", RED)]
        else:      # no-book version (political topics on TikTok: no commercial content)
            lines = [("Isu seterusnya", 46, "inter", KOPI), ("Ikut kami", 120, "anton", RED), ("@kafe.lembaran", 64, "inter", KOPI)]
        self.slip = slip(lines, rot=2)
    def frame(self, t):
        fr = self.bg.copy(); clock(fr, self.secs, frozen=True)
        if t < LAND: y = 1080 - 220 * (1 - ease_out(t / LAND)) ** 1.5
        else: q = min(1, (t - LAND) / 0.25); y = 1080 - 8 * math.sin(q * math.pi) * (1 - q)
        fr.alpha_composite(self.cup, (SAFE_RIGHT - 300, int(y)))
        place_slap(fr, self.slip, 50, 300, t, LAND + 0.1)
        k = ease_out((t - LAND - 0.7) / 0.4)
        if k > 0:
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
            ld.text((70, 1330), "kafelembaran.com", font=F("inter", 50, 800), fill=KOPI[:3] + (int(255 * k),))
            ld.text((70, 1400), "@kafe.lembaran di TikTok, YouTube dan Instagram", font=F("inter", 32, 500), fill=(70, 60, 50, int(255 * k)))
            fr.alpha_composite(lay)
        return fr

# ---------------- whole timeline ----------------
def build(ep, SCN, OUT_T, SUBS, SUB_END, intro_a, intro_b, OFF, panels_list):
    theme_panels()
    slips = [head_slip(sc["head"], i) for i, sc in enumerate(ep["scenes"])]
    stamps = {i: stamp_img(sc["head"]["text"]) for i, sc in enumerate(ep["scenes"]) if sc["head"]["kind"] == "stamp"}
    intro = Intro(ep["title"][0], ep["title"][1], OFF + SCN[0], intro_a, intro_b)
    nobook = ep.get("_nobook")
    outro = Outro(None if nobook else ep["book"].get("slip_lines", [ep["book"]["title"]]), ep["book"]["author"], OUT_T - SCN[0])

    def scene(i, tv):
        sc = ep["scenes"][i]; age = tv - SCN[i]; dur = (SCN[i + 1] if i + 1 < len(SCN) else OUT_T) - SCN[i]
        fr = SCENE_BG.copy()
        pim = panels_list[i].render(age, dur, frame_panel)
        pim = pim.resize((int(pim.width * PANEL_SCALE), int(pim.height * PANEL_SCALE)), Image.BILINEAR)
        fr.alpha_composite(pim, (60, PANEL_Y))
        if sc.get("source"):
            ImageDraw.Draw(fr).text((SAFE_RIGHT, PANEL_Y + pim.height + 8), "Sumber: " + sc["source"], font=F("inter", 28, 600), fill=KOPI, anchor="ra")
        place_slap(fr, slips[i], 30, SLIP_Y, age, 0.0)
        if i in stamps: place_slap(fr, stamps[i], 500, SLIP_Y + 50, age, 0.35)
        fr.alpha_composite(SHADE, (0, SHADE_Y))
        cur = [s for s in SUBS if s[0] <= tv]
        if cur and tv < SUB_END: subtitle(fr, cur[-1][1], tv - cur[-1][0])
        clock(fr, max(0, tv - SCN[0])); return fr

    def frame(t):
        tv = t - OFF
        if tv < SCN[0]: return intro.frame(t)
        if tv >= OUT_T: return outro.frame(tv - OUT_T)
        return scene(max(k for k in range(len(SCN)) if SCN[k] <= tv), tv)        # hard cuts
    return frame, outro
