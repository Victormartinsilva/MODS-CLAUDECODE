"""Embute audio/a{n}.mp3 como base64 no marcador /*AUDIO*/ e grava o HTML final."""
import base64, pathlib, sys

src, audio_dir, dst = map(pathlib.Path, sys.argv[1:4])
files = sorted(audio_dir.glob("a*.mp3"), key=lambda p: int(p.stem[1:]))
items = ",".join('"' + base64.b64encode(p.read_bytes()).decode() + '"' for p in files)
html = src.read_text(encoding="utf-8")
assert "/*AUDIO*/" in html
dst.write_text(html.replace("/*AUDIO*/", items), encoding="utf-8")
print(len(files), "audios,", round(dst.stat().st_size / 1e6, 2), "MB")
