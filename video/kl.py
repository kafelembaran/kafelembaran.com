"""Kafe Lembaran video kit: shared constants, fonts, drawing helpers, opening and closing cards.
Everything is relative to this folder, so the kit works from any checkout."""
import math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, 30
FONT = {"lora": "Lora-Variable.ttf", "poppins": "Poppins-Bold.ttf", "inter": "Inter.ttf", "mono": "ShareTechMono.ttf"}
_cache = {}

def F(name, size, wght=None):
    size = max(4, int(size)); key = (name, size, wght)
    if key in _cache: return _cache[key]
    f = ImageFont.truetype(os.path.join(HERE, "fonts", FONT[name]), size)
    if wght:
        try:
            axes = f.get_variation_axes(); vals = [a.get("default", 400) for a in axes]
            for i, a in enumerate(axes):
                if "eight" in str(a.get("name", "")): vals[i] = max(a["minimum"], min(a["maximum"], wght))
            f.set_variation_by_axes(vals)
        except Exception:
            pass
    _cache[key] = f; return f

hexc = lambda h, a=255: tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) + (a,)
# Theme "Kafe Klasik"
BG = ["#165450", "#123f3c"]; FG = hexc("#f7f1e8"); GOLD = hexc("#f2c14e"); ORANGE = hexc("#e07a3a")
TEAL_D = (12, 44, 41, 255); RED = (226, 80, 62, 255); MUTED = (200, 200, 190, 255); DIM = (40, 90, 85, 255)

ease_out = lambda x: 1 - (1 - max(0, min(1, x))) ** 3
def back_out(x):
    x = max(0, min(1, x)); c = 1.70158
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2
def text_w(f, s): return f.getlength(s)
def draw_center(d, y, s, f, fill, stroke=0, sfill=None):
    d.text(((W - text_w(f, s)) / 2, y), s, font=f, fill=fill, stroke_width=stroke, stroke_fill=sfill)
def fade(c, k): return c[:3] + (int(c[3] * max(0, min(1, k))),)

def asset(name): return Image.open(os.path.join(HERE, "assets", name)).convert("RGBA")
BANNER = asset("banner.png")
def bg(i): return Image.new("RGBA", (W, H), hexc(BG[i % 2]))
def clk_str(sec): return f"{int(sec // 60):02d}:{int(sec % 60):02d}:{int((sec % 1) * 100):02d}"

_cup = asset("sil_cup.png"); _cup = _cup.crop(_cup.getbbox())
def cup_img(width, col=FG):
    c = _cup.resize((width, int(_cup.height * width / _cup.width)), Image.BICUBIC)
    out = Image.new("RGBA", c.size, col); out.putalpha(c.getchannel("A")); return out

# ---------------- opening card ----------------
class Intro:
    """Title card. line_a / line_b: when the narrator says each half of the hook (seconds from card start)."""
    def __init__(self, title1, title2, length, line_a, line_b):
        self.t1, self.t2, self.L, self.a, self.b = title1, title2, length, line_a, line_b
        self.bg = bg(0); self.cup = cup_img(440); self.cx, self.cy = (W - 440) // 2 - 30, 980
    def frame(self, t):
        fr = self.bg.copy(); lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        k0 = ease_out(t / 0.5); kk = ease_out((t - 0.2) / 0.5)
        draw_center(d, 300 + (1 - kk) * 20, "DUA HIRUPAN KOPI", F("poppins", 34), fade(GOLD, kk))
        d.line([(W / 2 - 60, 360), (W / 2 + 60, 360)], fill=fade(GOLD, kk), width=4)
        ft = F("lora", 128 if max(text_w(F("lora", 128, 700), s) for s in (self.t1, self.t2)) < 1000 else 100, 700)
        for i, (s, y) in enumerate(((self.t1, 410), (self.t2, 560))):
            k = ease_out((t - 0.45 - i * 0.2) / 0.6); draw_center(d, y + (1 - k) * 50, s, ft, fade(GOLD if i else FG, k))
        c = self.cup.copy(); c.putalpha(c.getchannel("A").point(lambda v: int(v * 0.9 * k0))); fr.alpha_composite(c, (self.cx, self.cy))
        for j, x0 in enumerate((self.cx + 140, self.cx + 200, self.cx + 260)):
            pts = [(x0 + 14 * math.sin(i * 0.35 + t * 3 + j * 2.1) * (i / 26 + 0.3), self.cy - 20 - i * 9) for i in range(26)]
            for i in range(25): d.line([pts[i], pts[i + 1]], fill=fade(FG, (1 - i / 26) * k0 * 0.6), width=6)
        fq = F("lora", 60, 500); ka = ease_out((t - self.a) / 0.5); kb = ease_out((t - self.b) / 0.5)
        draw_center(d, 1400 + (1 - ka) * 20, "“Biar saya terangkan…", fq, fade(FG, ka))
        draw_center(d, 1480 + (1 - kb) * 20, "di antara dua hirupan kopi.”", fq, fade(GOLD, kb))
        fr.alpha_composite(lay); fr.alpha_composite(BANNER)
        if t > self.L - 0.35: fr.alpha_composite(Image.new("RGBA", (W, H), (10, 30, 28, int(120 * (t - self.L + 0.35) / 0.35))))
        return fr

# ---------------- closing card ----------------
class Outro:
    LAND = 0.55
    def __init__(self, book, author, clock):
        self.book, self.author, self.clock = book, author, clock
        self.bg = bg(1); self.cup = cup_img(300); self.cx, self.cy = (W - 300) // 2, 330
    def frame(self, t):
        fr = self.bg.copy(); lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); L = self.LAND
        draw_center(d, 96, self.clock, F("mono", 64), GOLD); draw_center(d, 185, "Antara dua hirupan kopi", F("inter", 34, 700), fade(FG, 0.82))
        if t < L: y = self.cy - 160 * (1 - ease_out(t / L)); al = ease_out(t / 0.25)
        else: q = min(1, (t - L) / 0.25); y = self.cy - 10 * math.sin(q * math.pi) * (1 - q); al = 1
        c = self.cup.copy(); c.putalpha(c.getchannel("A").point(lambda v: int(v * al))); fr.alpha_composite(c, (self.cx, int(y)))
        if t >= L:
            for r0 in (0, 0.18):
                p = (t - L - r0) / 0.9
                if 0 < p < 1:
                    r = 120 + 360 * ease_out(p); x0, y0 = W / 2, self.cy + self.cup.height - 20
                    d.ellipse([x0 - r, y0 - r * 0.35, x0 + r, y0 + r * 0.35], outline=fade(GOLD, 0.8 * (1 - p)), width=5)
        k = back_out((t - L - 0.05) / 0.4)
        if k > 0.01: draw_center(d, 690, "Kafe Lembaran", F("lora", 96 * max(0.4, k), 700), fade(FG, k))
        k = ease_out((t - L - 0.3) / 0.4)
        if k > 0:
            draw_center(d, 830, "BUKU DALAM VIDEO INI", F("poppins", 34), fade(GOLD, k))
            fb = F("lora", 84 if text_w(F("lora", 84, 700), self.book) < 980 else 60, 700)
            draw_center(d, 880 + (1 - k) * 20, self.book, fb, fade(FG, k))
            draw_center(d, 990 + (1 - k) * 20, self.author, F("inter", 40, 500), fade(FG, 0.8 * k))
        k = back_out((t - L - 0.6) / 0.4)
        if k > 0.01:
            f = F("poppins", 52); s = "LINK BUKU KAT BIO"; pw, ph = (text_w(f, s) + 110) * k, 110 * k
            d.rounded_rectangle([W / 2 - pw / 2, 1185 - ph / 2, W / 2 + pw / 2, 1185 + ph / 2], radius=int(55 * k), fill=GOLD)
            if k > 0.6: draw_center(d, 1152, s, f, (18, 63, 60, int(255 * min(1, (k - 0.6) / 0.4))))
        k = ease_out((t - L - 0.9) / 0.4)
        if k > 0:
            draw_center(d, 1300, "kafelembaran.com", F("inter", 52, 800), fade(GOLD, k))
            draw_center(d, 1380, "@kafe.lembaran", F("inter", 44, 600), fade(FG, 0.9 * k))
            draw_center(d, 1440, "TikTok · YouTube · Instagram", F("inter", 34, 500), fade(FG, 0.67 * k))
        fr.alpha_composite(lay); fr.alpha_composite(BANNER); return fr
