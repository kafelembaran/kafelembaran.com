"""Middle-section visual cards (960x540 window under the headline): Gemini footage or animated infographics.
Exec'd inside render_vo3.py, which supplies W, H, F, FG, GOLD, ORANGE, ease_out, back_out, text_w, Image, ImageDraw, np, subprocess."""
import math
CX0, CY0, CW, CH = 60, 790, 960, 540
TEAL_D = (12, 44, 41, 255); LINE = (247, 241, 232, 255); RED = (226, 80, 62, 255)
GEM = "/home/claude/gem"

class Clip:
    """Sequential frame reader for a footage segment (scaled a little larger than the card for a slow push-in)."""
    def __init__(self, path, start):
        self.path, self.start = path, start; self.p = None; self.last = None; self.n = 0
        self.sw, self.sh = int(CW * 1.12) // 2 * 2, int(CH * 1.12) // 2 * 2
    def open(self):
        self.p = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-ss", str(self.start), "-stream_loop", "-1", "-i", self.path,
                                   "-vf", f"fps=30,scale={self.sw}:{self.sh}:force_original_aspect_ratio=increase,crop={self.sw}:{self.sh},eq=saturation=0.85",
                                   "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    def frame(self, age, dur):
        want = int(age * 30)
        if self.p is None: self.open()
        while self.n <= want:
            buf = self.p.stdout.read(self.sw * self.sh * 3)
            if len(buf) < self.sw * self.sh * 3: break
            self.last = Image.frombytes("RGB", (self.sw, self.sh), buf); self.n += 1
        if self.last is None: return Image.new("RGBA", (CW, CH), TEAL_D)
        p = min(1, age / max(dur, 0.1)); z = 1.0 + 0.1 * p                   # push-in
        w, h = int(self.sw / 1.12 * (1.12 / z)), int(self.sh / 1.12 * (1.12 / z))
        x0, y0 = (self.sw - w) // 2, (self.sh - h) // 2
        return self.last.crop((x0, y0, x0 + w, y0 + h)).resize((CW, CH), Image.BICUBIC).convert("RGBA")

def person(d, x, y, s, col):
    d.ellipse([x - 28 * s, y - 120 * s, x + 28 * s, y - 64 * s], fill=col)
    d.rounded_rectangle([x - 50 * s, y - 56 * s, x + 50 * s, y + 60 * s], radius=int(40 * s), fill=col)

def chip_icon(d, x, y, s, col, core=None):
    d.rounded_rectangle([x - 60 * s, y - 60 * s, x + 60 * s, y + 60 * s], radius=int(10 * s), fill=core or col)
    for k in range(5):
        o = -48 * s + k * 24 * s
        for a, b, c, e in ((x + o, y - 60 * s, x + o, y - 82 * s), (x + o, y + 60 * s, x + o, y + 82 * s),
                           (x - 60 * s, y + o, x - 82 * s, y + o), (x + 60 * s, y + o, x + 82 * s, y + o)):
            d.line([(a, b), (c, e)], fill=col, width=max(2, int(6 * s)))

def barrel(d, x, y, s, col):
    d.rounded_rectangle([x - 55 * s, y - 75 * s, x + 55 * s, y + 75 * s], radius=int(18 * s), fill=col)
    for yy in (-35, 35): d.line([(x - 55 * s, y + yy * s), (x + 55 * s, y + yy * s)], fill=TEAL_D, width=int(7 * s))

def label(d, x, y, s, size=36, col=LINE, font="inter", wg=700, anchor="mm"):
    d.text((x, y), s, font=F(font, max(4, int(size)), wg), fill=col, anchor=anchor)

def info(name, age, dur):
    """Draw an animated infographic card."""
    im = Image.new("RGBA", (CW, CH), TEAL_D); d = ImageDraw.Draw(im)
    if name == "gpu":       # CPU: a few big cores vs GPU: many small cores working at once
        label(d, 240, 50, "CPU", 40, GOLD); label(d, 720, 50, "GPU", 40, GOLD)
        for k in range(4):
            r, c = divmod(k, 2); x0, y0 = 120 + c * 125, 110 + r * 125
            on = int(age * 2.5) % 4 == k
            d.rounded_rectangle([x0, y0, x0 + 110, y0 + 110], radius=12, fill=GOLD if on else (40, 90, 85, 255))
        label(d, 240, 400, "beberapa teras besar", 30); label(d, 240, 440, "kira satu demi satu", 30, (200, 200, 190, 255), wg=500)
        n = 12; sz = 26
        for r in range(n):
            for c in range(n):
                x0, y0 = 560 + c * 33, 90 + r * 24
                ph = (math.sin(age * 6 + r * 0.7 + c * 0.4) + 1) / 2
                d.rectangle([x0, y0, x0 + sz, y0 + 18], fill=GOLD if ph > 0.45 else (40, 90, 85, 255))
        label(d, 720, 400, "ribuan teras kecil", 30); label(d, 720, 440, "kira serentak", 30, (200, 200, 190, 255), wg=500)
        d.line([(480, 70), (480, 470)], fill=(60, 110, 104, 255), width=3)
    elif name == "pair":    # two figures linked by a dotted question
        k = ease_out(age / 0.6)
        person(d, 260, 330, 1.3, LINE); person(d, 700, 330, 1.3, (200, 200, 190, 255))
        n = int(14 * ease_out((age - 0.4) / 1.0))
        for j in range(n): d.ellipse([350 + j * 21, 268, 360 + j * 21, 278], fill=GOLD)
        if age > 1.3: label(d, 480, 210, "?", int(110 * min(1, back_out((age - 1.3) / 0.4))), ORANGE, "lora")
        label(d, 260, 450, "Huang", 34); label(d, 700, 450, "Wanita disyaki", 30); label(d, 700, 490, "perisik China", 30)
    elif name == "calendar":
        k = back_out(age / 0.5); w, h = 360 * k, 380 * k; x0, y0 = 300 - w / 2 + 50, 270 - h / 2
        if k > 0.05:
            d.rounded_rectangle([x0, y0, x0 + w, y0 + h], radius=20, fill=LINE)
            d.rounded_rectangle([x0, y0, x0 + w, y0 + h * 0.25], radius=20, fill=RED); d.rectangle([x0, y0 + h * 0.15, x0 + w, y0 + h * 0.25], fill=RED)
            if k > 0.9:
                label(d, x0 + w / 2, y0 + h * 0.13, "NOV 2026", 40, LINE, "poppins", None)
                label(d, x0 + w / 2, y0 + h * 0.6, "12", 170, TEAL_D, "lora")
        k2 = ease_out((age - 0.8) / 0.5)
        if k2 > 0:
            label(d, 720, 200, "CEO", 54, (255, 255, 255, int(255 * k2)), "poppins", None)
            if age > 1.4: d.line([(640, 200), (640 + 160 * ease_out((age - 1.4) / 0.3), 200)], fill=RED, width=8)
            label(d, 720, 290, "Jensen Huang", 40, (247, 241, 232, int(255 * k2)))
            k3 = ease_out((age - 2.0) / 0.5)
            if k3 > 0:
                label(d, 720, 380, "CEO interim:", 34, GOLD[:3] + (int(255 * k3),)); label(d, 720, 425, "Colette Kress", 40, (247, 241, 232, int(255 * k3)))
    elif name == "timeline":
        x0, x1, y = 110, 850, 270; p = ease_out(age / 2.2)
        d.line([(x0, y), (x1, y)], fill=(60, 110, 104, 255), width=14)
        d.line([(x0, y), (x0 + (x1 - x0) * p, y)], fill=GOLD, width=14)
        for yr, fx in ((1993, 0), (2000, 7 / 33), (2010, 17 / 33), (2020, 27 / 33), (2026, 1)):
            xx = x0 + (x1 - x0) * fx; on = p >= fx - 0.001
            d.ellipse([xx - 16, y - 16, xx + 16, y + 16], fill=GOLD if on else (60, 110, 104, 255))
            label(d, xx, y + 60, str(yr), 32, LINE if on else (130, 160, 155, 255))
        label(d, x0, y - 70, "Asas Nvidia", 30, LINE); label(d, x1, y - 70, "Letak jawatan", 30, ORANGE)
        label(d, (x0 + x1) / 2, 450, f"{int(round(33 * p))} tahun sebagai CEO", 44, GOLD, "lora")
    elif name == "oil":
        k = ease_out(age / 0.5); barrel(d, 230, 250, 1.4 * k + 0.01, (200, 200, 190, 255))
        if age > 0.6: label(d, 480, 250, "=", int(140 * min(1, back_out((age - 0.6) / 0.4))), GOLD, "lora")
        k2 = ease_out((age - 0.9) / 0.5)
        if k2 > 0: chip_icon(d, 730, 250, 1.3 * k2 + 0.01, GOLD)
        label(d, 230, 440, "Abad ke-20: minyak", 32); label(d, 730, 440, "Abad ke-21: cip AI", 32, GOLD)
    elif name == "block":
        label(d, 180, 120, "AMERIKA", 44, LINE, "poppins", None); label(d, 780, 120, "CHINA", 44, LINE, "poppins", None)
        d.rounded_rectangle([60, 170, 300, 400], radius=24, outline=LINE, width=5); d.rounded_rectangle([660, 170, 900, 400], radius=24, outline=LINE, width=5)
        cyc = (age % 2.2) / 2.2; x = 200 + 280 * ease_out(min(1, cyc / 0.6))
        chip_icon(d, x, 285, 0.55, GOLD)
        if cyc > 0.55:
            k = min(1, back_out((cyc - 0.55) / 0.2)); cx, cy, r = 560, 285, 70 * k
            d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=RED, width=12); d.line([(cx - r * 0.7, cy - r * 0.7), (cx + r * 0.7, cy + r * 0.7)], fill=RED, width=12)
        label(d, 480, 470, "Sekatan eksport cip AI canggih sejak 2022", 32, GOLD)
    elif name == "chain":
        steps = ["Reka bentuk", "Fabrikasi wafer", "Pemasangan & ujian"]
        for j, s in enumerate(steps):
            k = ease_out((age - j * 0.4) / 0.4); x0 = 40 + j * 310; hl = j == 2
            if k <= 0: continue
            d.rounded_rectangle([x0, 150, x0 + 270, 330], radius=20, fill=GOLD if hl else (40, 90, 85, int(255 * k)))
            for kk, part in enumerate(s.split(" & ") if "&" in s else [s]):
                label(d, x0 + 135, 220 + kk * 46 - (20 if "&" in s else 0), part + (" &" if "&" in s and kk == 0 else ""), 32, TEAL_D if hl else LINE)
            if j < 2: label(d, x0 + 290, 240, "›", 60, GOLD)
        if age > 1.3:
            k = back_out((age - 1.3) / 0.4); label(d, 815, 400, "MALAYSIA", int(38 * max(0.3, k)), GOLD, "poppins", None)
            label(d, 815, 455, "13% dunia", int(34 * max(0.3, k)), LINE)
    elif name == "middle":
        sh = math.sin(age * 9) * 6 if age > 1.0 else 0; push = 60 * ease_out(age / 1.2)
        for cx, txt in ((200 + push, "AMERIKA"), (760 - push, "CHINA")):
            d.ellipse([cx - 170, 270 - 170, cx + 170, 270 + 170], fill=(40, 90, 85, 255), outline=LINE, width=4)
            label(d, cx, 270, txt, 42, LINE, "poppins", None)
        r = 62; d.ellipse([480 - r, 270 - r + sh, 480 + r, 270 + r + sh], fill=GOLD)
        label(d, 480, 270 + sh, "MY", 44, TEAL_D, "poppins", None)
        label(d, 480, 480, "Malaysia di tengah", 36, GOLD, "lora")
    return im

CARD = {0: ("clip", f"{GEM}/v2.mp4", 0.5), 1: ("clip", f"{GEM}/v1.mp4", 0.5), 2: ("info", "gpu"), 3: ("clip", f"{GEM}/v4.mp4", 0.5),
        4: ("clip", f"{GEM}/v4.mp4", 10.6), 5: ("info", "pair"), 6: ("info", "calendar"), 7: ("info", "timeline"),
        8: ("info", "oil"), 9: ("info", "block"), 10: ("info", "chain"), 11: ("info", "middle")}
CLIPS = {k: Clip(v[1], v[2]) for k, v in CARD.items() if v[0] == "clip"}
MASK = Image.new("L", (CW, CH), 0); ImageDraw.Draw(MASK).rounded_rectangle([0, 0, CW - 1, CH - 1], radius=28, fill=255)

def card(i, age, dur):
    c = CARD[i]
    im = CLIPS[i].frame(age, dur) if c[0] == "clip" else info(c[1], age, dur)
    if i == 3:   # 90% bar over the server footage
        d = ImageDraw.Draw(im); p = ease_out(age / 1.6)
        d.rounded_rectangle([40, CH - 70, CW - 40, CH - 34], radius=18, fill=(0, 0, 0, 150))
        d.rounded_rectangle([40, CH - 70, 40 + (CW - 80) * 0.9 * p, CH - 34], radius=18, fill=GOLD)
        d.text((CW - 50, CH - 82), "NVIDIA ~90%", font=F("poppins", 30), fill=LINE, anchor="rb")
    out = Image.new("RGBA", (CW, CH), (0, 0, 0, 0)); out.paste(im, (0, 0), MASK)
    ImageDraw.Draw(out).rounded_rectangle([0, 0, CW - 1, CH - 1], radius=28, outline=GOLD[:3] + (200,), width=4)
    return out
