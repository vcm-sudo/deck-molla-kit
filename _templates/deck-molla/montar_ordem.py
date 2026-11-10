#!/usr/bin/env python3
"""Monta o order.txt da aula a partir do plano de blocos.

    /usr/local/bin/python3 montar_ordem.py

O plano abaixo e a ordem de palco. As laminas de conteudo entram pelo numero do
Keynote original (o prefixo NN- do nome do arquivo), entao desdobramentos (NN-a,
NN-b) entram juntos e na ordem alfabetica. Laminas que existem em parts/ mas nao
estao no plano sao acrescentadas no fim, comentadas, para nao sumirem.
"""
import pathlib
import re
import sys

BASE = pathlib.Path(__file__).parent
PARTS = BASE / "parts"

SECOES_KEYNOTE = set()   # numeros de laminas do PPTX/Keynote original que viraram divisoria
OCULTAS = set()          # numeros que entram ocultos

# Exemplo: blocos e a ordem de palco. Itens podem ser nome de part ou numero do original.
PLANO = [
    ("ABERTURA", ["capa", "aviso", "segunda", "agenda"]),
    ("1 · BLOCO", ["sec-bloco1", 1, 2, 3]),
    ("FECHO", ["levar", "perguntas", "despedida"]),
]


def por_numero(n):
    """Todos os parts cujo prefixo numerico e n, em ordem (NN, NN-a, NN-b...)."""
    achados = sorted(p.stem for p in PARTS.glob(f"{n:02d}-*.html"))
    return achados


def main():
    if not PARTS.exists():
        sys.exit("parts/ nao existe")
    existentes = {p.stem for p in PARTS.glob("*.html")}
    usados, linhas, faltando = set(), [], []

    linhas.append("# ORDEM DOS SLIDES — # no inicio oculta. Rode ./build.sh depois de editar.")
    linhas.append("# Gerado por montar_ordem.py; o plano dos blocos esta la dentro.")
    for titulo, itens in PLANO:
        linhas.append("")
        linhas.append(f"# ===== {titulo}")
        for item in itens:
            if isinstance(item, int):
                if item in SECOES_KEYNOTE:
                    continue
                nomes = por_numero(item)
                if not nomes:
                    faltando.append(f"lamina {item} do Keynote")
                    continue
                for nome in nomes:
                    usados.add(nome)
                    linhas.append(("#" if item in OCULTAS else "") + nome)
            else:
                if item in existentes:
                    usados.add(item)
                    linhas.append(item)
                else:
                    faltando.append(item)

    sobrando = sorted(existentes - usados)
    if sobrando:
        linhas.append("")
        linhas.append("# ===== FORA DO PLANO (acrescentadas aqui para nao se perderem)")
        for nome in sobrando:
            linhas.append("#" + nome)

    (BASE / "order.txt").write_text("\n".join(linhas) + "\n", encoding="utf-8")

    visiveis = sum(1 for l in linhas if l and not l.startswith("#"))
    ocultas = sum(1 for l in linhas if l.startswith("#") and not l.startswith("# "))
    print(f"order.txt: {visiveis} laminas visiveis, {ocultas} ocultas")
    if faltando:
        print("\nNAO ENCONTRADAS em parts/ (o plano pede, o arquivo nao existe):")
        for x in faltando:
            print("  " + x)
    if sobrando:
        print(f"\nFORA DO PLANO ({len(sobrando)}), entraram ocultas no fim:")
        for x in sobrando:
            print("  " + x)


if __name__ == "__main__":
    main()
