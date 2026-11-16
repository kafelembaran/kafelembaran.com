"""Kafe Lembaran closing template: the cup lands on the saucer, sound B ('ting') fires, channel info + book link pop in.
Usage: python3 outro_template.py "BOOK TITLE" "Author" "00:08:20" [out.mp4]"""
import subprocess, sys, wave
ARGS = sys.argv[1:]; sys.argv = [sys.argv[0]]
exec(open('/home/claude/samples/render_samples.py').read().split('if __name__ == "__main__":')[0])
BOOK, AUTHOR, CLK = (ARGS + ["ADIKUASA", "Ayman Rashdan Wong", "00:08:20"])[:3]
OUT = ARGS[3] if len(ARGS) > 3 else f"{D}/outro-dua-hirupan.mp4"
th = THEMES[1]; FG = hexc(th["fg"]); GOLD = hexc(th["acc"]); TOTAL = 4.6
LAND = 0.55                       # cup touches the saucer
B_FILE = "/home/claude/gem/c2_clinkA.wav"
bg = make_bg(th, 1).convert("RGBA")
cup = Image.open(f"{D}/sil_cup.png").convert("RGBA"); cup = cup.crop(cup.getbbox())
cw = 300; cup = cup.resize((cw, int(cup.height * cw / cup.width)), Image.BICUBIC)
a = cup.getchannel("A"); cupc = Image.new("RGBA", cup.size, FG); cupc.putalpha(a)
CX, CY = (W - cw) // 2, 330

def frame(t):
    fr = bg.copy(); lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    # stopwatch frozen in gold (time between the two sips)
    draw_center(d, 96, CLK, F("mono", 64), GOLD); draw_center(d, 185, "Antara dua hirupan kopi", F("inter", 34, 700), FG[:3] + (210,))
    # cup drops and lands, with a small bounce
    if t < LAND: y = CY - 160 * (1 - ease_out(t / LAND)) ** 1; al = ease_out(t / 0.25)
    else: y = CY - 10 * math.sin(min(1, (t - LAND) / 0.25) * math.pi) * (1 - min(1, (t - LAND) / 0.25)); al = 1
    c2 = cupc.copy(); c2.putalpha(cupc.getchannel("A").point(lambda v: int(v * al))); fr.alpha_composite(c2, (CX, int(y)))
    # ripple rings at the 'ting'
    if t >= LAND:
        for r0 in (0, 0.18):
            p = (t - LAND - r0) / 0.9
            if 0 < p < 1:
                r = 120 + 360 * ease_out(p); cx0, cy0 = W / 2, CY + cup.height - 20
                d.ellipse([cx0 - r, cy0 - r * 0.35, cx0 + r, cy0 + r * 0.35], outline=GOLD[:3] + (int(200 * (1 - p)),), width=5)
    def pop(delay):
        return back_out((t - LAND - delay) / 0.4)
    k = pop(0.05)
    if k > 0.01:
        f = F("lora", int(96 * max(0.4, k)), 700); draw_center(d, 690, "Kafe Lembaran", f, FG[:3] + (int(255 * min(1, k)),))
    k = ease_out((t - LAND - 0.3) / 0.4)
    if k > 0:
        draw_center(d, 830, "BUKU DALAM VIDEO INI", F("poppins", 34), GOLD[:3] + (int(255 * k),))
        draw_center(d, 880 + (1 - k) * 20, BOOK, F("lora", 84, 700), FG[:3] + (int(255 * k),))
        draw_center(d, 990 + (1 - k) * 20, AUTHOR, F("inter", 40, 500), FG[:3] + (int(200 * k),))
    k = pop(0.6)
    if k > 0.01:   # gold pill button
        f = F("poppins", 52); s = "LINK BUKU KAT BIO"; tw = text_w(f, s); pw, ph = (tw + 110) * k, 110 * k
        x0, y0 = W / 2 - pw / 2, 1130 + 55 - ph / 2
        d.rounded_rectangle([x0, y0, x0 + pw, y0 + ph], radius=int(55 * k), fill=GOLD)
        if k > 0.6: draw_center(d, 1130 + 22, s, f, (18, 63, 60, int(255 * min(1, (k - 0.6) / 0.4))))
    k = ease_out((t - LAND - 0.9) / 0.4)
    if k > 0:
        draw_center(d, 1300, "kafelembaran.com", F("inter", 52, 800), GOLD[:3] + (int(255 * k),))
        draw_center(d, 1380, "@kafe.lembaran", F("inter", 44, 600), FG[:3] + (int(230 * k),))
        draw_center(d, 1440, "TikTok · YouTube · Instagram", F("inter", 34, 500), FG[:3] + (int(170 * k),))
    fr.alpha_composite(lay); fr.alpha_composite(banner)
    return fr

silent = f"{D}/outro_silent.mp4"
ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                       "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", silent], stdin=subprocess.PIPE)
for fi in range(int(TOTAL * FPS)): ff.stdin.write(frame(fi / FPS).convert("RGB").tobytes())
ff.stdin.close(); ff.wait()

sr = 44100; n = int(TOTAL * sr)
def load(p):
    w = wave.open(p); return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).reshape(-1, 2) / 32768.0
mus = load("/home/claude/video-huang/v5/musicn.wav"); mus = mus[int(20 * sr):int(20 * sr) + n].copy()
env = np.ones(n) * 0.35; fo = int(1.8 * sr); env[-fo:] *= np.linspace(1, 0, fo)
mix = mus * env[:, None]
b = load(B_FILE); s = int(max(0, LAND - 0.15) * sr)             # the clink peak sits ~0.15 s into the file
mix[s:s + len(b)] += b[:n - s] * 1.0
pcm = (np.clip(mix, -1, 1) * 32767).astype(np.int16)
w = wave.open(f"{D}/outro.wav", "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes(pcm.tobytes()); w.close()
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-i", f"{D}/outro.wav", "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", OUT], check=True)
print("ok", OUT)
