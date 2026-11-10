#!/usr/bin/env python3
"""Renderiza UMA lamina do deck em PNG 1920x1080, para conferir uma edicao.

    /usr/local/bin/python3 render_lamina.py <nome-do-part> <saida.png> [--passos N] [--online]

Monta o deck (build.sh), abre no Chromium headless, vai ate a lamina e tira a foto.
--passos N   aperta N vezes a barra de espaco antes da foto (revela data-passo / cortina).
--online     liga o modo on-line (tecla W) antes da foto.
Sem --passos, usa ?static=1 (tudo revelado, sem animacao) — e o estado "final" da lamina.
"""
import asyncio
import pathlib
import subprocess
import sys

BASE = pathlib.Path(__file__).parent


async def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    nome, saida = sys.argv[1], pathlib.Path(sys.argv[2])
    passos = int(sys.argv[sys.argv.index("--passos") + 1]) if "--passos" in sys.argv else 0
    online = "--online" in sys.argv
    subprocess.run(["./build.sh"], cwd=BASE, check=True, capture_output=True)
    ordem = [l.strip() for l in (BASE / "order.txt").read_text(encoding="utf-8").splitlines()
             if l.strip() and not l.startswith("#")]
    if nome not in ordem:
        sys.exit(f"'{nome}' nao esta no order.txt (visivel). Confira o nome do part.")
    i = ordem.index(nome) + 1
    from playwright.async_api import async_playwright
    async with async_playwright() as pw:
        b = await pw.chromium.launch()
        pg = await b.new_page(viewport={"width": 1920, "height": 1080})
        url = (BASE / "deck.html").resolve().as_uri() + ("" if passos else "?static=1") + f"#{i}"
        await pg.goto(url)
        if online:
            await pg.evaluate("()=>{ if(typeof modoOnline==='function') modoOnline(true); }")
        await pg.wait_for_timeout(1100)
        for _ in range(passos):
            await pg.keyboard.press(" ")
            await pg.wait_for_timeout(900)
        await pg.screenshot(path=str(saida))
        await b.close()
    print(f"{saida} (lamina {i}: {nome}{', ' + str(passos) + ' passo(s)' if passos else ''}{', on-line' if online else ''})")


asyncio.run(main())
