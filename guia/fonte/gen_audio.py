"""Gera um mp3 por legenda do guia-mods.html, na ordem em que as cenas aparecem."""
import asyncio, re, sys, pathlib
import edge_tts

html = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
out = pathlib.Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
caps = re.findall(r"\[\s*'([^']+)',\s*(?:async|null)", html)
print(len(caps), "legendas")

async def main():
    for i, t in enumerate(caps):
        await edge_tts.Communicate(t, "pt-BR-FranciscaNeural", rate="+5%").save(str(out / f"a{i}.mp3"))
        print(i, t[:50])

asyncio.run(main())
