#!/usr/bin/env python3
"""Audita as figuras do deck: resolução efetiva e figuras órfãs/ausentes.

    /usr/local/bin/python3 qa_figuras.py

Para cada <img src="img/fig/..."> do deck, calcula quantos pixels da imagem caem
por pixel de palco (o deck é 1920x1080) e sinaliza o que está abaixo de 1,0 —
essas são as candidatas a trocar pela figura original do artigo
(ver ref/artigos-por-lamina.json). Também lista figuras referenciadas que não
existem e arquivos em img/fig/ que ninguem usa.
"""
import re
import pathlib
import sys

try:
    from PIL import Image
except ImportError:
    sys.exit("precisa do Pillow: use /usr/local/bin/python3")

BASE = pathlib.Path(__file__).parent
PARTS = sorted((BASE / "parts").glob("*.html"))
FIGDIR = BASE / "img" / "fig"

IMG_RE = re.compile(r'<img[^>]+src="(img/fig/[^"]+)"', re.I)
BOX_RE = re.compile(r'class="figwrap([^"]*)"[^>]*style="([^"]*)"', re.I)
NUM_RE = re.compile(r'(left|right|top|bottom|width|height):\s*(-?\d+)px')


def caixa(style, duo):
    """Largura/altura em px de palco a partir do style do .figwrap."""
    v = {k: int(n) for k, n in NUM_RE.findall(style)}
    w = v.get("width")
    if w is None:
        w = 1920 - v.get("left", 0) - v.get("right", 0)
    h = v.get("height")
    if h is None:
        h = 1080 - v.get("top", 0) - v.get("bottom", 0)
    if duo:
        w = w / 2
    return max(w, 1), max(h, 1)


def main():
    usadas, problemas, baixas = set(), [], []
    # cada <div class="figwrap ..." style="..."> ... </div> e uma caixa; as <img> dentro
    # dela dividem o espaco (classe "duo" = duas colunas, "trio" = tres).
    BLOCO_RE = re.compile(r'<div class="figwrap([^"]*)"[^>]*style="([^"]*)"[^>]*>(.*?)</div>', re.S)
    SOLTA_RE = re.compile(r'<img[^>]+src="(img/fig/[^"]+)"')

    for p in PARTS:
        html = p.read_text(encoding="utf-8")
        vistos = set()
        for cls, style, dentro in BLOCO_RE.findall(html):
            srcs = SOLTA_RE.findall(dentro)
            if not srcs:
                continue
            n = len(srcs)
            cw, ch = caixa(style, False)
            if "duo" in cls or n == 2:
                cw = cw / 2
            elif "trio" in cls or n >= 3:
                cw = cw / n
            for src in srcs:
                vistos.add(src)
                usadas.add(src.split("/")[-1])
                arq = BASE / src
                if not arq.exists():
                    problemas.append(f"{p.name}: referencia {src} — ARQUIVO NAO EXISTE")
                    continue
                try:
                    iw, ih = Image.open(arq).size
                except Exception as e:
                    problemas.append(f"{p.name}: {src} nao abre ({e})")
                    continue
                escala = min(cw / iw, ch / ih)
                dens = 1 / escala if escala else 0
                if dens < 1.0:
                    baixas.append((dens, p.name, src, f"{iw}x{ih}", f"caixa {int(cw)}x{int(ch)}"))
        # imagens fora de um figwrap com geometria: so confere existencia
        for src in SOLTA_RE.findall(html):
            if src in vistos:
                continue
            usadas.add(src.split("/")[-1])
            if not (BASE / src).exists():
                problemas.append(f"{p.name}: referencia {src} — ARQUIVO NAO EXISTE")

    orfas = sorted(f.name for f in FIGDIR.glob("*.png") if f.name not in usadas)

    print(f"figuras referenciadas: {len(usadas)} · arquivos em img/fig: {len(list(FIGDIR.glob('*.png')))}")
    if problemas:
        print("\nPROBLEMAS")
        for x in problemas:
            print("  " + x)
    if baixas:
        print("\nRESOLUCAO ABAIXO DE 1 px de imagem por px de palco (trocar pela figura do artigo)")
        for d, part, src, tam, box in sorted(baixas):
            print(f"  {d:.2f}x  {part:28s} {src.split('/')[-1]:34s} {tam:12s} {box}")
    if orfas:
        print("\nFIGURAS SEM USO em img/fig/")
        for x in orfas:
            print("  " + x)
    if not problemas and not baixas:
        print("\nok — todas as figuras existem e tem resolucao suficiente")


if __name__ == "__main__":
    main()
