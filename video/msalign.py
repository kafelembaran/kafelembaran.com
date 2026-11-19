"""Forced alignment of a Malay script to a voice file, using pocketsphinx's English acoustic model
and a rule-based Malay spelling -> phone mapping. Returns word timings (start, end) in seconds."""
import re, subprocess, os, tempfile
import numpy as np

DIGR = [("ngg", ["NG", "G"]), ("ng", ["NG"]), ("ny", ["N", "Y"]), ("sy", ["SH"]), ("kh", ["K"]), ("gh", ["G"]),
        ("ai", ["AY"]), ("au", ["AW"]), ("oi", ["OY"])]
ONE = {"a": "AA", "b": "B", "c": "CH", "d": "D", "e": "AH", "f": "F", "g": "G", "h": "HH", "i": "IY", "j": "JH", "k": "K",
       "l": "L", "m": "M", "n": "N", "o": "OW", "p": "P", "q": "K", "r": "R", "s": "S", "t": "T", "u": "UW", "v": "V",
       "w": "W", "x": "K", "y": "Y", "z": "Z"}

def phones(w):
    out, i = [], 0
    while i < len(w):
        for g, ph in DIGR:
            if w.startswith(g, i) and not (g in ("ai", "au", "oi") and i + 2 < len(w) and w[i + 2] in "aeiou"):
                out += ph; i += len(g); break
        else:
            if w[i] in ONE and not (out and out[-1] == ONE[w[i]]): out.append(ONE[w[i]])
            i += 1
    return out or ["AH"]

def words_of(text):
    return [w for w in re.split(r"[^a-z]+", text.lower()) if w]

def align_words(wav_path, words):
    from pocketsphinx import Decoder, get_model_path
    tmp = tempfile.mkdtemp(); dic = os.path.join(tmp, "my.dict")
    with open(dic, "w") as f:
        for w in sorted(set(words)): f.write(f"{w} {' '.join(phones(w))}\n")
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", wav_path, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                         capture_output=True, check=True).stdout
    dec = Decoder(hmm=os.path.join(get_model_path(), "en-us", "en-us"), dict=dic, samprate=16000, loglevel="FATAL",
                  beam=1e-80, wbeam=1e-60, pbeam=1e-80)
    dec.set_align_text(" ".join(words))
    dec.start_utt(); dec.process_raw(raw, full_utt=True); dec.end_utt()
    segs = [(s.word, s.start_frame / 100.0, (s.end_frame + 1) / 100.0) for s in dec.seg() if s.word not in ("<s>", "</s>", "<sil>", "(NULL)")]
    return segs
