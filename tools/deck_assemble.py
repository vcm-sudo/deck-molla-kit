#!/usr/bin/env python3
"""Monta um deck HTML a partir de _shell_head.html + parts/*.html + _shell_tail.html.

A ordem (e o que fica oculto) vem de order.txt: uma linha por slide, com o nome do
arquivo em parts/ sem extensao; linhas iniciadas por # sao ignoradas (slide oculto).
Cada <section> recebe data-id/data-name com o nome da part, que e o que o modo edicao
(tecla E) usa para ocultar/reordenar e para exportar a ordem de volta.

Uso:
    python3 tools/deck_assemble.py LMA/lma-2026
    python3 tools/deck_assemble.py LMA/lma-2026 --saida deck.html
"""
import argparse
import re
import sys
from pathlib import Path

SECTION_RE = re.compile(r"<section\b")


def montar(base: Path, saida: Path) -> int:
    head = (base / "_shell_head.html").read_text(encoding="utf-8")
    tail = (base / "_shell_tail.html").read_text(encoding="utf-8")
    ordem = base / "order.txt"

    nomes = []
    for linha in ordem.read_text(encoding="utf-8").splitlines():
        nome = linha.strip()
        if not nome or nome.startswith("#"):
            continue
        nomes.append(nome)

    corpo = []
    for nome in nomes:
        arq = base / "parts" / f"{nome}.html"
        if not arq.exists():
            sys.exit(f"erro: parts/{nome}.html nao existe (citado em order.txt)")
        html = arq.read_text(encoding="utf-8")
        if not SECTION_RE.search(html):
            sys.exit(f"erro: parts/{nome}.html nao tem <section>")
        html = SECTION_RE.sub(
            f'<section data-id="{nome}" data-name="{nome}"', html, count=1
        )
        corpo.append(html.rstrip("\n"))

    saida.write_text(head + "\n" + "\n\n".join(corpo) + "\n" + tail, encoding="utf-8")
    return len(nomes)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("pasta", help="pasta do deck (com _shell_head.html, parts/, order.txt)")
    p.add_argument("--saida", default="deck.html", help="nome do arquivo gerado")
    a = p.parse_args()

    base = Path(a.pasta).expanduser().resolve()
    saida = base / a.saida
    n = montar(base, saida)
    print(f"{saida.name}: {n} slides montados")


if __name__ == "__main__":
    main()
