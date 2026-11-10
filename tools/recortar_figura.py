#!/usr/bin/env python3
"""Recorta uma figura de artigo em PDF para lâmina.

Uso: recortar_figura.py <pdf> <página> <x> <y> <larg> <alt> <saida.png> [--sem-letra]
     x, y, larg, alt em pontos do PDF (1/72"), medidos a partir do canto superior esquerdo.

Rasteriza só a caixa a 500 dpi (pdftoppm), apaga filetes escuros nas bordas e barras pretas
encostadas na margem, apara o branco em volta e, com --sem-letra, apaga a letra do painel
(A, B…) no canto superior esquerdo. Conferir o resultado visualmente sempre.
"""
import subprocess, sys, tempfile, os
from PIL import Image, ImageChops

DPI = 500


def rasterizar(pdf, pag, x, y, w, h):
    k = DPI / 72
    base = os.path.join(tempfile.mkdtemp(), "r")
    subprocess.run(["pdftoppm", "-png", "-r", str(DPI), "-f", str(pag), "-l", str(pag), "-singlefile",
                    "-x", str(round(x * k)), "-y", str(round(y * k)),
                    "-W", str(round(w * k)), "-H", str(round(h * k)), pdf, base], check=True)
    return Image.open(base + ".png").convert("RGB")


def limpar_bordas(im, faixa=12, escuro=110, cobertura=0.6):
    """Apaga linhas/colunas escuras que atravessam a figura junto às bordas (filete, barra)."""
    g = im.convert("L"); W, H = g.size; px = g.load(); im = im.copy()
    linhas = [r for r in list(range(faixa)) + list(range(H - faixa, H))
              if sum(px[c, r] < escuro for c in range(W)) > cobertura * W]
    colunas = [c for c in list(range(faixa)) + list(range(W - faixa, W))
               if sum(px[c, r] < escuro for r in range(H)) > cobertura * H]
    for r in linhas: im.paste((255, 255, 255), (0, r, W, r + 1))
    for c in colunas: im.paste((255, 255, 255), (c, 0, c + 1, H))
    return im


def aparar(im, margem=20):
    fundo = Image.new("RGB", im.size, (255, 255, 255))
    caixa = ImageChops.difference(im, fundo).convert("L").point(lambda v: 255 if v > 18 else 0).getbbox()
    if not caixa: return im
    x0, y0, x1, y1 = caixa
    return im.crop((max(0, x0 - margem), max(0, y0 - margem), min(im.width, x1 + margem), min(im.height, y1 + margem)))


def sem_letra(im, frac=0.07):
    """Branqueia o canto superior esquerdo, onde fica a letra do painel."""
    im = im.copy(); s = round(min(im.size) * frac)
    im.paste((255, 255, 255), (0, 0, s, s))
    return im


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    if len(a) != 7: sys.exit(__doc__)
    pdf, pag, x, y, w, h, saida = a[0], int(a[1]), *map(float, a[2:6]), a[6]
    im = rasterizar(pdf, pag, x, y, w, h)
    im = limpar_bordas(im)
    if "--sem-letra" in sys.argv: im = sem_letra(im)
    im = aparar(im)
    im.save(saida, optimize=True)
    print(f"{saida}: {im.width}×{im.height} px")
