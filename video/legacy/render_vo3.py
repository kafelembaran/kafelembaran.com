"""Kejatuhan Jensen Huang: voiceover version. Scenes and subtitles follow the AI Studio voice; kopitiam chatter bed;
call + 'ahh' before the voice, 'ting' at the closing."""
import subprocess, sys, wave
sys.argv = [sys.argv[0]]
SRC = open('/home/claude/samples/render_samples.py').read().split('if __name__ == "__main__":')[0]
exec(SRC)
th = THEMES[1]; FG = hexc(th["fg"]); GOLD = hexc(th["acc"]); ORANGE = hexc(th["acc2"])
exec(open("/home/claude/samples/cards.py").read())
sil_img.update({k: Image.open(f"{D}/sil_{k}.png").convert("RGBA") for k in ("factory", "cup")})
OFF = 2.6                                  # voice starts after 'Bang, order bang!' + 'ahh'
VO = "/home/claude/vo/enzo.wav"; VO_LEN = 75.48
SCN_T = [5.5, 10.6, 14.2, 22.1, 28.1, 32.9, 40.9, 46.0, 50.0, 55.4, 60.7, 67.0]   # voice time
OUT_T = 70.5
TOTAL = OFF + VO_LEN + 1.2
BEATS = [
 ("big",   "Jensen Huang", ["Pengasas Nvidia, 1993"], "gpu", ""),
 ("type",  "1963", ["Lahir di Taiwan"], "wafer", ""),
 ("big",   "GPU", ["Ribuan kiraan serentak"], "gpu", ""),
 ("count", "90", ["pasaran cip AI dunia"], None, "Anggaran · Fortune"),
 ("big",   "8 NOV", ["Lembaga Nvidia buka siasatan"], "figures", "AI Business, AP"),
 ("stamp", "DAKWAAN", ["(China & Megaspeed menafikan)"], None, "NBC, CBS"),
 ("big",   "12 NOV", ["Huang letak jawatan"], None, "Nvidia 8-K (SEC)"),
 ("count", "33", ["tahun sebagai CEO"], None, "Al Jazeera"),
 ("big",   "Kenapa?", ["Cip AI = minyak abad ke-21"], "factory", ""),
 ("type",  "2022", ["Amerika sekat cip AI ke China"], "wafer", ""),
 ("count", "13", ["pemasangan & ujian cip dunia"], "factory", "MIDA"),
 ("big",   "Kita?", ["Bila gergasi bergaduh"], "cup", ""),
]
SUBS = [(5.77, "Jensen Huang. Pengasas Nvidia, tahun 1993."), (10.86, "Lahir di Taiwan, tahun 1963."),
 (14.52, "Nvidia buat cip GPU... cip yang boleh buat ribuan kiraan serentak."), (19.79, "Itulah enjin di sebalik AI."),
 (22.45, "Hari ini, Nvidia kuasai hampir 90% pasaran cip AI dunia."), (28.45, "Tapi pada 8 November, lembaga Nvidia buka siasatan."),
 (33.23, "Huang *didakwa* rapat dengan seorang wanita yang disyaki perisik China."), (38.03, "China dan syarikat wanita itu menafikan."),
 (41.21, "Empat hari kemudian, 12 November... Huang letak jawatan."), (46.32, "33 tahun sebagai CEO, berakhir."),
 (50.24, "Kenapa ini penting? Sebab cip AI ialah minyak abad ke-21."), (55.76, "Sejak 2022, Amerika sekat eksport cip AI canggih ke China."),
 (60.96, "Dan Malaysia? Kita kendalikan 13% pemasangan dan ujian cip dunia."), (67.25, "Bila gergasi bergaduh... kita di tengah.")]
SUB_END = 70.2

# ---------- intro and outro frame functions from the templates (own namespaces) ----------
def load_ns(path, argv, repl):
    src = open(path).read().split("\nsilent = ")[0]
    for a, b in repl: src = src.replace(a, b)
    ns = {"__name__": "tpl"}; old = sys.argv; sys.argv = [path] + argv; exec(src, ns); sys.argv = old; return ns
INTRO_LEN = OFF + SCN_T[0]
intro = load_ns(f"{D}/intro_template.py", ["Kejatuhan", "Jensen Huang"],
                [("TOTAL = 4.2", f"TOTAL = {INTRO_LEN}"), ("(t - 1.5)", f"(t - {OFF + 0.27})"), ("(t - 2.1)", f"(t - {OFF + 2.40})")])
OUTRO_LEN = TOTAL - (OFF + OUT_T)
CLK_SPAN = OUT_T - SCN_T[0]
def clk_str(sec): return f"{int(sec // 60):02d}:{int(sec % 60):02d}:{int((sec % 1) * 100):02d}"
outro = load_ns(f"{D}/outro_template.py", ["ADIKUASA", "Ayman Rashdan Wong", clk_str(CLK_SPAN)], [("TOTAL = 4.6", f"TOTAL = {OUTRO_LEN}")])

# ---------- middle scenes ----------
def head(kind, big, subs, age, d, lay):
    fh = F("lora", 230, 700)
    if kind == "type":
        n = min(len(big), int(age / 0.14) + 1); full = text_w(fh, big); d.text(((W - full) / 2, 360), big[:n], font=fh, fill=GOLD); y = 680
    elif kind == "count":
        k = ease_out(age / 1.4); v = int(round(int(big) * k)); draw_center(d, 360, (f"{v}%" if big == "13" else f"~{v}%" if big == "90" else str(v)), fh, GOLD); y = 680
    elif kind == "ring":
        k = ease_out(age / 1.6); draw_center(d, 330, f"~{int(round(90 * k))}%", F("lora", 210, 700), GOLD)
        cx, cy, r = 540, 1000, 140
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=FG[:3] + (70,), width=26)
        if k > 0: d.arc([cx - r, cy - r, cx + r, cy + r], start=-90, end=-90 + 324 * k, fill=GOLD, width=26)
        y = 620
    elif kind == "stamp":
        f = F("lora", 140, 700); st = Image.new("RGBA", (900, 320), (0, 0, 0, 0)); sd = ImageDraw.Draw(st); tw = text_w(f, big)
        sd.rounded_rectangle([450 - tw / 2 - 40, 40, 450 + tw / 2 + 40, 40 + f.size * 1.25], radius=18, outline=ORANGE, width=14)
        sd.text((450 - tw / 2, 40 + f.size * 0.05), big, font=f, fill=ORANGE); st = st.rotate(6, resample=Image.BICUBIC, expand=True)
        p = min(1, age / 0.25); sc = 2.2 - 1.2 * p ** 2; sh = random.Random(int(age * 100)).randint(-9, 9) if 0.25 <= age < 0.45 else 0
        nw, nh = int(st.width * sc), int(st.height * sc); s2 = st.resize((nw, nh), Image.BICUBIC)
        if p < 1: s2.putalpha(s2.getchannel("A").point(lambda v: int(v * p)))
        lay.alpha_composite(s2, (int(540 - nw / 2 + sh), int(470 - nh / 2 + sh))); y = 680
    else:
        size = 170 if len(big) <= 7 else 120; k = ease_out(age / 0.5)
        draw_center(d, 400 + (1 - k) * 50, big, F("lora", size, 700), GOLD[:3] + (int(255 * k),)); y = 400 + size * 1.35
    for j, s in enumerate(subs):
        k = ease_out((age - 0.45 - j * 0.18) / 0.4); small = s.startswith("(")
        draw_center(d, y + j * 72 + (1 - k) * 20, s, F("inter", 40 if small else 52, 500 if small else 600), FG[:3] + (int((180 if small else 255) * k),))

bgs = [make_bg(th, i).convert("RGBA") for i in range(2)]
def scene(i, tv):
    kind, big, subs, sk, src = BEATS[i]; age = tv - SCN_T[i]; dur = (SCN_T[i + 1] if i + 1 < len(SCN_T) else OUT_T) - SCN_T[i]; p = age / dur
    fr = bgs[i % 2].copy()
    ck = ease_out(age / 0.45); cimg = card(i, age, dur)
    if ck < 1: cimg.putalpha(cimg.getchannel("A").point(lambda v: int(v * ck)))
    fr.alpha_composite(cimg, (CX0, int(CY0 + (1 - ck) * 30)))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); head(kind, big, subs, age, d, lay); fr.alpha_composite(lay)
    if src:
        d2 = ImageDraw.Draw(fr); f = F("inter", 28, 500); s = "Sumber: " + src; d2.text((W - 60 - text_w(f, s), 1342), s, font=f, fill=FG[:3] + (160,))
    return fr

def wrap(words, f, maxw):
    lines, cur = [], []
    for w in words:
        test = cur + [w]
        if cur and sum(text_w(f, x[0]) for x in test) + text_w(f, " ") * (len(test) - 1) > maxw: lines.append(cur); cur = [w]
        else: cur = test
    if cur: lines.append(cur)
    return lines
def subtitle(fr, tv):
    idx = [k for k, (s, _) in enumerate(SUBS) if s - 0.1 <= tv]
    if not idx or tv > SUB_END: return
    k = idx[-1]; s0, txt = SUBS[k]; age = tv - (s0 - 0.1); a = ease_out(age / 0.2)
    f = F("poppins", 60); toks = []; hl = False
    for w in txt.split():
        if w.startswith("*"): hl = True
        toks.append((w.replace("*", ""), hl))
        if w.endswith("*") or w.endswith("*,") or w.endswith("*."): hl = False
    lines = wrap(toks, f, 960); lh = 84; y0 = 1625 - lh * len(lines)
    d = ImageDraw.Draw(fr); sp = text_w(f, " ")
    for j, ln in enumerate(lines):
        tw = sum(text_w(f, w) for w, _ in ln) + sp * (len(ln) - 1); x = (W - tw) / 2
        for w, h in ln:
            d.text((x, y0 + j * lh + (1 - a) * 12), w, font=f, fill=(GOLD if h else (255, 255, 255, 255))[:3] + (int(255 * a),),
                   stroke_width=7, stroke_fill=(0, 0, 0, int(230 * a)))
            x += text_w(f, w) + sp

def clock(fr, tv):
    d = ImageDraw.Draw(fr)
    draw_center(d, 96, clk_str(max(0, tv - SCN_T[0])), F("mono", 64), hexc(th["clock"]))
    draw_center(d, 185, "Antara dua hirupan kopi", F("inter", 34, 700), FG[:3] + (210,))

def frame(t):
    tv = t - OFF
    if tv < SCN_T[0]: return intro["frame"](t)
    if tv >= OUT_T:
        fr = outro["frame"](tv - OUT_T)
        if tv - OUT_T < 0.3: fr = Image.blend(mid_frame(OUT_T - 0.001), fr, ease_out((tv - OUT_T) / 0.3))
        return fr
    fr = mid_frame(tv)
    if tv - SCN_T[0] < 0.3: fr = Image.blend(intro["frame"](INTRO_LEN - 0.001).convert("RGBA"), fr, ease_out((tv - SCN_T[0]) / 0.3))
    return fr
def mid_frame(tv):
    i = max(k for k in range(len(SCN_T)) if SCN_T[k] <= tv); fr = scene(i, tv); tin = tv - SCN_T[i]
    if i > 0 and tin < 0.3: fr = Image.blend(scene(i - 1, tv), fr, ease_out(tin / 0.3))
    clock(fr, tv); subtitle(fr, tv); fr.alpha_composite(banner); return fr

silent = f"{D}/vo_silent.mp4"
ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                       "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", silent], stdin=subprocess.PIPE)
NF = int(TOTAL * FPS)
for fi in range(NF): ff.stdin.write(frame(fi / FPS).convert("RGB").tobytes())
ff.stdin.close(); ff.wait()

# ---------- audio ----------
sr = 44100; n = int(TOTAL * sr); tt = np.arange(n) / sr
def load(p):
    q = wave.open(p); a = np.frombuffer(q.readframes(q.getnframes()), np.int16) / 32768
    return a.reshape(-1, q.getnchannels()) if q.getnchannels() == 2 else np.repeat(a[:, None], 2, axis=1)
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", VO, "-ar", "44100", "-ac", "2", "/home/claude/vo/enzo44.wav"], check=True)
vo = load("/home/claude/vo/enzo44.wav")
G2 = "/home/claude/gem2"
c2 = load(f"{G2}/c2.wav")[int(0.3 * sr):int(9.9 * sr)]; c3 = load(f"{G2}/c3.wav")[int(0.3 * sr):int(9.9 * sr)]
def chain(order, skip):
    out = np.zeros((n + sr * 12, 2)); pos = 0; xf = int(1.2 * sr); r = np.linspace(0, 1, xf)[:, None]; i = 0
    while pos < n:
        s = order[i % len(order)].copy()
        if i == 0: s = s[int(skip * sr):]
        s[-xf:] *= r[::-1]
        if i > 0: s[:xf] *= r
        out[pos:pos + len(s)] += s; pos += len(s) - xf; i += 1
    return out[:n]
bed = chain([c2, c3], 0.0) * 0.8 + chain([c3, c2], 4.7)[:, ::-1] * 0.5
env = np.where(tt < OFF - 0.2, 0.85, 0.32) * np.clip(tt / 0.4, 0, 1) * np.clip((TOTAL - tt) / 2, 0, 1)
k_ = int(0.3 * sr); cs = np.cumsum(np.concatenate([np.full(k_, env[0]), env, np.full(k_, env[-1])])); env = ((cs[2 * k_:] - cs[:-2 * k_]) / (2 * k_))[:n]
mix = bed * env[:, None]
def put(x, at, g):
    s = int(at * sr); e = min(n, s + len(x)); mix[s:e] += x[:e - s] * g
put(load(f"{G2}/shout.wav"), 0.0, 1.2); put(load("/home/claude/gem/c1_ahhA.wav"), 1.25, 1.0)
put(vo, OFF, 1.6)
put(load("/home/claude/gem/c2_clinkA.wav"), OFF + OUT_T + 0.55 - 0.143, 1.1)
tk = np.arange(int(0.03 * sr)) / sr; click = np.repeat((np.sin(2 * np.pi * 1800 * tk) * np.exp(-tk * 180) * 0.025)[:, None], 2, axis=1)
for s_ in range(int(CLK_SPAN) + 1): put(click, OFF + SCN_T[0] + s_, 1.0)
mix *= 0.9 / np.abs(mix).max()
pcm = (mix * 32767).astype(np.int16); w = wave.open(f"{D}/vo_mix.wav", "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes(pcm.tobytes()); w.close()
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-i", f"{D}/vo_mix.wav", "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                "-af", "loudnorm=I=-14:TP=-1.5", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", f"{D}/kejatuhan-jensen-huang-enzo-v2.mp4"], check=True)
print("done", TOTAL, clk_str(CLK_SPAN))
