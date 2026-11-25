"""Kafe Lembaran episode builder.

  python3 make_episode.py script  <episode_dir>   -> tts_script.txt + gemini_prompts.txt (for the user)
  python3 make_episode.py align   <episode_dir>   -> prints sentence timings found in voice.wav
  python3 make_episode.py render  <episode_dir>   -> out/<slug>.mp4 + out/sheet.png

<episode_dir> holds episode.json, voice.wav (from AI Studio) and clips/ (Gemini footage, optional).
"""
import json, os, re, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kl import (W, H, FPS, HERE, F, FG, GOLD, ORANGE, BANNER, bg, ease_out, text_w, draw_center, fade, clk_str, Intro, Outro)
from panels import Panel, CX0, CY0

CHATTER_TEMPO = 1.0    # chatter playback speed (1.0 = original)
CHATTER_LEVEL = (0.60, 0.22)   # chatter volume before the voice, and under the voice (was 0.85 / 0.32)
OFF = 2.6          # voice starts after "Bang, order bang!" (0.0 s) and sound A (1.25 s)
LEAD = 0.3         # a scene appears this long before its first sentence
# Standard voice style for EVERY episode (fixed 24 Nov 2026). Do not change per episode;
# only add pronunciations through episode.json "say_as": {"Riemann": "Ree-man", ...}.
TTS_STYLE = ("Read in Malaysian Malay, calm and relaxed, like a friend explaining the news over coffee at a kopitiam. "
             "Clear, steady pace of about 140 words per minute. Keep exactly the same speed from the first line to the last; do not slow down towards the end or before numbers. "
             "Short pause at each \"...\". Neutral tone, not dramatic.")
TTS_HEADER = "AI STUDIO: Gemini Flash TTS (Audio tab), Speaker 1 - Enzo, Friendly. Download -> voice.wav"

def tts_style(ep):
    say_as = ep.get("say_as") or {}
    extra = " ".join(f'Say "{k}" as "{v}".' for k, v in say_as.items())
    return TTS_STYLE + (" " + extra if extra else "")

def load(ep_dir):
    with open(os.path.join(ep_dir, "episode.json")) as f: return json.load(f)

def units(ep):
    """Ordered spoken units: (scene index | 'intro' | 'outro', say, show)."""
    u = [("intro", ep["intro_say"], ep["intro_say"])]
    for i, sc in enumerate(ep["scenes"]):
        for s in sc["say"]:
            s = {"say": s} if isinstance(s, str) else s
            u.append((i, s["say"], s.get("show", s["say"])))
    u.append(("outro", ep["outro_say"], ep["outro_say"]))
    return u

# ---------------- 1. script for the user ----------------
def cmd_script(ep_dir):
    ep = load(ep_dir); out = [ep["intro_say"], ""]
    for sc in ep["scenes"]:
        out.append(" ".join(s if isinstance(s, str) else s["say"] for s in sc["say"]))
    out += ["", ep["outro_say"]]
    with open(os.path.join(ep_dir, "tts_script.txt"), "w") as f:
        f.write(TTS_HEADER + "\n")
        f.write(f"STYLE: {tts_style(ep)}\n\n--- paste below ---\n\n" + "\n".join(out) + "\n")
    prompts = [f"[{sc['panel']['file']}]\n{sc['panel']['prompt']}\n" for sc in ep["scenes"] if sc["panel"].get("prompt")]
    with open(os.path.join(ep_dir, "gemini_prompts.txt"), "w") as f:
        f.write("GEMINI VIDEO (Veo). Optional: missing clips fall back to text panels. Save each as clips/<name>.mp4\n\n" + "\n".join(prompts))
    print(open(os.path.join(ep_dir, "tts_script.txt")).read())

# ---------------- 2. align sentences to the voice ----------------
def speech_segments(path):
    r = subprocess.run(["ffmpeg", "-i", path, "-af", "silencedetect=noise=-34dB:d=0.12", "-f", "null", "-"], capture_output=True, text=True).stderr
    st = [float(x) for x in re.findall(r"silence_start: ([0-9.]+)", r)]; en = [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", r)]
    dur = float(re.findall(r"Duration: (\d+):(\d+):([0-9.]+)", r)[0][2]) + 60 * float(re.findall(r"Duration: (\d+):(\d+)", r)[0][1])
    sil = sorted(zip(st, en + [dur] * (len(st) - len(en))))
    segs, t = [], 0.0
    for a, b in sil:
        if a - t > 0.05: segs.append((t, a))
        t = b
    if dur - t > 0.05: segs.append((t, dur))
    return segs, dur

SPOKEN_WORDS = {"UMNO": 2}
def syllables(text):
    """Spoken syllables in Malay text: vowel groups (ai/au/oi = one), acronyms by letter (MCA = 3), digits as words."""
    n = 0
    for tok in re.findall(r"[A-Za-z']+|\d+", text):
        if tok.isdigit(): n += 3 * len(tok)                              # numbers are read out in words
        elif tok.isupper() and len(tok) <= 4: n += SPOKEN_WORDS.get(tok, len(tok))
        else: n += max(1, len(re.findall(r"ai|au|oi|[aeiou]", tok.lower())))
    return n

def align(ep, voice):
    """Word-level forced alignment (msalign: pocketsphinx + Malay phone rules); falls back to the old DP method."""
    U = units(ep); segs, dur = speech_segments(voice)
    try:
        import msalign
        words, owner = [], []
        for k, u in enumerate(U):
            ws = msalign.words_of(u[1]); words += ws; owner += [k] * len(ws)
        wt = msalign.align_words(voice, words)
        if len(wt) != len(words): raise ValueError(f"aligned {len(wt)} of {len(words)} words")
        spans = {}
        for (w, a, b), k in zip(wt, owner): spans.setdefault(k, [a, b]); spans[k][1] = b
        out = []
        for k, u in enumerate(U):
            a, b = spans[k]; ss = [(max(s0, a), min(s1, b)) for s0, s1 in segs if s1 > a and s0 < b] or [(a, b)]
            out.append((u, ss[0][0], ss[-1][1], ss))
        return out, dur
    except Exception as e:
        print("forced alignment unavailable, using DP:", e)
    return align_dp(ep, voice)

def align_dp(ep, voice):
    """Dynamic programming: split the speech segments into len(units) consecutive groups whose lengths best match
    each sentence's character count, preferring to cut at long pauses."""
    U = units(ep); segs, dur = speech_segments(voice); n, m = len(U), len(segs)
    weight = np.array([syllables(u[1]) + 1.0 * u[1].count("...") for u in U], float)
    total = segs[-1][1] - segs[0][0]; exp = total * weight / weight.sum()
    gap_before = [0.0] + [segs[j][0] - segs[j - 1][1] for j in range(1, m)]
    INF = 1e18; dp = np.full((n + 1, m + 1), INF); back = np.zeros((n + 1, m + 1), int); dp[0][0] = 0
    for k in range(1, n + 1):
        for j in range(k, m - (n - k) + 1):
            for i in range(k - 1, j):
                if dp[k - 1][i] >= INF: continue
                span = segs[j - 1][1] - segs[i][0]
                c = 2.0 * np.log(max(span, 0.2) / max(exp[k - 1], 0.4)) ** 2 - (0.8 * gap_before[i] if i > 0 else 0)
                if dp[k - 1][i] + c < dp[k][j]: dp[k][j] = dp[k - 1][i] + c; back[k][j] = i
    cuts, j = [], m
    for k in range(n, 0, -1): i = back[k][j]; cuts.append((i, j)); j = i
    cuts.reverse()
    return [(U[k], segs[i][0], segs[j - 1][1], segs[i:j]) for k, (i, j) in enumerate(cuts)], dur

def cmd_align(ep_dir):
    ep = load(ep_dir); res, dur = align(ep, os.path.join(ep_dir, "voice.wav"))
    for (sc, say, _), a, b, _ in res: print(f"{a:6.2f}-{b:6.2f}  [{sc}]  {say[:70]}")
    print("voice length", dur)

# ---------------- 3. render ----------------
def head(H_, age, d, lay):
    kind = H_["kind"]; fh = F("lora", 230, 700); y = 680
    if kind == "type":
        s = str(H_["text"]); n = min(len(s), int(age / 0.14) + 1); d.text(((W - text_w(fh, s)) / 2, 360), s[:n], font=fh, fill=GOLD)
    elif kind == "count":
        k = ease_out(age / 1.4); v = H_["value"] * k; v = f"{v:.0f}" if float(H_["value"]).is_integer() else f"{v:.1f}"
        draw_center(d, 360, f"{H_.get('prefix', '')}{v}{H_.get('suffix', '')}", fh, GOLD)
    elif kind == "stamp":
        import random
        f = F("lora", 140, 700); st = Image.new("RGBA", (900, 320), (0, 0, 0, 0)); sd = ImageDraw.Draw(st); tw = text_w(f, H_["text"])
        sd.rounded_rectangle([450 - tw / 2 - 40, 40, 450 + tw / 2 + 40, 40 + f.size * 1.25], radius=18, outline=ORANGE, width=14)
        sd.text((450 - tw / 2, 40 + f.size * 0.05), H_["text"], font=f, fill=ORANGE); st = st.rotate(6, resample=Image.BICUBIC, expand=True)
        p = min(1, age / 0.25); sc = 2.2 - 1.2 * p ** 2; sh = random.Random(int(age * 100)).randint(-9, 9) if 0.25 <= age < 0.45 else 0
        nw, nh = int(st.width * sc), int(st.height * sc); s2 = st.resize((nw, nh), Image.BICUBIC)
        if p < 1: s2.putalpha(s2.getchannel("A").point(lambda v: int(v * p)))
        lay.alpha_composite(s2, (int(540 - nw / 2 + sh), int(470 - nh / 2 + sh)))
    else:
        s = H_["text"]; size = 170 if text_w(F("lora", 170, 700), s) < 980 else 120; k = ease_out(age / 0.5)
        draw_center(d, 400 + (1 - k) * 50, s, F("lora", size, 700), fade(GOLD, k)); y = 400 + size * 1.35
    if H_.get("sub"):
        k = ease_out((age - 0.45) / 0.4); small = H_["sub"].startswith("(")
        draw_center(d, y + (1 - k) * 20, H_["sub"], F("inter", 40 if small else 52, 500 if small else 600), fade(FG, (0.7 if small else 1) * k))

def subtitle(fr, txt, age):
    a = ease_out(age / 0.2); f = F("poppins", 60); sp = text_w(f, " "); toks, hl = [], False
    for w in txt.split():
        if w.startswith("*"): hl = True
        toks.append((w.replace("*", ""), hl))
        if "*" in w[1:]: hl = False
    rows, cur = [], []
    for tk in toks:
        if cur and sum(text_w(f, x[0]) for x in cur + [tk]) + sp * len(cur) > 960: rows.append(cur); cur = [tk]
        else: cur.append(tk)
    rows.append(cur); y0 = 1625 - 84 * len(rows); d = ImageDraw.Draw(fr)
    for j, ln in enumerate(rows):
        x = (W - sum(text_w(f, w) for w, _ in ln) - sp * (len(ln) - 1)) / 2
        for w, h in ln:
            d.text((x, y0 + j * 84 + (1 - a) * 12), w, font=f, fill=fade(GOLD if h else (255, 255, 255, 255), a), stroke_width=7, stroke_fill=(0, 0, 0, int(230 * a)))
            x += text_w(f, w) + sp

def cmd_render(ep_dir, nobook=False):
    ep = load(ep_dir); ep["_nobook"] = nobook or not ep.get("book"); cutbook = nobook and bool(ep.get("book")); voice = os.path.join(ep_dir, "voice.wav"); res, vlen = align(ep, voice)
    if ep.get("max_gap") or ep.get("voice_tempo"):     # tighten long pauses and/or speed up slightly (pitch kept), then re-align
        q = wave.open(voice); fr_ = q.getframerate(); ch = q.getnchannels(); sw = q.getsampwidth(); raw = np.frombuffer(q.readframes(q.getnframes()), np.int16).reshape(-1, ch); q.close()
        mg = ep.get("max_gap", 99); keep, last = [], 0
        for k in range(1, len(res)):
            b, a2 = res[k - 1][2], res[k][1]
            if a2 - b > mg:
                cut0 = int((b + mg / 2) * fr_); cut1 = int((a2 - mg / 2) * fr_); keep.append(raw[last:cut0]); last = cut1
        keep.append(raw[last:]); os.makedirs(os.path.join(ep_dir, "out"), exist_ok=True)
        tmpw = os.path.join(ep_dir, "out", "voice_tight_raw.wav"); q = wave.open(tmpw, "wb"); q.setnchannels(ch); q.setsampwidth(sw); q.setframerate(fr_); q.writeframes(np.concatenate(keep).tobytes()); q.close()
        voice = os.path.join(ep_dir, "out", "voice_tight.wav")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmpw, "-af", f"atempo={ep.get('voice_tempo', 1.0)}", voice], check=True)
        res, vlen = align(ep, voice)
    says_ = [({"say": x} if isinstance(x, str) else x) for sc in ep["scenes"] for x in sc["say"]]
    gaps_at = [res[1:-1][k][2] + 0.05 for k, sd in enumerate(says_) if sd.get("sfx_after")]
    if gaps_at:                                         # open a 1.1 s gap in the voice for each sound effect, then re-align
        q = wave.open(voice); fr_ = q.getframerate(); ch = q.getnchannels(); sw = q.getsampwidth(); raw = np.frombuffer(q.readframes(q.getnframes()), np.int16).reshape(-1, ch); q.close()
        parts, last = [], 0
        for g in gaps_at:
            i = int(g * fr_); parts += [raw[last:i], np.zeros((int(1.1 * fr_), ch), np.int16)]; last = i
        parts.append(raw[last:]); voice = os.path.join(ep_dir, "out", "voice_fx.wav"); os.makedirs(os.path.dirname(voice), exist_ok=True)
        q = wave.open(voice, "wb"); q.setnchannels(ch); q.setsampwidth(sw); q.setframerate(fr_); q.writeframes(np.concatenate(parts).tobytes()); q.close()
        res, vlen = align(ep, voice)
    intro_u = res[0]; outro_u = res[-1]; mid = res[1:-1]
    SCN = [min(a for (u, a, b, s) in mid if u[0] == i) - LEAD for i in range(len(ep["scenes"]))]
    OUT_T = outro_u[1] - LEAD; TOTAL = OFF + vlen + 1.2
    if cutbook: TOTAL = OFF + OUT_T + 4.5          # the spoken book line is cut, so the closing is shorter
    SUBS = [(a + 0.05, u[2]) for (u, a, b, s) in mid]; SUB_END = OUT_T - 0.3
    if os.environ.get("PREP_ONLY"):                     # print scene-relative timings for tuning panels, then stop
        for (u, a, b, s) in res: print(f"{a:7.2f}  [{u[0]}] +{a - (SCN[u[0]] if isinstance(u[0], int) else 0):5.2f}  {u[1][:50]}")
        print("voice", vlen); return
    iseg = intro_u[3]; line_b = max(iseg[1:], key=lambda s: s[0] - 0)[0] if len(iseg) > 1 else intro_u[1] + 2.0
    if len(iseg) > 1:                                   # second half starts after the longest pause inside the hook
        gaps = [(iseg[k][0] - iseg[k - 1][1], iseg[k][0]) for k in range(1, len(iseg))]; line_b = max(gaps)[1]
    gag = None
    if ep.get("intro_gag") and len(iseg) >= 3:          # "satu hirupan" -> scratch -> "Eh, tak cukup. Dua hirupan!"
        gaps = [(iseg[k][0] - iseg[k - 1][1], k) for k in range(1, len(iseg))]; km = max(gaps)[1]
        before = [g for g in gaps if g[1] < km]; after = [g for g in gaps if g[1] > km]
        line_b = iseg[max(before)[1]][0] if before else (iseg[0][0] + iseg[km - 1][1]) / 2
        t_scr = iseg[km - 1][1] + 0.08; t_dua = iseg[max(after)[1]][0] if after else iseg[km][0] + 1.0
        gag = (OFF + t_scr, OFF + t_dua)
    ep["_gag"] = gag
    intro = Intro(ep["title"][0], ep["title"][1], OFF + SCN[0], OFF + intro_u[1], OFF + line_b)
    CLK = OUT_T - SCN[0]; outro = Outro(ep.get("book", {}).get("title", ""), ep.get("book", {}).get("author", ""), clk_str(CLK))
    panels = [Panel(sc["panel"], ep_dir) for sc in ep["scenes"]]; bgs = [bg(0), bg(1)]

    def scene(i, tv):
        sc = ep["scenes"][i]; age = tv - SCN[i]; dur = (SCN[i + 1] if i + 1 < len(SCN) else OUT_T) - SCN[i]
        fr = bgs[i % 2].copy(); ck = ease_out(age / 0.45); im = panels[i].render(age, dur)
        if ck < 1: im.putalpha(im.getchannel("A").point(lambda v: int(v * ck)))
        fr.alpha_composite(im, (CX0, int(CY0 + (1 - ck) * 30)))
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); head(sc["head"], age, ImageDraw.Draw(lay), lay); fr.alpha_composite(lay)
        if sc.get("source"):
            f = F("inter", 28, 500); s = "Sumber: " + sc["source"]; ImageDraw.Draw(fr).text((W - 60 - text_w(f, s), 1342), s, font=f, fill=fade(FG, 0.63))
        return fr
    def mid_frame(tv):
        i = max(k for k in range(len(SCN)) if SCN[k] <= tv); fr = scene(i, tv)
        if i > 0 and tv - SCN[i] < 0.3: fr = Image.blend(scene(i - 1, tv), fr, ease_out((tv - SCN[i]) / 0.3))
        d = ImageDraw.Draw(fr); draw_center(d, 96, clk_str(max(0, tv - SCN[0])), F("mono", 64), (255, 255, 255, 255))
        draw_center(d, 185, "Antara dua hirupan kopi", F("inter", 34, 700), fade(FG, 0.82))
        cur = [s for s in SUBS if s[0] <= tv]
        if cur and tv < SUB_END: subtitle(fr, cur[-1][1], tv - cur[-1][0])
        fr.alpha_composite(BANNER); return fr
    def frame(t):
        tv = t - OFF
        if tv < SCN[0]: return intro.frame(t)
        if tv >= OUT_T:
            fr = outro.frame(tv - OUT_T)
            return Image.blend(mid_frame(OUT_T - 0.001), fr, ease_out((tv - OUT_T) / 0.3)) if tv - OUT_T < 0.3 else fr
        fr = mid_frame(tv)
        return Image.blend(intro.frame(OFF + SCN[0] - 0.001), fr, ease_out((tv - SCN[0]) / 0.3)) if tv - SCN[0] < 0.3 else fr

    if ep.get("style") == "kopitiam":
        import style_kopitiam
        frame, _ = style_kopitiam.build(ep, SCN, OUT_T, SUBS, SUB_END, OFF + intro_u[1], OFF + line_b, OFF, panels)
    out_dir = os.path.join(ep_dir, "out"); os.makedirs(out_dir, exist_ok=True); silent = os.path.join(out_dir, "silent.mp4")
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", silent], stdin=subprocess.PIPE)
    for fi in range(int(TOTAL * FPS)): ff.stdin.write(frame(fi / FPS).convert("RGB").tobytes())
    ff.stdin.close(); ff.wait()
    for p in panels:
        if p.clip: p.clip.close()

    # audio: chatter bed + call + A + voice + ticks + B
    sr = 44100; n = int(TOTAL * sr); tt = np.arange(n) / sr; SFX = os.path.join(HERE, "sfx")
    def wav(p, af=None):
        tmp = os.path.join(out_dir, "_tmp.wav"); subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", p] + (["-af", af] if af else []) + ["-ar", "44100", "-ac", "2", tmp], check=True)
        q = wave.open(tmp); return np.frombuffer(q.readframes(q.getnframes()), np.int16).reshape(-1, 2) / 32768
    slow = f"atempo={CHATTER_TEMPO}"; cut = int((9.9 / CHATTER_TEMPO) * sr)
    c1 = wav(os.path.join(SFX, "chatter_1.wav"), slow)[int(0.3 * sr):cut]; c2 = wav(os.path.join(SFX, "chatter_2.wav"), slow)[int(0.3 * sr):cut]
    def chain(order, skip):
        o = np.zeros((n + sr * 12, 2)); pos, i, xf = 0, 0, int(1.2 * sr); r = np.linspace(0, 1, xf)[:, None]
        while pos < n:
            s = order[i % 2].copy()
            if i == 0: s = s[int(skip * sr):]
            s[-xf:] *= r[::-1]
            if i: s[:xf] *= r
            o[pos:pos + len(s)] += s; pos += len(s) - xf; i += 1
        return o[:n]
    bed = chain([c1, c2], 0) * 0.8 + chain([c2, c1], 4.7 / CHATTER_TEMPO)[:, ::-1] * 0.5
    env = np.where(tt < OFF - 0.2, CHATTER_LEVEL[0], CHATTER_LEVEL[1]) * np.clip(tt / 0.4, 0, 1) * np.clip((TOTAL - tt) / 2, 0, 1)
    k_ = int(0.3 * sr); cs = np.cumsum(np.concatenate([np.full(k_, env[0]), env, np.full(k_, env[-1])])); env = ((cs[2 * k_:] - cs[:-2 * k_]) / (2 * k_))[:n]
    mix = bed * env[:, None] * ep.get("chatter_scale", 1.0)
    if ep.get("music"):                           # optional music bed (looped), e.g. the weekly pantun recap
        mu = wav(os.path.join(HERE, "music", ep["music"]["file"])); reps = n // len(mu) + 1; mu = np.tile(mu, (reps, 1))[:n]
        menv = ep["music"].get("level", 0.15) * np.clip((tt - 0.2) / 1.5, 0, 1) * np.clip((TOTAL - tt) / 2.5, 0, 1)
        mix += mu * menv[:, None]
    def put(x, at, g):
        s = int(at * sr); e = min(n, s + len(x)); mix[s:e] += x[:e - s] * g
    put(wav(os.path.join(SFX, "shout.wav")), 0.0, 1.2); put(wav(os.path.join(SFX, "ahh_A.wav")), 1.25, 1.0); vo = wav(voice)
    if cutbook:                                   # cut the voice before the spoken book line
        cut = int((outro_u[1] - 0.12) * sr); vo = vo[:cut].copy(); f = int(0.08 * sr); vo[-f:] *= np.linspace(1, 0, f)[:, None]
    put(vo, OFF, 1.6)
    put(wav(os.path.join(SFX, "ting_B.wav")), OFF + OUT_T + Outro.LAND - 0.143, 1.1)
    if gag: put(wav(os.path.join(SFX, "scratch.wav")), gag[0], 0.9)
    says = [({"say": x} if isinstance(x, str) else x) for sc in ep["scenes"] for x in sc["say"]]
    for (u, a, b, s_), sd in zip(mid, says):           # optional sound after a sentence, e.g. {"sfx_after": "ahh_A"}
        if sd.get("sfx_after"): put(wav(os.path.join(SFX, sd["sfx_after"] + ".wav")), OFF + b + 0.05, 0.8)
    if ep.get("scene_ting"):                      # soft "ting" at each new story
        tg = wav(os.path.join(SFX, "ting_B.wav"))
        for i in range(1, len(SCN)): put(tg, OFF + SCN[i] - 0.05, ep.get("scene_ting_gain", 0.45))
    tk = np.arange(int(0.03 * sr)) / sr; click = np.repeat((np.sin(2 * np.pi * 1800 * tk) * np.exp(-tk * 180) * 0.025)[:, None], 2, axis=1)
    for s_ in range(int(CLK) + 1): put(click, OFF + SCN[0] + s_, 1.0)
    mix *= 0.9 / np.abs(mix).max(); mixp = os.path.join(out_dir, "mix.wav")
    w = wave.open(mixp, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes((mix * 32767).astype(np.int16).tobytes()); w.close()
    final = os.path.join(out_dir, f"{ep['slug']}{'-tiktok' if nobook else ''}.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-i", mixp, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-af", "loudnorm=I=-14:TP=-1.5",
                    "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", final], check=True)
    # contact sheet for checking: one frame per scene + opening + closing
    times = [2.0, OFF + SCN[0] - 0.5] + [OFF + SCN[i] + 1.6 for i in range(len(SCN))] + [OFF + OUT_T + 2.5]
    sheet = Image.new("RGB", (216 * 7, 384 * ((len(times) + 6) // 7)))
    for k, t in enumerate(times):
        p = os.path.join(out_dir, "_f.png"); subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{t:.2f}", "-i", final, "-frames:v", "1", "-vf", "scale=216:-1", p])
        sheet.paste(Image.open(p), ((k % 7) * 216, (k // 7) * 384))
    sheet.save(os.path.join(out_dir, "sheet.png"))
    for p in ("silent.mp4", "_tmp.wav", "_f.png", "mix.wav"):
        try: os.remove(os.path.join(out_dir, p))
        except OSError: pass
    print(json.dumps({"video": final, "length": round(TOTAL, 1), "scenes": [round(x, 2) for x in SCN], "outro": round(OUT_T, 2), "clock": clk_str(CLK)}))

if __name__ == "__main__":
    if sys.argv[1] == "render" and "--no-book" in sys.argv: cmd_render(sys.argv[2], nobook=True)
    else: {"script": cmd_script, "align": cmd_align, "render": cmd_render}[sys.argv[1]](sys.argv[2])
