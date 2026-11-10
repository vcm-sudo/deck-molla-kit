#!/usr/bin/env python3
"""Gera os QR codes da segunda tela (SVG inline, tema molla) e embute no deck.html.

Uso:
  python3 build_qr.py                        # sessão padrão ("AULAID")
  python3 build_qr.py --session=sbtmo-2027   # outra turma (votos/perguntas separados)
  python3 build_qr.py --base=https://...     # outra URL do app

O app da segunda tela (não incluído neste kit) fica em POLL_BASE;
o parâmetro d=AULAID é o que faz o celular carregar os estudos e artigos DESTA aula.
Os SVG são desenhados localmente (segno); só a URL que carregam é aberta pelo celular.
"""
import argparse
import json
import re
from pathlib import Path

import segno

NAVY = "#010f40"
POLL_BASE = "https://AULAID-segunda-tela.vercel.app"
DECK = "AULAID"          # id da pasta decks/<id>/ no app da segunda tela


def url(caminho, session):
    u = POLL_BASE + caminho
    u += ("&" if "?" in u else "?") + f"d={DECK}"
    if session and session != "default":
        u += f"&s={session}"
    return u


def main():
    global POLL_BASE
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", default="AULAID")
    ap.add_argument("--base", default=None)
    a = ap.parse_args()
    session = (a.session or "AULAID").strip() or "AULAID"
    if a.base:
        POLL_BASE = a.base.rstrip("/")

    qrs = {
        "segunda-tela": url("/", session),
        "artigos":      url("/?tab=artigos", session),
        "nuvem":        url("/?tab=nuvem", session),
        "quiz-perfil":  url("/?tab=quiz", session),
        "quiz-q1pre":   url("/?tab=quiz", session),
        "quiz-q1pos":   url("/?tab=quiz", session),
        "quiz-q2":      url("/?tab=quiz", session),
        "quiz-q3":      url("/?tab=quiz", session),
        "quiz-mf1":     url("/?tab=quiz", session),
        "quiz-mf2":     url("/?tab=quiz", session),
        "estimativa":   url("/", session),
        "perguntar":    url("/?tab=perg", session),
    }

    base = Path(__file__).parent
    out = base / "qr"
    out.mkdir(exist_ok=True)
    svgs = {}
    for nome, u in qrs.items():
        q = segno.make(u, error="m")
        svg = q.svg_inline(scale=1, border=3, dark=NAVY, light="#ffffff")   # borda 3: zona de silencio que o decodificador exige
        m = re.search(r'width="(\d+(?:\.\d+)?)"\s+height="(\d+(?:\.\d+)?)"', svg)
        if m and "viewBox" not in svg:
            w, h = m.group(1), m.group(2)
            svg = svg.replace(m.group(0), f'width="100%" height="100%" viewBox="0 0 {w} {h}"', 1)
        (out / f"{nome}.svg").write_text(svg, encoding="utf-8")
        svgs[nome] = svg

    # mapa nome -> endereço: o modo on-line imprime a URL ao lado do QR,
    # porque quem assiste de casa digita ou cola o link, não aponta a câmera.
    (out / "urls.json").write_text(json.dumps(qrs, ensure_ascii=False, indent=1), encoding="utf-8")

    deck = base / "deck.html"
    if deck.exists():
        html = deck.read_text(encoding="utf-8")
        n = 0
        for nome, svg in svgs.items():
            pad = re.compile(r"(<!--QR:" + re.escape(nome) + r"-->).*?(<!--/QR:" + re.escape(nome) + r"-->)", re.S)
            html, k = pad.subn(lambda m: m.group(1) + svg + m.group(2), html)
            n += k
        html = re.sub(r'const POLL_SESSION\s*=\s*"[^"]*"', f'const POLL_SESSION = "{session}"', html)
        html = re.sub(r'const POLL_BASE\s*=\s*"[^"]*"', f'const POLL_BASE = "{POLL_BASE}"', html)
        deck.write_text(html, encoding="utf-8")
        print(f"deck.html: {n} QR embutidos · sessão '{session}'")

    print(f"\nQR gerados em {out} ({len(svgs)}):")
    for nome, u in qrs.items():
        print(f"  {nome:<14} {u}")
    print("\nTela de moderação:")
    print(f"  {POLL_BASE}/tela.html?d={DECK}&s={session}")
    print("\nZerar a turma antes de começar:")
    print(f"  {POLL_BASE}/api/reset-all?session={session}")


if __name__ == "__main__":
    main()
