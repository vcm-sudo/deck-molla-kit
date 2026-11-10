#!/usr/bin/env python3
"""Portao de QA dos QR codes: decodifica o que esta EMBUTIDO no deck.html.

    /usr/local/bin/python3 qa_qr.py

Le cada bloco <!--QR:nome-->...<!--/QR:nome--> do deck montado, renderiza o SVG,
decodifica com o detector do OpenCV e confere:
  1. decodifica (QR quebrado nao adianta gerar)
  2. aponta para o app certo (POLL_BASE do build_qr.py)
  3. tem d=<DECK> — sem isso o celular abre a aula ERRADA, a ultima que estiver
     na raiz do app. Foi exatamente o que aconteceu antes: o deck nasceu copiado
     de outra aula e carregava os QR dela.
  4. tem s=<sessao> igual a POLL_SESSION do deck

Sai com 1 se algo falhar.
"""
import asyncio
import pathlib
import re
import sys
import tempfile

import cv2
from playwright.async_api import async_playwright

BASE = pathlib.Path(__file__).parent


# QR que apontam de proposito para fora do app da aula (o episodio do podcast)
EXTERNOS = {"podcast"}


def esperado():
    b = (BASE / "build_qr.py").read_text(encoding="utf-8")
    app = re.search(r'POLL_BASE\s*=\s*"([^"]+)"', b).group(1)
    deck = re.search(r'DECK\s*=\s*"([^"]+)"', b).group(1)
    d = (BASE / "deck.html").read_text(encoding="utf-8")
    ses = re.search(r'const POLL_SESSION\s*=\s*"([^"]+)"', d)
    return app, deck, (ses.group(1) if ses else "default")


async def main():
    app, deck, sessao = esperado()
    html = (BASE / "deck.html").read_text(encoding="utf-8")
    blocos = re.findall(r"<!--QR:([^>]+?)-->(.*?)<!--/QR:\1-->", html, re.S)
    if not blocos:
        print("nenhum QR embutido no deck.html — rode ./build.sh")
        return 1
    erros = []
    with tempfile.TemporaryDirectory() as tmp:
        async with async_playwright() as pw:
            b = await pw.chromium.launch()
            pg = await b.new_page(viewport={"width": 600, "height": 600})
            det = cv2.QRCodeDetector()
            for nome, svg in blocos:
                if "build_qr.py" in svg:            # placeholder, QR ainda nao gerado
                    erros.append(f"{nome}: placeholder — rode build_qr.py")
                    continue
                await pg.set_content(
                    f'<div style="width:560px;height:560px;background:#fff;padding:20px">{svg}</div>')
                await pg.wait_for_timeout(110)
                f = f"{tmp}/{nome}.png"
                await pg.screenshot(path=f, clip={"x": 0, "y": 0, "width": 600, "height": 600})
                txt, _, _ = det.detectAndDecode(cv2.imread(f))
                if not txt:
                    # o detector classico do OpenCV falha em alguns QR validos (versoes maiores,
                    # zona de silencio no limite): tenta o detector Aruco e uma captura maior
                    try:
                        txt, _, _ = cv2.QRCodeDetectorAruco().detectAndDecode(cv2.imread(f))
                    except Exception:
                        txt = ""
                if not txt:
                    await pg.set_viewport_size({"width": 1000, "height": 1000})
                    await pg.set_content(
                        f'<div style="width:900px;height:900px;background:#fff;padding:50px">{svg}</div>')
                    await pg.wait_for_timeout(110)
                    await pg.screenshot(path=f, clip={"x": 0, "y": 0, "width": 1000, "height": 1000})
                    await pg.set_viewport_size({"width": 600, "height": 600})
                    txt, _, _ = det.detectAndDecode(cv2.imread(f))
                if not txt:
                    erros.append(f"{nome}: nao decodificou")
                    continue
                if nome in EXTERNOS:
                    if not txt.startswith("https://"):
                        erros.append(f"{nome}: QR externo com URL invalida — {txt}")
                    continue
                if not txt.startswith(app):
                    erros.append(f"{nome}: aponta para outro app — {txt}")
                elif f"d={deck}" not in txt:
                    erros.append(f"{nome}: sem d={deck} — o celular abre a aula errada — {txt}")
                elif sessao != "default" and f"s={sessao}" not in txt:
                    erros.append(f"{nome}: sessao diferente de '{sessao}' — {txt}")
                else:
                    print(f"  ok  {nome:16s} {txt}")
            await b.close()
    print(f"\n{len(blocos)} QR · app {app} · deck {deck} · sessao {sessao}")
    if erros:
        print(f"\nERROS ({len(erros)})")
        for e in erros:
            print("  " + e)
        return 1
    print("ok — todos os QR levam a esta aula")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
