"""Render 7 short style samples (~12.5 s) of 'Jensen Huang & Nvidia dalam 40 saat'.
Usage: python3 render_samples.py <theme numbers...>
"""
import sys, math, random, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
D = "/home/claude/samples"; FD = "/home/claude/fonts"
GF = "/usr/share/fonts/truetype/google-fonts"
LIB = "/usr/share/fonts/truetype/liberation"
FONT = {
 "lora": f"{GF}/Lora-Variable.ttf", "poppins": f"{GF}/Poppins-Bold.ttf", "montserrat": f"{FD}/Montserrat.ttf",
 "inter": f"{FD}/Inter.ttf", "anton": f"{FD}/Anton.ttf", "mono": f"{FD}/ShareTechMono.ttf", "oswald": f"{FD}/Oswald.ttf",
 "playfair": f"{FD}/Playfair.ttf", "jet": f"{FD}/JetBrainsMono.ttf", "lib": f"{LIB}/LiberationSans-Regular.ttf",
}
def F(name, size, wght=None):
    f = ImageFont.truetype(FONT[name], size)
    if wght:
        try:
            axes = f.get_variation_axes()
            vals = [a.get("default", 400) for a in axes]
            for i, a in enumerate(axes):
                if str(a.get("name", b"")).lower().find("weight") >= 0 or a.get("name") in (b"Weight", "Weight"):
                    vals[i] = max(a["minimum"], min(a["maximum"], wght))
            f.set_variation_by_axes(vals)
        except Exception:
            pass
    return f
hexc = lambda h, a=255: tuple(int(h[i:i+2], 16) for i in (1, 3, 5)) + (a,)

THEMES = {
 1: dict(name="kafe-klasik", bg=["#165450", "#123f3c"], fg="#f7f1e8", acc="#f2c14e", acc2="#e07a3a",
         head=("lora", 700), cap=("poppins", None), capstyle="outline", trans="fade", sil=0.18, clock="#ffffff"),
 2: dict(name="berita-moden", bg=["#14181f", "#1b2130"], fg="#ffffff", acc="#fbbf24", acc2="#ef4444",
         head=("montserrat", 900), cap=("inter", 800), capstyle="box", trans="fade", sil=0.12, clock="#fbbf24"),
 3: dict(name="tabloid-tegas", bg=["#0b0b0b", "#1a0507"], fg="#ffffff", acc="#ff2d3d", acc2="#ffd400",
         head=("anton", None), cap=("anton", None), capstyle="outline", trans="cut", sil=0.14, clock="#ff2d3d", bars=True),
 4: dict(name="kertas-editorial", bg=["#f3ede1", "#efe6d6"], fg="#1b1b1b", acc="#c0392b", acc2="#c0392b",
         head=("playfair", 800), cap=("inter", 700), capstyle="marker", trans="fade", sil=0.10, clock="#1b1b1b", paper=True),
 5: dict(name="terminal-data", bg=["#050b08", "#06100c"], fg="#d1fae5", acc="#34d399", acc2="#fbbf24",
         head=("jet", 800), cap=("jet", 700), capstyle="mono", trans="cut", sil=0.12, clock="#34d399", grid=True),
 6: dict(name="huruf-gergasi", bg=["#165450", "#e07a3a", "#123f3c", "#c2571f"], fg="#ffffff", acc="#f2c14e", acc2="#f7f1e8",
         head=("oswald", 700), cap=("oswald", 600), capstyle="outline", trans="slide", sil=0.0, clock="#ffffff", giant=True),
 7: dict(name="gerak-penuh", bg=["#165450", "#123f3c"], fg="#f7f1e8", acc="#f2c14e", acc2="#e07a3a",
         head=("lora", 700), cap=("poppins", None), capstyle="pop", trans="slide", sil=0.20, clock="#ffffff", parallax=True),
}

# ---- timeline (seconds) ----
SC = [("intro", 0.0, 2.4), ("y1963", 2.4, 5.0), ("p90", 5.0, 8.2), ("dakwaan", 8.2, 10.6), ("end", 10.6, 12.6)]
CLOCK0 = 2.4; TOTAL = 12.6
CAPS = {"intro": "JENSEN HUANG & *NVIDIA*", "y1963": "LAHIR DI *TAIWAN*", "p90": "KINI KUASAI *~90%*",
        "dakwaan": "HUANG *DIDAKWA* RAPAT", "end": "LINK BUKU KAT *BIO*"}
SIL = {"intro": "gpu", "y1963": "wafer", "p90": None, "dakwaan": "figures", "end": None}
sil_img = {k: Image.open(f"{D}/sil_{k}.png").convert("RGBA") for k in ("gpu", "wafer", "figures")}
banner = Image.open(f"{D}/banner.png").convert("RGBA")
logo = Image.open(f"{D}/logo300.png").convert("RGBA")

ease_out = lambda x: 1 - (1 - max(0, min(1, x))) ** 3
def back_out(x):
    x = max(0, min(1, x)); c = 1.70158
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2

def paper_tex(img):
    rng = np.random.default_rng(3); a = np.asarray(img).astype(np.int16)
    n = rng.normal(0, 6, a.shape[:2])[..., None]
    return Image.fromarray(np.clip(a + n, 0, 255).astype(np.uint8))

def make_bg(th, idx):
    col = th["bg"][idx % len(th["bg"])]
    im = Image.new("RGB", (W, H), hexc(col)[:3])
    if th.get("paper"): im = paper_tex(im)
    d = ImageDraw.Draw(im)
    if th.get("grid"):
        for x in range(0, W, 60): d.line([(x, 0), (x, H)], fill=(18, 40, 30))
        for y in range(0, H, 60): d.line([(0, y), (W, y)], fill=(18, 40, 30))
    if th.get("bars"):
        d.rectangle([0, 300, W, 312], fill=hexc(th["acc"])[:3]); d.rectangle([0, 1240, W, 1252], fill=hexc(th["acc"])[:3])
    return im

def tint(sil, colhex, op, angle=0, scale=1.0, dx=0, dy=0):
    s = sil
    if angle or scale != 1.0:
        s = s.rotate(angle, resample=Image.BICUBIC, center=(540, 700)) if angle else s
        if scale != 1.0:
            nw, nh = int(s.width * scale), int(s.height * scale); s2 = s.resize((nw, nh), Image.BICUBIC)
            c = Image.new("RGBA", s.size, (0, 0, 0, 0)); c.alpha_composite(s2, ((s.width - nw) // 2, (s.height - nh) // 2)); s = c
    a = s.getchannel("A").point(lambda v: int(v * op))
    out = Image.new("RGBA", s.size, hexc(colhex)); out.putalpha(a)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); lay.alpha_composite(out, (int(dx), int(dy))); return lay

def text_w(f, s): return f.getlength(s)

def draw_center(d, y, s, f, fill, stroke=0, sfill=None, x=None):
    w = text_w(f, s); xx = (W - w) / 2 if x is None else x
    d.text((xx, y), s, font=f, fill=fill, stroke_width=stroke, stroke_fill=sfill)
    return w

def caption(th, s, t_in, t):
    """Return an RGBA layer with the caption drawn just above the banner."""
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    fname, wg = th["cap"]; size = 84 if fname not in ("anton", "oswald") else 104
    f = F(fname, size, wg)
    words = s.split(" "); toks = []; hl = False
    for w in words:
        if w.startswith("*"): hl = True
        toks.append((w.replace("*", ""), hl))
        if w.endswith("*"): hl = False
    sp = text_w(f, " "); total = sum(text_w(f, w) for w, _ in toks) + sp * (len(toks) - 1)
    if total > 980:   # shrink to fit one line
        f = F(fname, int(size * 980 / total), wg); sp = text_w(f, " "); total = sum(text_w(f, w) for w, _ in toks) + sp * (len(toks) - 1)
    x = (W - total) / 2; y = 1500 - f.size
    age = t - t_in
    for i, (w, h) in enumerate(toks):
        ww = text_w(f, w)
        style = th["capstyle"]
        if style == "pop":
            k = back_out((age - i * 0.14) / 0.28)
            if k <= 0: x += ww + sp; continue
            wl = Image.new("RGBA", (int(ww + 40), int(f.size * 1.6)), (0, 0, 0, 0)); wd = ImageDraw.Draw(wl)
            wd.text((20, 10), w, font=f, fill=hexc(th["acc"]) if h else (255, 255, 255, 255), stroke_width=7, stroke_fill=(0, 0, 0, 255))
            sc = max(0.05, k); nw, nh = max(1, int(wl.width * sc)), max(1, int(wl.height * sc)); wl2 = wl.resize((nw, nh), Image.BICUBIC)
            lay.alpha_composite(wl2, (int(x + ww / 2 + 20 - nw / 2 - 20), int(y + 10 + f.size * 0.8 - nh / 2 - 10)))
        elif style == "box":
            if h:
                d.rounded_rectangle([x - 12, y + f.size * 0.08, x + ww + 12, y + f.size * 1.18], radius=10, fill=hexc(th["acc"]))
                d.text((x, y), w, font=f, fill=(20, 20, 20, 255))
            else:
                d.text((x, y), w, font=f, fill=(255, 255, 255, 255), stroke_width=3, stroke_fill=(0, 0, 0, 200))
        elif style == "marker":
            if h: d.rectangle([x - 8, y + f.size * 0.55, x + ww + 8, y + f.size * 1.12], fill=(253, 224, 71, 255))
            d.text((x, y), w, font=f, fill=hexc(th["fg"]))
        elif style == "mono":
            d.text((x, y), w, font=f, fill=hexc(th["acc"]) if h else hexc(th["fg"]))
            if h: d.line([(x, y + f.size * 1.2), (x + ww, y + f.size * 1.2)], fill=hexc(th["acc"]), width=5)
        else:   # outline
            d.text((x + 4, y + 6), w, font=f, fill=(0, 0, 0, 140))
            d.text((x, y), w, font=f, fill=hexc(th["acc"]) if h else (255, 255, 255, 255), stroke_width=7, stroke_fill=(0, 0, 0, 255))
        x += ww + sp
    if th["capstyle"] != "pop":
        al = min(1.0, age / 0.12)
        if al < 1: lay.putalpha(lay.getchannel("A").point(lambda v: int(v * al)))
    return lay

def headline(th, name, t0, t, d, lay):
    fname, wg = th["head"]; fg = hexc(th["fg"]); acc = hexc(th["acc"]); acc2 = hexc(th["acc2"])
    age = t - t0; giant = th.get("giant")
    if name == "intro":
        k = ease_out(age / 0.6); f = F(fname, 120 if not giant else 170, wg); f2 = F(fname, 92 if not giant else 130, wg)
        dy = (1 - k) * 60; a = int(255 * k)
        draw_center(d, 420 + dy, "Jensen Huang", f, fg[:3] + (a,))
        draw_center(d, 560 + dy, "& Nvidia", f, fg[:3] + (a,))
        k2 = ease_out((age - 0.5) / 0.5)
        draw_center(d, 740 + (1 - k2) * 40, "dalam 40 saat", f2, acc[:3] + (int(255 * k2),))
    elif name == "y1963":
        f = F(fname, 300 if not giant else 420, wg); n = min(4, int(age / 0.14) + 1); s = "1963"[:n]
        full = text_w(f, "1963"); d.text(((W - full) / 2, 360 if not giant else 330), s, font=f, fill=acc)
        k = ease_out((age - 0.6) / 0.4); fs = F("inter", 50, 600)
        draw_center(d, 760 if not giant else 860, "Lahir di Taiwan", fs, fg[:3] + (int(255 * k),))
    elif name == "p90":
        k = ease_out(age / 1.4); v = int(round(90 * k)); f = F(fname, 260 if not giant else 380, wg)
        s = f"~{v}%"; draw_center(d, 360 if not giant else 330, s, f, acc)
        if not giant:   # ring chart filling up
            cx, cy, r = 540, 1010, 150
            d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=fg[:3] + (70,), width=26)
            if k > 0: d.arc([cx - r, cy - r, cx + r, cy + r], start=-90, end=-90 + 360 * 0.9 * k, fill=acc, width=26)
        fs = F("inter", 46, 600); draw_center(d, 690 if not giant else 800, "pasaran cip AI dunia", fs, fg)
        fsrc = F("inter", 26, 500); d.text((W - 360, 1625 - 250 - 36), "Anggaran 2024 · Fortune", font=fsrc, fill=fg[:3] + (150,))
    elif name == "dakwaan":
        f = F(fname, 150 if not giant else 210, wg); st = Image.new("RGBA", (900, 330), (0, 0, 0, 0)); sd = ImageDraw.Draw(st)
        tw = text_w(f, "DAKWAAN"); sd.rounded_rectangle([450 - tw / 2 - 40, 40, 450 + tw / 2 + 40, 40 + f.size * 1.25], radius=18, outline=acc2, width=14)
        sd.text((450 - tw / 2, 40 + f.size * 0.05), "DAKWAAN", font=f, fill=acc2)
        st = st.rotate(6, resample=Image.BICUBIC, expand=True)
        p = min(1, age / 0.25); sc = 2.2 - 1.2 * (p ** 2)
        shake = (random.Random(int(t * 100)).randint(-9, 9) if 0.25 <= age < 0.45 else 0)
        nw, nh = int(st.width * sc), int(st.height * sc); s2 = st.resize((nw, nh), Image.BICUBIC)
        if p < 1: s2.putalpha(s2.getchannel("A").point(lambda v: int(v * p)))
        lay.alpha_composite(s2, (int(540 - nw / 2 + shake), int(470 - nh / 2 + shake)))
        k = ease_out((age - 0.5) / 0.4); fs = F("inter", 40, 500)
        draw_center(d, 1215, "Tiada pertuduhan jenayah dilaporkan", fs, fg[:3] + (int(230 * k),))
    elif name == "end":
        k = back_out(age / 0.5); sz = max(1, int(300 * k)); lg = logo.resize((sz, sz), Image.BICUBIC)
        bgc = Image.new("RGBA", (sz, sz), (0, 0, 0, 0)); ImageDraw.Draw(bgc).ellipse([0, 0, sz - 1, sz - 1], fill=(247, 241, 232, 255)); bgc.alpha_composite(lg)
        lay.alpha_composite(bgc, (540 - sz // 2, 520 - sz // 2))
        f = F(fname, 96, wg); draw_center(d, 720, "Kafe Lembaran", f, fg)
        f2 = F("inter", 66, 800); draw_center(d, 860, "kafelembaran.com", f2, acc)

def clock(th, t, d):
    f = F("mono", 64); sec = max(0.0, t - CLOCK0); ended = t >= SC[-1][1]
    s = f"00:{int(sec):02d}:{int((sec % 1) * 100):02d}"
    col = hexc(th["acc"]) if ended else (hexc(th["clock"]) if t >= CLOCK0 else hexc(th["clock"], 110))
    draw_center(d, 96, s, f, col)
    ft = F("inter", 34, 700); draw_center(d, 185, "Antara dua hirupan kopi", ft, hexc(th["fg"], 210))

def render(n):
    th = THEMES[n]; random.seed(n)
    bgs = [make_bg(th, i) for i in range(len(SC))]
    out = f"{D}/sample{n}-{th['name']}.mp4"; silent = f"{D}/s{n}.mp4"
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", silent], stdin=subprocess.PIPE)
    N = int(TOTAL * FPS)
    def scene_frame(i, t):
        name, s0, s1 = SC[i]; p = (t - s0) / (s1 - s0)
        z = 1 + 0.03 * p
        bg = bgs[i] if th.get("paper") or th.get("grid") or th.get("bars") else bgs[i]
        fr = bg.convert("RGBA")
        sk = SIL[name]
        if sk and th["sil"] > 0:
            ang = (t - s0) * 6 if sk == "wafer" else 0
            dx = (-40 * p if th.get("parallax") else 0)
            fr.alpha_composite(tint(sil_img[sk], th["fg"], th["sil"], angle=ang, scale=z, dx=dx))
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dd = ImageDraw.Draw(lay)
        headline(th, name, s0, t, dd, lay)
        if th.get("parallax"):
            lay2 = Image.new("RGBA", (W, H), (0, 0, 0, 0)); lay2.alpha_composite(lay, (int(20 * p), 0)); lay = lay2
        fr.alpha_composite(lay)
        fr.alpha_composite(caption(th, CAPS[name], s0 + 0.15, t))
        return fr
    for fi in range(N):
        t = fi / FPS
        i = next(k for k, (nm, a, b) in enumerate(SC) if a <= t < b or k == len(SC) - 1)
        fr = scene_frame(i, t)
        # transitions into scene i
        tin = t - SC[i][1]
        if i > 0 and tin < 0.3 and th["trans"] != "cut":
            prev = scene_frame(i - 1, t); k = ease_out(tin / 0.3)
            if th["trans"] == "fade":
                fr = Image.blend(prev, fr, k)
            else:   # slide: new scene pushes in from the right
                c = Image.new("RGBA", (W, H)); off = int(W * (1 - k)); c.alpha_composite(prev, (off - W, 0)); c.alpha_composite(fr, (off, 0)); fr = c
        dc = ImageDraw.Draw(fr); clock(th, t, dc)
        fr.alpha_composite(banner)
        ff.stdin.write(fr.convert("RGB").tobytes())
    ff.stdin.close(); ff.wait()
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-i", f"{D}/audio.wav", "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
                    "-shortest", "-movflags", "+faststart", out], check=True)
    print("done", out)

if __name__ == "__main__":
    for a in sys.argv[1:]: render(int(a))
