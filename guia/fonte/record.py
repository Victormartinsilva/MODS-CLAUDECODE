"""Grava o guia (modo #rec) com o Chrome headless via CDP.

Salva os quadros do screencast (frames/*.jpg + frames.json com o horario de cada um)
e log.json com o horario em que cada legenda comecou.
Uso: python record.py <guia.html com audio embutido> <pasta de saida>
"""
import asyncio, base64, json, pathlib, subprocess, sys, tempfile
import aiohttp

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PORT = 9333
html = pathlib.Path(sys.argv[1]).resolve()
out = pathlib.Path(sys.argv[2]); frames = out / "frames"; frames.mkdir(parents=True, exist_ok=True)

proc = subprocess.Popen([CHROME, "--headless=new", f"--remote-debugging-port={PORT}",
    f"--user-data-dir={tempfile.mkdtemp()}", "--window-size=1280,800", "--hide-scrollbars",
    "--autoplay-policy=no-user-gesture-required", "--mute-audio", "--force-device-scale-factor=1", "about:blank"])

async def main():
    async with aiohttp.ClientSession() as s:
        for _ in range(100):
            try:
                async with s.get(f"http://127.0.0.1:{PORT}/json") as r:
                    tabs = await r.json(); break
            except Exception:
                await asyncio.sleep(0.2)
        tab = next(t for t in tabs if t["type"] == "page")
        ws = await s.ws_connect(tab["webSocketDebuggerUrl"], max_msg_size=0)
        pending, meta, seq = {}, [], [0]

        async def call(method, **params):
            seq[0] += 1; fut = asyncio.get_running_loop().create_future(); pending[seq[0]] = fut
            await ws.send_json({"id": seq[0], "method": method, "params": params})
            return await fut

        async def reader():
            async for msg in ws:
                d = json.loads(msg.data)
                if d.get("id") in pending:
                    pending.pop(d["id"]).set_result(d.get("result"))
                elif d.get("method") == "Page.screencastFrame":
                    p = d["params"]; i = len(meta)
                    (frames / f"f{i:06d}.jpg").write_bytes(base64.b64decode(p["data"]))
                    meta.append(p["metadata"]["timestamp"])
                    await ws.send_json({"id": 10**9 + i, "method": "Page.screencastFrameAck",
                                        "params": {"sessionId": p["sessionId"]}})

        rt = asyncio.create_task(reader())
        await call("Page.enable")
        await call("Emulation.setDeviceMetricsOverride", width=1280, height=800, deviceScaleFactor=1, mobile=False)
        await call("Page.navigate", url=html.as_uri() + "#rec")
        await asyncio.sleep(4)
        await call("Page.startScreencast", format="jpeg", quality=88, maxWidth=1280, maxHeight=800, everyNthFrame=1)
        await asyncio.sleep(1.5)
        await call("Runtime.evaluate", expression="window.__start()")
        while True:
            await asyncio.sleep(1)
            r = await call("Runtime.evaluate", expression="JSON.stringify({d:!!window.__done,l:window.__log})", returnByValue=True)
            v = json.loads(r["result"]["value"])
            if v["d"]:
                break
        await asyncio.sleep(3)
        await call("Page.stopScreencast")
        await asyncio.sleep(0.5)
        (out / "frames.json").write_text(json.dumps(meta))
        (out / "log.json").write_text(json.dumps(v["l"]))
        print(len(meta), "quadros,", len(v["l"]), "legendas,", round(meta[-1] - meta[0]), "s")
        rt.cancel()

try:
    asyncio.run(main())
finally:
    proc.terminate()
