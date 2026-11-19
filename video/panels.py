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
FONTMAP = {"inter": "inter", "lora": "lora", "poppins": "poppins"}
GRID = (60, 110, 104, 255); OFF_TXT = (130, 160, 155, 255); INK_ON = TEAL_D; PANEL_BG = TEAL_D
def set_theme(t):
    """Rebind panel colours/fonts for a style. Keys: FG GOLD ORANGE TEAL_D RED MUTED DIM GRID OFF_TXT FONTMAP."""
    globals().update(t)

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
        if self.last is None: return Image.new("RGBA", (CW, CH), PANEL_BG)
        z = 1.0 + 0.1 * min(1, age / max(dur, 0.1)); w, h = int(self.sw / z), int(self.sh / z)
        x0, y0 = (self.sw - w) // 2, (self.sh - h) // 2
        return self.last.crop((x0, y0, x0 + w, y0 + h)).resize((CW, CH), Image.BICUBIC).convert("RGBA")
    def close(self):
        if self.p: self.p.kill()

def label(d, x, y, s, size=36, col=None, font="inter", wg=700):
    font = FONTMAP.get(font, font)
    d.text((x, y), s, font=F(font, size, wg if font in ("inter", "lora", "playfair") else None), fill=col or FG, anchor="mm")
def lines(d, x, y, s, size=32, col=None, gap=42):
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
    for yy in (-35, 35): d.line([(x - 55 * s, y + yy * s), (x + 55 * s, y + yy * s)], fill=INK_ON, width=max(1, int(7 * s)))
def globe(d, x, y, s, col):
    r = 80 * s; d.ellipse([x - r, y - r, x + r, y + r], outline=col, width=max(2, int(8 * s)))
    d.ellipse([x - r * 0.45, y - r, x + r * 0.45, y + r], outline=col, width=max(2, int(6 * s))); d.line([(x - r, y), (x + r, y)], fill=col, width=max(2, int(6 * s)))
def book(d, x, y, s, col):
    d.polygon([(x, y - 40 * s), (x - 90 * s, y - 60 * s), (x - 90 * s, y + 60 * s), (x, y + 80 * s)], fill=col)
    d.polygon([(x, y - 40 * s), (x + 90 * s, y - 60 * s), (x + 90 * s, y + 60 * s), (x, y + 80 * s)], fill=col); d.line([(x, y - 40 * s), (x, y + 80 * s)], fill=INK_ON, width=max(2, int(5 * s)))
def money(d, x, y, s, col):
    d.rounded_rectangle([x - 100 * s, y - 55 * s, x + 100 * s, y + 55 * s], radius=int(12 * s), fill=col)
    d.ellipse([x - 30 * s, y - 30 * s, x + 30 * s, y + 30 * s], outline=INK_ON, width=max(2, int(7 * s)))
ICONS = {"barrel": barrel, "chip": chip, "person": person, "globe": globe, "book": book, "money": money}

def info(P, age):
    t = P["type"]; im = Image.new("RGBA", (CW, CH), PANEL_BG); d = ImageDraw.Draw(im)
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
        d.line([(480, 70), (480, 470)], fill=GRID, width=3)
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
            if k > 0.9: label(d, x0 + w / 2, y0 + h * 0.13, P.get("month", ""), 40, FG, "poppins"); label(d, x0 + w / 2, y0 + h * 0.6, P.get("day", ""), 170, INK_ON, "lora")
        k2 = ease_out((age - 0.8) / 0.5)
        if k2 > 0 and P.get("struck"):
            label(d, 720, 200, P["struck"], 54, fade(FG, k2), "poppins"); tw = text_w(F("poppins", 54), P["struck"])
            if age > 1.4: d.line([(720 - tw / 2 - 10, 200), (720 - tw / 2 - 10 + (tw + 20) * ease_out((age - 1.4) / 0.3), 200)], fill=RED, width=8)
        if k2 > 0 and P.get("who"): label(d, 720, 290, P["who"], 40, fade(FG, k2))
        k3 = ease_out((age - 2.0) / 0.5)
        if k3 > 0 and P.get("note"): label(d, 720, 380, P["note"], 34, fade(GOLD, k3)); label(d, 720, 425, P.get("note2", ""), 40, fade(FG, k3))
    elif t == "timeline":
        a, b = P["start"], P["end"]; x0, x1, y = 110, 850, 270; p = ease_out(age / 2.2)
        d.line([(x0, y), (x1, y)], fill=GRID, width=14); d.line([(x0, y), (x0 + (x1 - x0) * p, y)], fill=GOLD, width=14)
        for yr in [a] + P.get("ticks", []) + [b]:
            fx = (yr - a) / (b - a); xx = x0 + (x1 - x0) * fx; on = p >= fx - 0.001
            d.ellipse([xx - 16, y - 16, xx + 16, y + 16], fill=GOLD if on else GRID); label(d, xx, y + 70, str(yr), 46, FG if on else OFF_TXT)
        label(d, x0 + 60, y - 80, P.get("left", ""), 42); label(d, x1 - 60, y - 80, P.get("right", ""), 42, ORANGE)
        label(d, (x0 + x1) / 2, 455, P.get("caption", "{n} tahun").format(n=int(round((b - a) * p))), 72, GOLD, "lora")
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
            lines(d, x0 + bw / 2, 240, s.replace(" & ", " &|"), 30, INK_ON if on else FG)
            if j < n - 1: label(d, x0 + bw + 20, 240, "›", 60, GOLD)
        if age > 1.3 and P.get("note"):
            k = max(0.3, back_out((age - 1.3) / 0.4)); xh = 40 + hl * (bw + 40) + bw / 2
            label(d, xh, 400, P["note"], 38 * k, GOLD, "poppins"); label(d, xh, 455, P.get("note2", ""), 34 * k, FG)
    elif t == "middle":
        sh = math.sin(age * 9) * 6 if age > 1.0 else 0; push = 60 * ease_out(age / 1.2)
        for cx, txt in ((200 + push, P.get("left", "")), (760 - push, P.get("right", ""))):
            d.ellipse([cx - 170, 100, cx + 170, 440], fill=DIM, outline=FG, width=4); label(d, cx, 270, txt, 42, FG, "poppins")
        d.ellipse([418, 208 + sh, 542, 332 + sh], fill=GOLD); label(d, 480, 270 + sh, P.get("mid", "MY"), 44, INK_ON, "poppins")
        label(d, 480, 485, P.get("caption", ""), 36, GOLD, "lora")
    elif t == "bars":
        items = P["items"]; mx = max(v for _, v in items); unit = P.get("unit", "")
        for j, (name, v) in enumerate(items):
            y = 90 + j * (360 / len(items)); p = ease_out((age - j * 0.2) / 1.2)
            label(d, 150, y + 30, name, 32, FG); d.rounded_rectangle([280, y + 8, 280 + 560 * v / mx * p + 1, y + 52], radius=12, fill=GOLD if j == P.get("highlight", 0) else DIM)
            d.text((300 + 560 * v / mx * p, y + 30), f"{v * p:.{0 if float(v).is_integer() else 1}f}{unit}", font=F("inter", 32, 700), fill=FG, anchor="lm")
        label(d, 480, 480, P.get("caption", ""), 32, GOLD)
    elif t == "text":
        for j, s in enumerate(P["lines"]):
            k = ease_out((age - j * 0.3) / 0.5); sz = P.get("size", 88)
            while sz > 40 and text_w(F(FONTMAP.get("lora", "lora"), sz, 700), s) > 900: sz -= 4
            label(d, 480, 270 + (j - (len(P["lines"]) - 1) / 2) * (sz * 1.35), s, sz, fade(GOLD if j == 0 else FG, k), "lora")
    return im

class Panel:
    def __init__(self, spec, root):
        self.P = spec; self.clip = Clip(os.path.join(root, spec["file"]), spec.get("start", 0)) if spec["type"] == "clip" else None
        if self.clip and not os.path.exists(self.clip.path):     # footage missing: fall back to a text panel
            self.clip = None; self.P = {"type": "text", "lines": spec.get("fallback", ["", ""])}
    def render(self, age, dur, frame_fn=None):
        im = self.clip.frame(age, dur) if self.clip else info(self.P, age)
        bar = self.P.get("bar")
        if bar:
            d = ImageDraw.Draw(im); p = ease_out(age / 1.6)
            d.rounded_rectangle([40, CH - 70, CW - 40, CH - 34], radius=18, fill=(0, 0, 0, 150))
            d.rounded_rectangle([40, CH - 70, 40 + (CW - 80) * bar["value"] * p, CH - 34], radius=18, fill=GOLD)
            d.text((CW - 50, CH - 82), bar["label"], font=F("poppins", 30), fill=FG, anchor="rb")
        if frame_fn: return frame_fn(im, self.clip is not None)
        out = Image.new("RGBA", (CW, CH), (0, 0, 0, 0)); out.paste(im, (0, 0), MASK)
        ImageDraw.Draw(out).rounded_rectangle([0, 0, CW - 1, CH - 1], radius=28, outline=fade(GOLD, 0.8), width=4)
        return out

# ---------------- added 17 Nov 2026: pagoda, flex, seats, seatrows, trio, versus ----------------
def _col(k):
    return {"accent": GOLD, "fg": FG, "muted": MUTED, "dim": DIM, "red": RED}.get(k, FG)

def pagoda(d, cx, base, age, P, scale=1.0):
    floors = 5; shake = P.get("shake", True); amp = P.get("amp", 10) * scale
    gx = (4 * math.sin(age * 28)) if shake and int(age * 2) % 3 != 2 else 0          # ground jolts
    hl = P.get("highlight_pillar", False); fh = 58 * scale; top = base - floors * fh - 30 * scale
    xs = []
    for i in range(floors):
        ph = math.sin(age * 5.5) * ((-1) ** i) * amp * (i + 1) / floors if shake else 0
        xs.append(cx + gx + ph)
    # central pillar first (behind floors when not highlighted)
    pcol = GOLD if hl else FG
    d.line([(cx + gx, base), (xs[-1], top - 50 * scale)], fill=pcol, width=int((14 if hl else 8) * scale))
    for i in range(floors):
        w = (300 - i * 34) * scale; y1 = base - i * fh; y0 = y1 - fh * 0.62; x = xs[i]
        d.rectangle([x - w * 0.36, y0, x + w * 0.36, y1], fill=MUTED)
        if hl: d.rectangle([x - 7 * scale, y0, x + 7 * scale, y1], fill=GOLD)
        ry = y0; d.polygon([(x - w / 2 - 14 * scale, ry + 6 * scale), (x + w / 2 + 14 * scale, ry + 6 * scale), (x + w * 0.3, ry - fh * 0.38), (x - w * 0.3, ry - fh * 0.38)], fill=FG)
        labs = P.get("labels", [])
        if i < len(labs) and labs[i]:
            d.text((x + w / 2 + 40 * scale, (y0 + y1) / 2), labs[i], font=F(FONTMAP.get("inter", "inter"), 30 * scale, 700), fill=FG, anchor="lm")
    d.line([(xs[-1], top - 10 * scale), (xs[-1], top - 80 * scale)], fill=FG, width=int(6 * scale))
    for k in range(4): d.ellipse([xs[-1] - 9 * scale, top - 30 * scale - k * 14 * scale, xs[-1] + 9 * scale, top - 18 * scale - k * 14 * scale], outline=FG, width=3)
    d.line([(cx - 260 * scale, base + 4), (cx + 260 * scale, base + 4)], fill=FG, width=6)
    if P.get("pillar_label"):
        ly = base - fh * 2.4; lx = max(cx - 290 * scale, text_w(F(FONTMAP.get("inter", "inter"), 30 * scale, 700), P["pillar_label"]) + 30)
        d.text((lx, ly), P["pillar_label"], font=F(FONTMAP.get("inter", "inter"), 30 * scale, 700), fill=GOLD if hl else FG, anchor="rm")
        d.line([(lx + 8, ly), (cx + gx - 12, ly)], fill=GOLD if hl else FG, width=3)
    if P.get("height_label"):
        hx = cx + 230 * scale; d.line([(hx, base), (hx, top - 80 * scale)], fill=FG, width=3)
        for yy in (base, top - 80 * scale): d.line([(hx - 12, yy), (hx + 12, yy)], fill=FG, width=3)
        d.text((hx + 18, (base + top) / 2), P["height_label"], font=F(FONTMAP.get("inter", "inter"), 34 * scale, 700), fill=FG, anchor="lm")

def info_extra(P, age):
    t = P["type"]; im = Image.new("RGBA", (CW, CH), PANEL_BG); d = ImageDraw.Draw(im)
    if t == "pagoda":
        pagoda(d, P.get("cx", 400 if P.get("labels") else 480), 470, age, P)
        if P.get("caption"): label(d, 480, 515, P["caption"], 30, FG)
        if P.get("question") and age > 0.8: label(d, 820, 200, "?", 140, GOLD, "lora")
    elif t == "flex":
        # left: rigid block tower that cracks and leans; right: flexible stack that sways back
        lean = min(1, max(0, (age - 1.0) / 0.8)) * 9 if P.get("crack", True) else 0
        L = Image.new("RGBA", (220, 340), (0, 0, 0, 0)); ld = ImageDraw.Draw(L); ld.rectangle([50, 20, 170, 330], fill=MUTED)
        if age > 1.0: ld.line([(60, 200), (110, 175), (95, 150), (160, 120)], fill=RED, width=6)
        L = L.rotate(-lean, center=(110, 330), resample=Image.BICUBIC); im.alpha_composite(L, (130, 90))
        for i in range(6):
            off = math.sin(age * 5) * ((-1) ** i) * 6 * (i + 1) / 6
            d.rectangle([610 + off, 410 - i * 52, 730 + off, 450 - i * 52], fill=MUTED); d.line([(670, 450), (670 + off, 410 - i * 52)], fill=GOLD, width=4)
        d.line([(80, 424), (880, 424)], fill=FG, width=5)
        label(d, 240, 480, P.get("left", "Keras: retak"), 34, FG); label(d, 670, 480, P.get("right", "Lentur: bertahan"), 34, GOLD)
    elif t == "seats":
        total = P["total"]; groups = P["groups"]; cols = P.get("cols", 14); r = P.get("r", 22); gap = 2 * r + 10
        rows = (total + cols - 1) // cols; x0 = (CW - (cols - 1) * gap) / 2; y0 = 80 + (300 - (rows - 1) * gap) / 2
        seq = [c for _, n, c in groups for _ in range(n)]
        for k in range(total):
            rr, cc = divmod(k, cols); col = _col(seq[k]) if k < len(seq) else DIM
            d.ellipse([x0 + cc * gap - r, y0 + rr * gap - r, x0 + cc * gap + r, y0 + rr * gap + r], fill=col)
        lx = 120
        for name, n, c in groups:
            d.ellipse([lx, 450, lx + 26, 476], fill=_col(c)); t2 = f"{name} {n}"
            d.text((lx + 36, 463), t2, font=F(FONTMAP.get("inter", "inter"), 30, 700), fill=FG, anchor="lm"); lx += 80 + text_w(F(FONTMAP.get("inter", "inter"), 30, 700), t2)
    elif t == "seatrows":
        rows = P["rows"]; y = 70
        for name, won, total, note in rows:
            d.text((40, y + 22), name, font=F(FONTMAP.get("inter", "inter"), 32, 700), fill=FG, anchor="lm")
            r = 8 if total > 40 else 10; gap = 2 * r + 4; x0 = 260
            for k in range(total):
                rr, cc = divmod(k, 28); d.ellipse([x0 + cc * gap, y + rr * gap, x0 + cc * gap + 2 * r, y + rr * gap + 2 * r], fill=GOLD if k < won else DIM)
            d.text((x0, y + 2 * gap * ((total - 1) // 28 + 1) - 4), f"{won}/{total}  {note}".strip(), font=F(FONTMAP.get("inter", "inter"), 26, 600), fill=FG); y += 150
    elif t == "trio":
        names = P["names"]; d.rectangle([150, 250, 810, 268], fill=FG)                       # the beam they hold up
        d.rectangle([466, 40, 494, 250], fill=GOLD); label(d, 480, 30, P.get("pillar", ""), 30, GOLD)
        for j, nm in enumerate(names):
            x = 220 + j * 260; person(d, x, 380, 1.0, FG); lines(d, x, 480, nm, 28, FG, 34)
    elif t == "versus":
        for j, side in enumerate((P["left"], P["right"])):
            x = 240 + j * 480
            lines(d, x, 200, side["text"], 36, FG, 48)
            m = side.get("mark"); c = GOLD if m == "yes" else RED
            if m == "yes": d.line([(x - 40, 380), (x - 10, 410), (x + 50, 340)], fill=c, width=12)
            elif m == "no": d.line([(x - 40, 340), (x + 40, 420)], fill=c, width=12); d.line([(x + 40, 340), (x - 40, 420)], fill=c, width=12)
            if side.get("note"): label(d, x, 470, side["note"], 30, FG)
        d.line([(480, 80), (480, 460)], fill=DIM, width=3)
    return im

EXTRA_TYPES = {"pagoda", "flex", "seats", "seatrows", "trio", "versus"}
_info_base = info
def info(P, age):
    return info_extra(P, age) if P["type"] in EXTRA_TYPES else _info_base(P, age)

# ---------------- added 18 Nov 2026: tree, compound, grid (maths episodes) ----------------
def _sup(d, x, y, base, sup, size, col, anchor_mid=True):
    """Draw base text with a superscript; (x, y) is the centre of the whole expression."""
    fb = F(FONTMAP.get("anton", "anton"), size); fs = F(FONTMAP.get("anton", "anton"), int(size * 0.5))
    wb, ws = text_w(fb, base), text_w(fs, sup); x0 = x - (wb + ws + 6) / 2 if anchor_mid else x
    d.text((x0, y), base, font=fb, fill=col, anchor="lm"); d.text((x0 + wb + 6, y - size * 0.32), sup, font=fs, fill=col, anchor="lm")
    return x0 + wb + ws + 6

def info_maths(P, age):
    t = P["type"]; im = Image.new("RGBA", (CW, CH), PANEL_BG); d = ImageDraw.Draw(im)
    fi = lambda sz, w=700: F(FONTMAP.get("inter", "inter"), sz, w)
    if t == "tree":
        gens = P.get("gens", 7); y0, step = 36, 56; shown = min(gens, int(max(0, age - P.get("start", 0)) / P.get("pace", 0.4)))
        TX = CW / 2 - 40; prev = [(TX, y0)]; d.ellipse([TX - 9, y0 - 9, TX + 9, y0 + 9], fill=GOLD)
        d.text((TX + 24, y0), P.get("you", "Anda"), font=fi(34), fill=FG, anchor="lm")
        collapse = P.get("collapse") and age > P.get("collapse_at", 1.2)
        for g in range(1, shown + 1):
            n = 2 ** g; span = min(780, 60 * n); x0 = TX - span / 2; gap = span / (n - 1); y = y0 + g * step
            r = max(2.5, min(8, gap * 0.36)); cur = []
            for k in range(n):
                x = x0 + k * gap; cur.append((x, y))
                if g <= 5: d.line([prev[k // 2], (x, y)], fill=DIM, width=2)
                dead = collapse and g == gens and (k * 37) % 128 < 28          # ~22% of the last row are repeats
                d.ellipse([x - r, y - r, x + r, y + r], fill=(DIM if dead else (GOLD if g == gens else FG)))
            prev = cur
            d.text((CW - 8, y), str(n), font=fi(30, 700), fill=MUTED, anchor="rm")
        if shown >= gens:
            if collapse: label(d, CW / 2, 498, P.get("collapse_label", "≈ 100 orang berbeza"), 56, GOLD)
            else:
                fa = F(FONTMAP.get("anton", "anton"), 72); tail = f"  =  {2 ** gens}"; wt = text_w(fa, tail)
                xe = _sup(d, CW / 2 - wt / 2 - 30, 498, "2", str(gens), 72, FG); d.text((xe, 498), tail, font=fa, fill=GOLD, anchor="lm")
    elif t == "compound":
        base = P.get("base", 0.99); N = P.get("n", 100); k = max(1, min(N, int(1 + max(0, age - P.get("start", 0)) * P.get("speed", 40))))
        v = base ** k; t_full = P.get("start", 0) + N / P.get("speed", 40); flip = P.get("flip") and k >= N and age > t_full + 0.8
        _sup(d, CW / 2, 105, "0.99", str(k), 140, FG); d.text((CW / 2, 250), f"= {v * 100:.0f}%", font=F(FONTMAP.get("anton", "anton"), 120), fill=GOLD, anchor="mm")
        bx0, bx1, by = 40, CW - 40, 340
        d.rounded_rectangle([bx0, by, bx1, by + 64], radius=28, fill=DIM)
        d.rounded_rectangle([bx0, by, bx0 + (bx1 - bx0) * v, by + 64], radius=28, fill=FG)
        d.text((bx0, by + 100), P.get("clean_label", "peluang semua moyang bersih"), font=fi(38, 700), fill=FG, anchor="lm")
        if flip:
            q = ease_out((age - t_full - 0.8) / 0.6)
            d.rounded_rectangle([bx0 + (bx1 - bx0) * v, by, bx0 + (bx1 - bx0) * (v + (1 - v) * q), by + 64], radius=28, fill=RED)
            d.text((bx1, by + 165), f"1 − {v:.2f} = {1 - v:.2f}  →  {(1 - v) * 100:.0f}%", font=fi(50, 800), fill=RED, anchor="rm")
    elif t == "grid":
        cols = P.get("cols", 10); rows = P.get("rows", 10); total = cols * rows; fill = P["filled"]
        on = min(fill, int(age * P.get("speed", 45))); r = 17; gap = 42; x0 = (CW - (cols - 1) * gap) / 2; y0 = 26
        for k in range(total):
            rr, cc = divmod(k, cols); x = x0 + cc * gap; y = y0 + rr * gap
            d.ellipse([x - r, y - r, x + r, y + r], fill=(RED if k < on else DIM))
        if P.get("caption"): label(d, CW / 2, 455, P["caption"], 50, FG)
        if P.get("note"): label(d, CW / 2, 512, P["note"], 34, MUTED)
    return im

MATHS_TYPES = {"tree", "compound", "grid"}
_info_prev = info
def info(P, age):
    return info_maths(P, age) if P["type"] in MATHS_TYPES else _info_prev(P, age)
