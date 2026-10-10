"""Monta guia.mp4 (video + narracao sincronizada) e guia.gif (trecho) a partir da gravacao.
Uso: python assemble.py <pasta da gravacao> <pasta dos mp3> <pasta de saida> <legenda inicial do gif> <legenda final do gif>
"""
import json, pathlib, re, subprocess, sys
import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()
rec, audio, out = (pathlib.Path(a) for a in sys.argv[1:4]); out.mkdir(parents=True, exist_ok=True)
gif_from, gif_to = int(sys.argv[4]), int(sys.argv[5])
ts = json.loads((rec / "frames.json").read_text())
log = json.loads((rec / "log.json").read_text())
t0 = ts[0]

def run(args):
    r = subprocess.run([FF, "-hide_banner", "-y", *args], capture_output=True, text=True)
    if r.returncode: sys.exit(r.stderr[-3000:])
    return r.stderr

def duration(p):
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", subprocess.run([FF, "-i", str(p)], capture_output=True, text=True).stderr)
    return int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3])

# 1. quadros com duracao variavel -> video 30 fps
lines = []
for i, t in enumerate(ts):
    d = (ts[i + 1] - t) if i + 1 < len(ts) else 1.0
    lines += [f"file '{(rec / 'frames' / f'f{i:06d}.jpg').as_posix()}'", f"duration {max(d, 0.001):.4f}"]
lines.append(lines[-2])
(rec / "list.txt").write_text("\n".join(lines))
run(["-f", "concat", "-safe", "0", "-i", str(rec / "list.txt"), "-vf", "fps=30,format=yuv420p",
     "-c:v", "libx264", "-preset", "slow", "-crf", "27", str(rec / "video.mp4")])

# 2. narracao: cada mp3 no instante em que a legenda apareceu
for a, b in zip(log, log[1:]):
    d = duration(audio / f"a{a['n']}.mp3")
    if b["t"] - a["t"] < d - 0.2:
        print(f"aviso: legenda {a['n']} sobrepoe ({b['t'] - a['t']:.1f}s < {d:.1f}s)")
ins, flt = [], []
for k, e in enumerate(log):
    ms = int((e["t"] - t0) * 1000)
    ins += ["-i", str(audio / f"a{e['n']}.mp3")]
    flt.append(f"[{k + 1}:a]adelay={ms}|{ms}[a{k}]")
flt.append("".join(f"[a{k}]" for k in range(len(log))) + f"amix=inputs={len(log)}:normalize=0[aout]")
run(["-i", str(rec / "video.mp4"), *ins, "-filter_complex", ";".join(flt), "-map", "0:v", "-map", "[aout]",
     "-c:v", "copy", "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", str(out / "guia.mp4")])

# 3. GIF de um trecho (sem som)
start = next(e["t"] for e in log if e["n"] == gif_from) - t0 - 0.3
end = next(e["t"] for e in log if e["n"] == gif_to) - t0
run(["-ss", f"{start:.2f}", "-to", f"{end:.2f}", "-i", str(rec / "video.mp4"), "-vf",
     "fps=10,scale=800:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=96:stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle",
     str(out / "guia.gif")])
for f in ("guia.mp4", "guia.gif"):
    print(f, round((out / f).stat().st_size / 1e6, 1), "MB")
print("duracao", round(duration(out / "guia.mp4")), "s; gif", round(end - start), "s")
