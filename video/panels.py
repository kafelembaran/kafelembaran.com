"""Visual panels for the middle scenes: 960x540 window under the headline.
Each panel is {"type": ..., params}. Types:
  clip      {"file": "clips/x.mp4", "start": 0.5, "bar": {"label": "NVIDIA ~90%", "value": 0.9}}  (footage, slow push-in)
  cores     {"left": "CPU", "right": "GPU", ...captions}            few big cores vs many small cores
  pair      {"left": "Huang", "right": "Wanita disyaki|perisik China"}  two figures + dotted line + "?"
  calendar  {"month": "NOV 2026", "day": "12", "struck": "CEO", "who": "Jensen Huang", "note": "CEO interim:", "note2": "Colette Kress"}
  timeline  {"start": 1993, "end": 2026, "ticks": [2000, 2010, 2020], "left": "Asas Nvidia", "right": "Letak jawatan", "caption": "{n} tahun sebagai CEO"}
  equals    {"left_icon": "barrel|chip|person|globe|book|money", "left": "...", "right_icon": "...", "right": "..."}
  block     {"from": "AMERIKA", "to": "CHINA", "caption": "...", "item": "chip"}
  chain     {"steps": ["Reka bentuk", "Fabrikasi wafer", "Pemasangan & ujian"], "highlight": 2, "note": "MALAYSIA", "note2": "13% dunia"}
  middle    {"left": "AMERIKA", "right": "CHINA", "mid": "MY", "caption": "Malaysia di tengah"}
  bars      {"items": [["Nvidia", 90], ["Lain-lain", 10]], "unit": "%", "caption": "..."}
  text      {"lines": ["...", "..."]}                               fallback: big quote-style text
"""
import math, subprocess, os
from PIL import Image, ImageDraw
from kl import F, FG, GOLD, ORANGE, TEAL_D, RED, MUTED, DIM, ease_out, back_out, text_w, fade

CX0, CY0, CW, CH = 60, 790, 960, 540
MASK = Image.new("L", (CW, CH), 0); ImageDraw.Draw(MASK).rounded_rectangle([0, 0, CW - 1, CH - 1], radius=28, fill=255)

class Clip:
    def __init__(self, path, start=0.0):
        self.path, self.start, self.p, self.last, self.n = path, start, None, None, 0
        self.sw, self.sh = int(CW * 1.12) // 2 * 2, int(CH * 1.12) // 2 * 2
    def frame(self, age, dur):
        if self.p is None:
            self.p = subprocess.Popen(["ffmpeg", "-loglevel", "quiet", "-ss", str(self.start), "-stream_loop", "-1", "-i", self.path, "-vf",
                                       f"fps=30,scale={self.sw}:{self.sh}:force_original_aspect_ratio=increase,crop={self.sw}:{self.sh},eq=saturation=0.85",
                                       "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
        sz = self.sw * self.sh * 3
        while self.n <= int(age * 30):
            buf = self.p.stdout.read(sz)
            if len(buf) < sz: break
            self.last = Image.frombytes("RGB", (self.sw, self.sh), buf); self.n += 1
        if self.last is None: return Image.new("RGBA", (CW, CH), TEAL_D)
        z = 1.0 + 0.1 * min(1, age / max(dur, 0.1)); w, h = int(self.sw / z), int(self.sh / z)
        x0, y0 = (self.sw - w) // 2, (self.sh - h) // 2
        return self.last.crop((x0, y0, x0 + w, y0 + h)).resize((CW, CH), Image.BICUBIC).convert("RGBA")
    def close(self):
        if self.p: self.p.kill()

def label(d, x, y, s, size=36, col=FG, font="inter", wg=700):
    d.text((x, y), s, font=F(font, size, wg if font in ("inter", "lora") else None), fill=col, anchor="mm")
def lines(d, x, y, s, size=32, col=FG, gap=42):
    for j, part in enumerate(s.split("|")): label(d, x, y + j * gap - (len(s.split("|")) - 1) * gap / 2, part, size, col)

def person(d, x, y, s, col):
    d.ellipse([x - 28 * s, y - 120 * s, x + 28 * s, y - 64 * s], fill=col)
    d.rounded_rectangle([x - 50 * s, y - 56 * s, x + 50 * s, y + 60 * s], radius=int(40 * s), fill=col)
def chip(d, x, y, s, col):
    d.rounded_rectangle([x - 60 * s, y - 60 * s, x + 60 * s, y + 60 * s], radius=int(10 * s), fill=col)
    for k in range(5):
        o = -48 * s + k * 24 * s
        for a, b, c, e in ((x + o, y - 60 * s, x + o, y - 82 * s), (x + o, y + 60 * s, x + o, y + 82 * s), (x - 60 * s, y + o, x - 82 * s, y + o), (x + 60 * s, y + o, x + 82 * s, y + o)):
            d.line([(a, b), (c, e)], fill=col, width=max(2, int(6 * s)))
def barrel(d, x, y, s, col):
    d.rounded_rectangle([x - 55 * s, y - 75 * s, x + 55 * s, y + 75 * s], radius=int(18 * s), fill=col)
    for yy in (-35, 35): d.line([(x - 55 * s, y + yy * s), (x + 55 * s, y + yy * s)], fill=TEAL_D, width=max(1, int(7 * s)))
def globe(d, x, y, s, col):
    r = 80 * s; d.ellipse([x - r, y - r, x + r, y + r], outline=col, width=max(2, int(8 * s)))
    d.ellipse([x - r * 0.45, y - r, x + r * 0.45, y + r], outline=col, width=max(2, int(6 * s))); d.line([(x - r, y), (x + r, y)], fill=col, width=max(2, int(6 * s)))
def book(d, x, y, s, col):
    d.polygon([(x, y - 40 * s), (x - 90 * s, y - 60 * s), (x - 90 * s, y + 60 * s), (x, y + 80 * s)], fill=col)
    d.polygon([(x, y - 40 * s), (x + 90 * s, y - 60 * s), (x + 90 * s, y + 60 * s), (x, y + 80 * s)], fill=col); d.line([(x, y - 40 * s), (x, y + 80 * s)], fill=TEAL_D, width=max(2, int(5 * s)))
def money(d, x, y, s, col):
    d.rounded_rectangle([x - 100 * s, y - 55 * s, x + 100 * s, y + 55 * s], radius=int(12 * s), fill=col)
    d.ellipse([x - 30 * s, y - 30 * s, x + 30 * s, y + 30 * s], outline=TEAL_D, width=max(2, int(7 * s)))
ICONS = {"barrel": barrel, "chip": chip, "person": person, "globe": globe, "book": book, "money": money}

def info(P, age):
    t = P["type"]; im = Image.new("RGBA", (CW, CH), TEAL_D); d = ImageDraw.Draw(im)
    if t == "cores":
        label(d, 240, 50, P.get("left", "CPU"), 40, GOLD); label(d, 720, 50, P.get("right", "GPU"), 40, GOLD)
        for k in range(4):
            r, c = divmod(k, 2); x0, y0 = 120 + c * 125, 110 + r * 125
            d.rounded_rectangle([x0, y0, x0 + 110, y0 + 110], radius=12, fill=GOLD if int(age * 2.5) % 4 == k else DIM)
        for r in range(12):
            for c in range(12):
                on = (math.sin(age * 6 + r * 0.7 + c * 0.4) + 1) / 2 > 0.45
                d.rectangle([560 + c * 33, 90 + r * 24, 586 + c * 33, 108 + r * 24], fill=GOLD if on else DIM)
        lines(d, 240, 420, P.get("left_caption", "beberapa teras besar|kira satu demi satu"), 30)
        lines(d, 720, 420, P.get("right_caption", "ribuan teras kecil|kira serentak"), 30)
        d.line([(480, 70), (480, 470)], fill=(60, 110, 104, 255), width=3)
    elif t == "pair":
        person(d, 260, 330, 1.3, FG); person(d, 700, 330, 1.3, MUTED)
        for j in range(int(14 * ease_out((age - 0.4) / 1.0))): d.ellipse([350 + j * 21, 268, 360 + j * 21, 278], fill=GOLD)
        if age > 1.3: label(d, 480, 210, "?", 110 * min(1, back_out((age - 1.3) / 0.4)), ORANGE, "lora")
        lines(d, 260, 470, P.get("left", ""), 32); lines(d, 700, 470, P.get("right", ""), 30)
    elif t == "calendar":
        k = back_out(age / 0.5); w, h = 360 * k, 380 * k; x0, y0 = 350 - w / 2, 270 - h / 2
        if k > 0.05:
            d.rounded_rectangle([x0, y0, x0 + w, y0 + h], radius=20, fill=FG)
            d.rounded_rectangle([x0, y0, x0 + w, y0 + h * 0.25], radius=20, fill=RED); d.rectangle([x0, y0 + h * 0.15, x0 + w, y0 + h * 0.25], fill=RED)
            if k > 0.9: label(d, x0 + w / 2, y0 + h * 0.13, P.get("month", ""), 40, FG, "poppins"); label(d, x0 + w / 2, y0 + h * 0.6, P.get("day", ""), 170, TEAL_D, "lora")
        k2 = ease_out((age - 0.8) / 0.5)
        if k2 > 0 and P.get("struck"):
            label(d, 720, 200, P["struck"], 54, fade((255, 255, 255, 255), k2), "poppins"); tw = text_w(F("poppins", 54), P["struck"])
            if age > 1.4: d.line([(720 - tw / 2 - 10, 200), (720 - tw / 2 - 10 + (tw + 20) * ease_out((age - 1.4) / 0.3), 200)], fill=RED, width=8)
        if k2 > 0 and P.get("who"): label(d, 720, 290, P["who"], 40, fade(FG, k2))
        k3 = ease_out((age - 2.0) / 0.5)
        if k3 > 0 and P.get("note"): label(d, 720, 380, P["note"], 34, fade(GOLD, k3)); label(d, 720, 425, P.get("note2", ""), 40, fade(FG, k3))
    elif t == "timeline":
        a, b = P["start"], P["end"]; x0, x1, y = 110, 850, 270; p = ease_out(age / 2.2)
        d.line([(x0, y), (x1, y)], fill=(60, 110, 104, 255), width=14); d.line([(x0, y), (x0 + (x1 - x0) * p, y)], fill=GOLD, width=14)
        for yr in [a] + P.get("ticks", []) + [b]:
            fx = (yr - a) / (b - a); xx = x0 + (x1 - x0) * fx; on = p >= fx - 0.001
            d.ellipse([xx - 16, y - 16, xx + 16, y + 16], fill=GOLD if on else (60, 110, 104, 255)); label(d, xx, y + 60, str(yr), 32, FG if on else (130, 160, 155, 255))
        label(d, x0, y - 70, P.get("left", ""), 30); label(d, x1, y - 70, P.get("right", ""), 30, ORANGE)
        label(d, (x0 + x1) / 2, 450, P.get("caption", "{n} tahun").format(n=int(round((b - a) * p))), 44, GOLD, "lora")
    elif t == "equals":
        k = ease_out(age / 0.5); ICONS[P.get("left_icon", "barrel")](d, 230, 250, 1.4 * k + 0.01, MUTED)
        if age > 0.6: label(d, 480, 250, P.get("sign", "="), 140 * min(1, back_out((age - 0.6) / 0.4)), GOLD, "lora")
        k2 = ease_out((age - 0.9) / 0.5)
        if k2 > 0: ICONS[P.get("right_icon", "chip")](d, 730, 250, 1.3 * k2 + 0.01, GOLD)
        lines(d, 230, 450, P.get("left", ""), 32); lines(d, 730, 450, P.get("right", ""), 32, GOLD)
    elif t == "block":
        label(d, 180, 120, P.get("from", ""), 44, FG, "poppins"); label(d, 780, 120, P.get("to", ""), 44, FG, "poppins")
        d.rounded_rectangle([60, 170, 300, 400], radius=24, outline=FG, width=5); d.rounded_rectangle([660, 170, 900, 400], radius=24, outline=FG, width=5)
        cyc = (age % 2.2) / 2.2; ICONS[P.get("item", "chip")](d, 200 + 280 * ease_out(min(1, cyc / 0.6)), 285, 0.55, GOLD)
        if cyc > 0.55:
            k = min(1, back_out((cyc - 0.55) / 0.2)); r = 70 * k
            d.ellipse([560 - r, 285 - r, 560 + r, 285 + r], outline=RED, width=12); d.line([(560 - r * 0.7, 285 - r * 0.7), (560 + r * 0.7, 285 + r * 0.7)], fill=RED, width=12)
        label(d, 480, 470, P.get("caption", ""), 32, GOLD)
    elif t == "chain":
        steps = P["steps"]; n = len(steps); bw = (880 - 40 * (n - 1)) / n; hl = P.get("highlight", n - 1)
        for j, s in enumerate(steps):
            k = ease_out((age - j * 0.4) / 0.4)
            if k <= 0: continue
            x0 = 40 + j * (bw + 40); on = j == hl
            d.rounded_rectangle([x0, 150, x0 + bw, 330], radius=20, fill=GOLD if on else DIM)
            lines(d, x0 + bw / 2, 240, s.replace(" & ", " &|"), 30, TEAL_D if on else FG)
            if j < n - 1: label(d, x0 + bw + 20, 240, "›", 60, GOLD)
        if age > 1.3 and P.get("note"):
            k = max(0.3, back_out((age - 1.3) / 0.4)); xh = 40 + hl * (bw + 40) + bw / 2
            label(d, xh, 400, P["note"], 38 * k, GOLD, "poppins"); label(d, xh, 455, P.get("note2", ""), 34 * k, FG)
    elif t == "middle":
        sh = math.sin(age * 9) * 6 if age > 1.0 else 0; push = 60 * ease_out(age / 1.2)
        for cx, txt in ((200 + push, P.get("left", "")), (760 - push, P.get("right", ""))):
            d.ellipse([cx - 170, 100, cx + 170, 440], fill=DIM, outline=FG, width=4); label(d, cx, 270, txt, 42, FG, "poppins")
        d.ellipse([418, 208 + sh, 542, 332 + sh], fill=GOLD); label(d, 480, 270 + sh, P.get("mid", "MY"), 44, TEAL_D, "poppins")
        label(d, 480, 485, P.get("caption", ""), 36, GOLD, "lora")
    elif t == "bars":
        items = P["items"]; mx = max(v for _, v in items); unit = P.get("unit", "")
        for j, (name, v) in enumerate(items):
            y = 90 + j * (360 / len(items)); p = ease_out((age - j * 0.2) / 1.2)
            label(d, 150, y + 30, name, 32, FG); d.rounded_rectangle([280, y + 8, 280 + 560 * v / mx * p + 1, y + 52], radius=12, fill=GOLD if j == 0 else DIM)
            d.text((300 + 560 * v / mx * p, y + 30), f"{v * p:.0f}{unit}", font=F("inter", 32, 700), fill=FG, anchor="lm")
        label(d, 480, 480, P.get("caption", ""), 32, GOLD)
    elif t == "text":
        for j, s in enumerate(P["lines"]):
            k = ease_out((age - j * 0.3) / 0.5); label(d, 480, 270 + (j - (len(P["lines"]) - 1) / 2) * 80, s, 56, fade(GOLD if j == 0 else FG, k), "lora")
    return im

class Panel:
    def __init__(self, spec, root):
        self.P = spec; self.clip = Clip(os.path.join(root, spec["file"]), spec.get("start", 0)) if spec["type"] == "clip" else None
        if self.clip and not os.path.exists(self.clip.path):     # footage missing: fall back to a text panel
            self.clip = None; self.P = {"type": "text", "lines": spec.get("fallback", ["", ""])}
    def render(self, age, dur):
        im = self.clip.frame(age, dur) if self.clip else info(self.P, age)
        bar = self.P.get("bar")
        if bar:
            d = ImageDraw.Draw(im); p = ease_out(age / 1.6)
            d.rounded_rectangle([40, CH - 70, CW - 40, CH - 34], radius=18, fill=(0, 0, 0, 150))
            d.rounded_rectangle([40, CH - 70, 40 + (CW - 80) * bar["value"] * p, CH - 34], radius=18, fill=GOLD)
            d.text((CW - 50, CH - 82), bar["label"], font=F("poppins", 30), fill=FG, anchor="rb")
        out = Image.new("RGBA", (CW, CH), (0, 0, 0, 0)); out.paste(im, (0, 0), MASK)
        ImageDraw.Draw(out).rounded_rectangle([0, 0, CW - 1, CH - 1], radius=28, outline=fade(GOLD, 0.8), width=4)
        return out
