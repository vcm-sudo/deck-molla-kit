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

# Laminas do Keynote que eram titulo de bloco e viraram divisoria propria:
# 13, 16, 20, 33, 37, 43, 62, 64 — nao entram como conteudo.
SECOES_KEYNOTE = {13, 16, 20, 33, 37, 43, 62, 64}
# Estavam marcadas como puladas no Keynote — entram ocultas.
OCULTAS = {3, 11, 23, 67}
# 06-tabela-escores-kroger (imagem ilegivel) foi substituida por 06-a/b/c nativas; fica oculta.

PLANO = [
    ("ABERTURA", ["capa", "01-evento", "aviso", "segunda", "nuvem", "perfil", "imp-unica", "agenda"]),
    ("1 · QUANDO TRANSPLANTAR", ["sec-quando", 3, 5, "06-a-escores-pontos", "06-b-escores-risco", "06-c-escores-tratamento", 7, 8, 9, 10, 11, "12-a-dipss-rr",
                                 "big-sem-tmo", "n-hctfs-itens", "n-fragilidade", "imp-janela"]),
    ("2 · DESFECHOS", ["sec-desfechos", 14, 15, "syn-nrm-series"]),
    ("3 · PRE-TCTH", ["sec-pre", 17, 18, 19, "n-deferasirox", "mf1", "mf1-resposta"]),
    ("4 · ESPLENOMEGALIA", ["sec-baco", 21, 22, 23, "n-svr35-panorama", "n-sentry",
                            26, 27, 28, 29, 30, 31, 32, "n-esplen-vs-irradiacao", "big-esplenectomia"]),
    ("5 · iJAK NO TCTH", ["sec-ijak", 38, 39, 40, 41, 42, "n-ruxo-profilaxia", "n-momelo-racional", "n-momelo-tcth", "q2", "q2-resposta", "imp-ijak"]),
    ("6 · DOADOR E CONDICIONAMENTO", ["sec-doador", 44, 45, "syn-doador", "n-hla-vs-idade-doador",
                                      "n-idade-doador-haplo", 46, 47, 48, 49, "big-doador", 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60,
                                      "syn-condicionamento", 61]),
    ("7 · CITOPENIAS E FALHA DE ENXERTIA", ["sec-citopenias", 34, 35, 36,
                                            "est-enxertia", "est-enxertia-resposta",
                                            "n-gf-incidencia", "n-gf-preco", "n-tbi-enxertia", "n-eltrombopag",
                                            "big-enxertia"]),
    ("8 · DOENCA RESIDUAL", ["sec-drm", 63, "imp-drm"]),
    ("9 · CONDUTA", ["sec-conduta", 66, 67, "syn-decisao", "q1pos", "levar", "big-fecho",
                     "perguntas", "despedida"]),
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
