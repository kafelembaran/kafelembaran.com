import sys, math, numpy as np, subprocess
sys.path.insert(0, "/home/claude/kafelembaran.com/video")
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import kl
from kl import W, H, F, text_w
kl.FONT["anton"] = "Anton.ttf"
GREEN = (22, 84, 80, 255); MARBLE = (236, 232, 225, 255); CHIT = (243, 230, 181, 255); RED = (184, 50, 43, 255); KOPI = (59, 38, 24, 255); CREAM = (247, 241, 232, 255)
rng = np.random.default_rng(3)

def marble(w, h):
    y, x = np.mgrid[0:h, 0:w] / 260.0
    n = sum(np.sin(x * f + 1.7 * np.sin(y * f * 0.7 + k) + k * 2) / f for k, f in enumerate([1.0, 2.3, 4.9, 9.7]))
    v = np.abs(np.sin(n * 3.0 + x * 0.9)) ** 0.12
    base = np.array(MARBLE[:3], float); vein = np.array([150, 150, 148], float)
    a = (1 - v)[..., None] * 0.38 + rng.normal(0, 0.012, (h, w, 1))
    img = base * (1 - a) + vein * a
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert("RGBA")

def tiles(w, h):
    im = Image.new("RGBA", (w, h), GREEN); d = ImageDraw.Draw(im)
    for x in range(0, w, 90): d.line([(x, 0), (x, h)], fill=(18, 74, 70, 255), width=3)
    for y in range(0, h, 90): d.line([(0, y), (w, y)], fill=(18, 74, 70, 255), width=3)
    return im

def chit(lines, w=None, rot=-2.5, maxw=960):
    def fit(txt, size, font):
        while text_w(F(font, size, 600 if font == "inter" else None), txt) > maxw - 150 and size > 20: size -= 4
        return size
    lines = [(t, fit(t, sz, fn), fn, c) for t, sz, fn, c in lines]
    def lh(t, sz, fn):
        b = F(fn, sz, 600 if fn == "inter" else None).getbbox(t); return b[3] - min(b[1], 0) + (18 if fn == "anton" else 14)
    tw = max(text_w(F(fn, sz, 600 if fn == "inter" else None), t) for t, sz, fn, c in lines)
    w = w or int(min(maxw, tw + 150)); hgt = 46 + sum(lh(*l[:3]) for l in lines) + 20
    im = Image.new("RGBA", (w, int(hgt) + 30), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    pts = [(0, 0), (w, 0), (w, hgt)] + [(w - i * 20, hgt + (10 if i % 2 else 0)) for i in range(w // 20 + 1)] + [(0, hgt)]
    d.polygon(pts, fill=CHIT)
    for y in range(60, int(hgt) - 10, 44): d.line([(24, y), (w - 24, y)], fill=(170, 190, 215, 120), width=2)
    d.line([(70, 0), (70, hgt)], fill=(210, 120, 120, 150), width=2)
    y = 36
    for txt, size, font, col in lines:
        f = F(font, size, 600 if font == "inter" else None); b = f.getbbox(txt)
        d.text((96, y - b[1]), txt, font=f, fill=col); y += lh(txt, size, font)
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); sh.putalpha(im.getchannel("A").point(lambda v: v // 3)); sh = sh.filter(ImageFilter.GaussianBlur(8))
    out = Image.new("RGBA", (im.width + 30, im.height + 30), (0, 0, 0, 0)); out.alpha_composite(sh, (14, 16)); out.alpha_composite(im, (0, 0))
    return out.rotate(rot, resample=Image.BICUBIC, expand=True)

def banner():
    b = Image.new("RGBA", (W, 256), CREAM); d = ImageDraw.Draw(b)
    logo = kl.asset("logo300.png").resize((150, 150)); b.alpha_composite(logo, (60, 53))
    d.text((240, 70), "Kafe Lembaran", font=F("lora", 64, 700), fill=GREEN)
    d.text((242, 160), "kafelembaran.com   @kafe.lembaran", font=F("inter", 34, 500), fill=(60, 90, 86, 255))
    return b
BAN = banner()

def clock(d, s):
    cx, cy, r = 112, 120, 52
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=CREAM, outline=KOPI, width=5)
    a = -math.pi / 2 + 2 * math.pi * (s % 60) / 60
    d.line([(cx, cy), (cx + 40 * math.cos(a), cy + 40 * math.sin(a))], fill=RED, width=5); d.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=KOPI)
    d.text((190, 78), f"{int(s // 60)}:{int(s % 60):02d}", font=F("anton", 64), fill=CREAM)
    d.text((192, 152), "antara dua hirupan kopi", font=F("inter", 30, 500), fill=(220, 230, 225, 255))

def table(img):
    t = marble(W, 760); t.alpha_composite(img.resize((W - 120, int((W - 120) * img.height / img.width))), (60, 60)); return t

def subtitle(d, txt, y=1530):
    f = F("inter", 54, 700); words = txt.split(); rows = []; cur = ""
    for w_ in words:
        if cur and text_w(f, cur + " " + w_) > 940: rows.append(cur); cur = w_
        else: cur = (cur + " " + w_).strip()
    rows.append(cur); y0 = 1640 - 70 * len(rows)
    for j, r in enumerate(rows): d.text((70, y0 + j * 70), r, font=f, fill=(255, 255, 255, 255), stroke_width=6, stroke_fill=(20, 30, 28, 255))

def frame_scene(footage, num, sub, src, say, clk, stamp=None):
    fr = tiles(W, H); fr.alpha_composite(table(footage), (0, 640))
    d = ImageDraw.Draw(fr); clock(d, clk)
    lines = [(num, 190, "anton", RED), (sub, 46, "inter", KOPI)]
    c = chit(lines); fr.alpha_composite(c, (40, 250))
    if stamp:
        st = Image.new("RGBA", (520, 170), (0, 0, 0, 0)); sd = ImageDraw.Draw(st)
        sd.rounded_rectangle([6, 6, 514, 164], radius=10, outline=RED, width=10); sd.text((260, 86), stamp, font=F("anton", 110), fill=RED, anchor="mm")
        st = st.rotate(8, expand=True, resample=Image.BICUBIC); fr.alpha_composite(st, (480, 300))
    if src: d.text((W - 60, 1280), "Sumber: " + src, font=F("inter", 30, 600), fill=KOPI, anchor="ra")
    fr.alpha_composite(Image.new("RGBA", (W, 330), (0, 0, 0, 0)), (0, 1400))
    sh = Image.new("RGBA", (W, 330), (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
    for y in range(330): sd.line([(0, y), (W, y)], fill=(10, 25, 23, int(170 * y / 330)))
    fr.alpha_composite(sh, (0, 1334)); subtitle(ImageDraw.Draw(fr), say)
    fr.alpha_composite(BAN, (0, H - 256)); return fr

def grab(path, t):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(t), "-i", path, "-frames:v", "1", "/tmp/g.png"]); return Image.open("/tmp/g.png").convert("RGBA")

E = "/home/claude/kafelembaran.com/episodes/2026-11-16-kejatuhan-jensen-huang/clips/"
f1 = frame_scene(grab(E + "servers.mp4", 3), "~90%", "pasaran cip AI dunia", "Fortune (anggaran)", "Hari ini, Nvidia kuasai hampir 90% pasaran cip AI dunia.", 18)
f2 = frame_scene(grab(E + "meeting.mp4", 3), "8 Nov", "Lembaga Nvidia buka siasatan", "AI Business, AP", "Tapi pada 8 November, lembaga Nvidia buka siasatan.", 24)
f3 = frame_scene(grab(E + "taipei-1963.mp4", 3), "1963", "Lahir di Taiwan", None, "Lahir di Taiwan, tahun 1963.", 6)

# opening
op = tiles(W, H); d = ImageDraw.Draw(op)
op.alpha_composite(marble(W, 700), (0, 1220))
cup = kl.cup_img(400, GREEN); op.alpha_composite(cup, (340, 1300))
c = chit([("Kejatuhan", 150, "anton", RED), ("Jensen Huang", 150, "anton", KOPI), ("Dua hirupan kopi, episod 1", 40, "inter", KOPI)], rot=-3)
op.alpha_composite(c, (60, 230))
d = ImageDraw.Draw(op); d.text((70, 990), "“Biar saya terangkan isu ini…", font=F("lora", 58, 500), fill=CREAM)
d.text((70, 1070), "di antara dua hirupan kopi.”", font=F("lora", 58, 500), fill=CREAM)
op.alpha_composite(BAN, (0, H - 256))
# closing
cl = tiles(W, H); cl.alpha_composite(marble(W, 1100), (0, 560)); d = ImageDraw.Draw(cl); clock(d, 65)
cl.alpha_composite(kl.cup_img(260, GREEN), (760, 1080))
c = chit([("Baca buku ini", 46, "inter", KOPI), ("ADIKUASA", 150, "anton", RED), ("Ayman Rashdan Wong", 44, "inter", KOPI), ("Link buku kat bio", 54, "inter", RED)], rot=2)
cl.alpha_composite(c, (60, 330)); d = ImageDraw.Draw(cl)
d.text((70, 1300), "kafelembaran.com", font=F("inter", 50, 800), fill=KOPI); d.text((70, 1370), "@kafe.lembaran di TikTok, YouTube dan Instagram", font=F("inter", 32, 500), fill=(70, 60, 50, 255))
cl.alpha_composite(BAN, (0, H - 256))
sheet = Image.new("RGB", (540 * 5, 960))
for i, im in enumerate([op, f3, f1, f2, cl]): sheet.paste(im.convert("RGB").resize((540, 960)), (i * 540, 0))
sheet.save("/home/claude/v2/mock.png"); print("ok")
