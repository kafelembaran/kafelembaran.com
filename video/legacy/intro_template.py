"""Kafe Lembaran opening template ('Dua Hirupan'), Kafe Klasik style.
Usage: python3 intro_template.py "Line 1" "Line 2" [out.mp4]
Sound A ('ahh') plays at the start; music fades in under it."""
import subprocess, sys, wave
ARGS = sys.argv[1:]; sys.argv = [sys.argv[0]]
exec(open('/home/claude/samples/render_samples.py').read().split('if __name__ == "__main__":')[0])
L1, L2 = (ARGS + ["Kejatuhan", "Jensen Huang?"])[:2]
OUT = ARGS[2] if len(ARGS) > 2 else f"{D}/intro-dua-hirupan.mp4"
th = THEMES[1]; FG = hexc(th["fg"]); GOLD = hexc(th["acc"]); TOTAL = 4.2; A_AT = 0.3
bg = make_bg(th, 0).convert("RGBA")
cup = Image.open(f"{D}/sil_cup.png").convert("RGBA")
bb = cup.getbbox(); cup = cup.crop(bb); cw = 440; cup = cup.resize((cw, int(cup.height * cw / cup.width)), Image.BICUBIC)
CUP_X, CUP_Y = (W - cw) // 2 - 30, 980

def cup_layer(alpha):
    a = cup.getchannel("A").point(lambda v: int(v * alpha)); c = Image.new("RGBA", cup.size, FG); c.putalpha(a); return c

def steam(d, t, alpha):
    # three wavy wisps rising from the cup
    for k, x0 in enumerate((CUP_X + 140, CUP_X + 200, CUP_X + 260)):
        pts = []
        for j in range(26):
            y = CUP_Y - 20 - j * 9
            x = x0 + 14 * math.sin(j * 0.35 + t * 3.0 + k * 2.1) * (j / 26 + 0.3)
            pts.append((x, y))
        for j in range(len(pts) - 1):
            fade = (1 - j / len(pts)) * alpha
            d.line([pts[j], pts[j + 1]], fill=FG[:3] + (int(150 * fade),), width=6)

def frame(t):
    fr = bg.copy(); lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    k0 = ease_out(t / 0.5)
    # kicker
    fk = F("poppins", 34); kk = ease_out((t - 0.2) / 0.5)
    draw_center(d, 300 + (1 - kk) * 20, "DUA HIRUPAN KOPI", fk, GOLD[:3] + (int(255 * kk),))
    d.line([(W / 2 - 60, 360), (W / 2 + 60, 360)], fill=GOLD[:3] + (int(255 * kk),), width=4)
    # title
    ft = F("lora", 128, 700)
    for i, (s, y) in enumerate(((L1, 410), (L2, 560))):
        k = ease_out((t - 0.45 - i * 0.2) / 0.6)
        draw_center(d, y + (1 - k) * 50, s, ft, (GOLD if i == 1 else FG)[:3] + (int(255 * k),))
    # cup + steam
    fr.alpha_composite(cup_layer(0.9 * k0), (CUP_X, CUP_Y)); steam(d, t, k0)
    # narrator line
    fq = F("lora", 60, 500); ka = ease_out((t - 1.5) / 0.5); kb = ease_out((t - 2.1) / 0.5)
    draw_center(d, 1400 + (1 - ka) * 20, "“Biar saya terangkan…", fq, FG[:3] + (int(255 * ka),))
    draw_center(d, 1480 + (1 - kb) * 20, "di antara dua hirupan kopi.”", fq, GOLD[:3] + (int(255 * kb),))
    fr.alpha_composite(lay); fr.alpha_composite(banner)
    if t > TOTAL - 0.35:          # quick fade to dark so the next scene can cut in
        f = (t - (TOTAL - 0.35)) / 0.35; fr.alpha_composite(Image.new("RGBA", (W, H), (10, 30, 28, int(120 * f))))
    return fr

silent = f"{D}/intro_silent.mp4"
ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                       "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", silent], stdin=subprocess.PIPE)
for fi in range(int(TOTAL * FPS)): ff.stdin.write(frame(fi / FPS).convert("RGB").tobytes())
ff.stdin.close(); ff.wait()

sr = 44100; n = int(TOTAL * sr)
def load(p):
    w = wave.open(p); return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).reshape(-1, 2) / 32768.0
mus = load("/home/claude/video-huang/v5/musicn.wav")[:n].copy()
env = np.clip(np.arange(n) / sr / 1.5, 0, 1); s = int(A_AT * sr); e = int((A_AT + 1.1) * sr); env[s:e] *= 0.35
mix = mus * env[:, None]; a = load("/home/claude/gem/c1_ahhA.wav"); mix[s:s + len(a)] += a[:n - s] * 0.9
pcm = (np.clip(mix, -1, 1) * 32767).astype(np.int16)
w = wave.open(f"{D}/intro.wav", "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes(pcm.tobytes()); w.close()
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-i", f"{D}/intro.wav", "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                "-af", "loudnorm=I=-16:TP=-1.5", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", OUT], check=True)
print("ok", OUT)
