#!/usr/bin/env python3
"""Extrai as referencias das laminas e gera ARTIGOS.md + artigos.json (segunda tela).

    /usr/local/bin/python3 gerar_artigos.py

Le o rodape <footer class="fonte"> de cada part, separa as citacoes por " · ",
agrupa por bloco (definido pela divisoria .secao que precede a lamina no order.txt)
e escreve:
  - ARTIGOS.md — indice legivel, com o selo de evidencia de cada lamina
  - artigos.json — no formato do app da segunda tela (decks/<id>/artigos.json)

O campo `busca` do JSON leva o termo a procurar no PubMed quando o titulo exato
nao esta na lamina (o rodape do padrao palco tras so autores/revista/ano).
"""
import html as HTML
import json
import re
import pathlib
from collections import OrderedDict

BASE = pathlib.Path(__file__).parent
TAG_RE = re.compile(r"<[^>]+>")
FOOT_RE = re.compile(r'<footer class="fonte">(.*?)</footer>', re.S)
BADGE_RE = re.compile(r'badge-(pdf|abs|did)')
H1_RE = re.compile(r"<h1>(.*?)</h1>", re.S)
H2_RE = re.compile(r"<h2[^>]*>(.*?)</h2>", re.S)

SELO = {"pdf": "Artigo publicado", "abs": "Dados de congresso", "did": "Didático"}


def limpo(s):
    return re.sub(r"\s+", " ", TAG_RE.sub("", s)).strip()


def ordem():
    """Lista (nome, bloco) na ordem do deck, bloco vindo da ultima divisoria."""
    arq = BASE / "order.txt"
    if not arq.exists():
        return [(p.stem, "Aula") for p in sorted((BASE / "parts").glob("*.html"))]
    saida, bloco = [], "Abertura"
    for linha in arq.read_text(encoding="utf-8").splitlines():
        nome = linha.strip()
        if not nome or nome.startswith("#"):
            continue
        p = BASE / "parts" / f"{nome}.html"
        if p.exists() and "slide secao" in p.read_text(encoding="utf-8"):
            h2 = H2_RE.search(p.read_text(encoding="utf-8"))
            bloco = limpo(h2.group(1)) if h2 else nome
            continue
        saida.append((nome, bloco))
    return saida


def main():
    grupos = OrderedDict()
    vistas = {}
    for nome, bloco in ordem():
        p = BASE / "parts" / f"{nome}.html"
        if not p.exists():
            continue
        h = p.read_text(encoding="utf-8")
        m = FOOT_RE.search(h)
        if not m:
            continue
        badge = BADGE_RE.search(m.group(1))
        selo = SELO.get(badge.group(1), "") if badge else ""
        txt = re.search(r'<span class="txt">(.*?)</span>', m.group(1), re.S)
        if not txt:
            continue
        titulo = limpo(H1_RE.search(h).group(1)) if H1_RE.search(h) else nome
        # rodape curto com varios autores e uma fonte so ("Bailly C · Bravo Solarte DC. ASH 2026"):
        # o autor sem ano herda a fonte do item seguinte que a traz
        partes = [c.strip(" .") for c in limpo(txt.group(1)).split(" · ")]
        for i, c in enumerate(partes):
            if re.fullmatch(r"[A-ZÀ-Ý][\w'’\-]+( [A-ZÀ-Ý][\w'’\-]+)*( [A-Z]{1,3})?", c):
                for d in partes[i + 1:]:
                    if re.search(r"\b(19|20)\d\d\b", d) and ". " in d:
                        partes[i] = c + ". " + d.split(". ", 1)[1]
                        break
        for cit in partes:
            if not cit or len(cit) < 8:
                continue
            # so entra o que e citacao: precisa de ano e de autor/revista.
            # avisos de rodape ("Declaracao completa...", "Aula independente...") ficam de fora.
            if not re.search(r"\b(19|20)\d\d\b", cit):
                continue
            # formato molla curto: "Sobrenome I. Revista Ano" (sem "et al") tambem conta
            if ("et al" not in cit and "Handbook" not in cit and "Slide do autor" not in cit
                    and not re.match(r"^[A-ZÀ-Ý][\w'’\-]+( [A-ZÀ-Ý][\w'’\-]+)*( [A-Z]{1,3})?\. .*\b(19|20)\d\d\b", cit)):
                continue
            chave = cit.lower()
            if chave in vistas:
                vistas[chave]["laminas"].append(titulo)
                continue
            item = {"ref": cit, "selo": selo, "laminas": [titulo], "bloco": bloco}
            vistas[chave] = item
            grupos.setdefault(bloco, []).append(item)

    # ARTIGOS.md
    linhas = ["# Referências da aula — TITULO DA AULA", "",
              "Uma linha por publicação citada, na ordem em que aparece na aula.",
              "O selo é o nível de evidência mostrado à plateia, não a auditoria.", ""]
    total = 0
    for bloco, itens in grupos.items():
        linhas.append(f"## {bloco}")
        linhas.append("")
        for it in itens:
            total += 1
            sel = f" `{it['selo']}`" if it["selo"] else ""
            linhas.append(f"- {it['ref']}{sel}")
        linhas.append("")
    linhas.append(f"**{total} referências em {len(grupos)} blocos.**")
    (BASE / "ARTIGOS.md").write_text("\n".join(linhas) + "\n", encoding="utf-8")

    # artigos.json — o app espera {"grupos":[{"nome":..,"itens":[{"t","r","oa","busca"}]}]}.
    # Com "grupo"/"ref" o fetch resolvia mas d.grupos era undefined e a aba caia no catch:
    # "Nao consegui carregar a lista de artigos".
    saida = {"grupos": []}
    for bloco, itens in grupos.items():
        lista = []
        for it in itens:
            ref = re.sub(r"\s+", " ", it["ref"]).strip()
            autor = ref.split(".")[0].strip()          # "Kroger N, et al"
            revista_ano = ".".join(ref.split(".")[1:]).strip().rstrip(".")
            lista.append({
                # o titulo mostrado e a lamina onde a referencia aparece: da contexto
                # a quem folheia no celular, em vez de repetir a citacao duas vezes
                "t": HTML.unescape(it["laminas"][0]) if it.get("laminas") else autor,
                "r": ref,
                "oa": False,
                "selo": it.get("selo", ""),
                "busca": autor.replace(", et al", ""),
            })
        saida["grupos"].append({"nome": bloco, "itens": lista})
    (BASE / "artigos.json").write_text(json.dumps(saida, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"ARTIGOS.md e artigos.json: {total} referências, {len(grupos)} blocos")


if __name__ == "__main__":
    main()
