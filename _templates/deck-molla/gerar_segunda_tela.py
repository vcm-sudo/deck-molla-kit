#!/usr/bin/env python3
"""Gera os tres JSON da segunda tela desta aula, direto das laminas.

    /usr/local/bin/python3 gerar_segunda_tela.py [--destino <pasta do app>]

  cards.json   — um cartao "Ao vivo" por lamina de estudo, montado a partir da
                 .ficha (desenho, N, idade, seguimento, desfechos), da leitura-chave
                 e do rodape. Tambem escreve data-card="<part>" na <section>, que e
                 o que faz o deck publicar o cartao certo.
  artigos.json — copiado do que gerar_artigos.py produziu.
  poll.json    — quiz, nuvem e estimativa, lidos das proprias laminas.

Sem --destino, escreve em ./segunda-tela/ para conferencia. Publicar e passo
separado (e precisa de autorizacao): copiar para o app e rodar o deploy.
"""
import argparse
import html
import json
import pathlib
import re

BASE = pathlib.Path(__file__).parent
PARTS = BASE / "parts"
TAG = re.compile(r"<[^>]+>")
DECK_ID = "AULAID"


def limpo(s):
    # <small> e <b> colados ao valor viravam "5634-68" e "12,5 m1,6-35,7" no celular:
    # cada tag que fecha vira um espaco antes de sumir
    s = re.sub(r"</(small|b|i|em|span|sup|sub)>", " ", s)
    s = re.sub(r"<(small|b|i|em|span|sup|sub)[^>]*>", " ", s)
    s = s.replace("<br>", " ").replace("<br/>", " ")
    s = re.sub(r"\s+", " ", TAG.sub("", s)).strip()
    s = html.unescape(s)
    return re.sub(r"\s+([,.;:!?)])", r"\1", s)


VERSAO = ""          # preenchido em main() por --versao
GABARITO = {}        # modo competicao: {quiz: "B"} — preenchido por poll()


def ordem():
    """Nomes das laminas na ordem em que serao apresentadas.

    Com --versao, segue a selecao salva no organizador (versoes.json): a mesma
    ordem e os mesmos ocultos que vao ao palco."""
    arq = BASE / "order.txt"
    nomes = []
    for linha in arq.read_text(encoding="utf-8").splitlines():
        n = linha.strip()
        if n and not n.startswith("#"):
            nomes.append(n)
    if not VERSAO:
        return nomes
    vj = BASE / "versoes.json"
    if not vj.exists():
        raise SystemExit(f"{vj} nao existe — exporte a versao pelo organizador (tecla O)")
    vs = json.loads(vj.read_text(encoding="utf-8"))
    if VERSAO not in vs:
        raise SystemExit(f"versao '{VERSAO}' nao esta em versoes.json. Ha: {', '.join(vs) or '(nenhuma)'}")
    v = vs[VERSAO]
    ocultas, sel = v.get("hidden") or [], v.get("order") or []
    return [nomes[i] for i in sel
            if i < len(nomes) and not (i < len(ocultas) and ocultas[i])]


def cards():
    saida, marcadas = {}, 0
    for nome in ordem():
        p = PARTS / f"{nome}.html"
        if not p.exists():
            continue
        h = p.read_text(encoding="utf-8")
        if '<div class="ficha"' not in h:
            continue
        # os pares rot/val so existem dentro da ficha: varrer o arquivo inteiro evita
        # ter de casar o </div> certo (a ficha contem um <div> por item).
        itens = []
        for rot, val in re.findall(r'<span class="rot">(.*?)</span>\s*<span class="val">(.*?)</span>', h, re.S):
            r, v = limpo(rot), limpo(val)
            if v and v != "—":
                itens.append(f"{r}: {v}")
        if not itens:
            continue
        h1 = re.search(r"<h1>(.*?)</h1>", h, re.S)
        sub = re.search(r'<div class="sub">(.*?)</div>', h, re.S)
        leit = re.search(r'<div class="t">(.*?)</div>', h, re.S)
        fonte = re.search(r'<span class="txt">(.*?)</span>', h, re.S)
        selo = re.search(r"badge-(pdf|abs|did)", h)
        # a lamina pode ja trazer um data-card de antes (ids proprios, varias laminas
        # para o mesmo estudo). E ele que o deck publica, entao e ele que vira a chave;
        # usar o nome da part deixaria o cartao orfao no celular.
        mc = re.search(r'data-card="([^"]+)"', h)
        chave = mc.group(1) if mc else nome
        saida[chave] = {
            "title": limpo(h1.group(1)) if h1 else nome,
            "tag": limpo(sub.group(1)) if sub else "",
            "arms": itens,
            "leitura": limpo(leit.group(1)) if leit else "",
            "fonte": limpo(fonte.group(1)) if fonte else "",
            "selo": {"pdf": "Artigo publicado", "abs": "Dados de congresso",
                     "did": "Didático"}.get(selo.group(1) if selo else "", ""),
        }
        if not mc:
            h2 = re.sub(r"<section ", f'<section data-card="{nome}" ', h, count=1)
            p.write_text(h2, encoding="utf-8")
            marcadas += 1
    return saida, marcadas


def poll():
    q = {"meta": {"kicker": "TITULO DA AULA",
                  "titulo": "SEU NOME · 2026"},
         "quiz": {}}
    for nome in ordem():                              # so o que esta visivel no deck
        p = PARTS / f"{nome}.html"
        if not p.exists():
            continue
        h = p.read_text(encoding="utf-8")
        mq = re.search(r'data-quiz="([^"]+)"', h)
        if mq:
            qid = mq.group(1)
            titulo = re.search(r"<h2[^>]*>(.*?)</h2>", h, re.S)
            kick = re.search(r'<div class="kick">(.*?)</div>', h, re.S)
            afirm = re.search(r'<div class="afirm">(.*?)</div>', h, re.S)
            opts = [limpo(t) for t in re.findall(r'<div class="txt">(.*?)</div>', h, re.S)]
            # data-short na .opt da a versao curta que cabe na barra do celular;
            # sem ela, a opcao longa era truncada com reticencias
            curtos = re.findall(r'<div class="opt"[^>]*data-short="([^"]*)"', h)
            if not opts and afirm:                       # mito ou fato
                opts = ["Mito", "Fato"]
            if not opts:
                continue
            # modo competicao: a resposta certa vai para o GABARITO (so o servidor le),
            # nunca para o poll.json, que e publico e o celular baixa
            sec = re.search(r'<section\b[^>]*data-quiz="' + re.escape(qid) + r'"[^>]*>', h)
            if sec and re.search(r'\sdata-competicao\b', sec.group(0)):
                mc = re.search(r'data-correta="([A-Ha-h])"', sec.group(0))
                if not mc:
                    raise SystemExit(f"{nome}: data-competicao sem data-correta=\"<letra>\"")
                GABARITO[qid] = mc.group(1).upper()
            q["quiz"][qid] = {
                "label": limpo(kick.group(1)) if kick else qid,
                "title": limpo(kick.group(1)) if kick else qid,
                "q": limpo((afirm or titulo).group(1)) if (afirm or titulo) else "",
                "opts": opts,
                "short": curtos if len(curtos) == len(opts) else
                         [o if len(o) <= 26 else o[:24].rstrip() + "…" for o in opts],
            }
        mw = re.search(r'data-wordq="([^"]+)"', h)
        if mw:
            q["nuvem"] = mw.group(1).replace("&quot;", '"')
        # o app le guess como MAPA id -> {title,q,min,max,step,unit}. Como objeto unico
        # com campo "id", o slider nunca aparecia no celular.
        mg = re.search(r'data-guess="([^"]+)"[^>]*data-min="([\d.]+)"[^>]*data-max="([\d.]+)"', h)
        if mg:
            titulo = re.search(r"<h2[^>]*>(.*?)</h2>", h, re.S)
            kick = re.search(r'<div class="kick">(.*?)</div>', h, re.S)
            num = lambda s: float(s) if "." in s else int(s)
            q.setdefault("guess", {})[mg.group(1)] = {
                "title": limpo(kick.group(1)) if kick else "Estimativa",
                "q": limpo(titulo.group(1)) if titulo else "",
                "min": num(mg.group(2)), "max": num(mg.group(3)),
                "step": 1, "unit": "%"}
    return q


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--destino", default=str(BASE / "segunda-tela"),
                    help="pasta onde escrever (no app: <app>/decks/AULAID)")
    ap.add_argument("--versao", default="", help="nome da versao salva no organizador")
    a = ap.parse_args()
    global VERSAO
    VERSAO = a.versao
    dest = pathlib.Path(a.destino).expanduser()
    dest.mkdir(parents=True, exist_ok=True)

    c, marcadas = cards()
    (dest / "cards.json").write_text(json.dumps(c, ensure_ascii=False, indent=1), encoding="utf-8")

    # falas.json — o roteiro do apresentador, para a tela presenter.html
    fal = BASE / "roteiro-falas.json"
    if fal.exists():
        todas = json.loads(fal.read_text(encoding="utf-8"))
        so_visiveis = {n: todas[n] for n in ordem() if n in todas}
        (dest / "falas.json").write_text(
            json.dumps(so_visiveis, ensure_ascii=False, indent=1), encoding="utf-8")

    # topicos.json — a mesma fala em topicos curtos, que e o que se le de relance no palco
    top = BASE / "roteiro-topicos.json"
    if top.exists():
        tt = json.loads(top.read_text(encoding="utf-8"))
        (dest / "topicos.json").write_text(
            json.dumps({n: tt[n] for n in ordem() if n in tt}, ensure_ascii=False, indent=1),
            encoding="utf-8")

    art = BASE / "artigos.json"
    if art.exists():
        (dest / "artigos.json").write_text(art.read_text(encoding="utf-8"), encoding="utf-8")

    p = poll()
    if GABARITO:
        p["competicao"] = {"quizzes": list(GABARITO)}
        # gabarito.json NAO vai para decks/<id>/ (seria publico): vai para
        # <app>/api/_gabaritos/<id>.json, que so as funcoes do servidor leem
        (dest / "gabarito.json").write_text(json.dumps(GABARITO, indent=1), encoding="utf-8")
    (dest / "poll.json").write_text(json.dumps(p, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"deck id: {DECK_ID}")
    print(f"cards.json  : {len(c)} cartões de estudo ({marcadas} lâminas ganharam data-card)")
    print(f"poll.json   : {len(p['quiz'])} quizzes"
          f"{' + nuvem' if 'nuvem' in p else ''}{' + estimativa' if 'guess' in p else ''}")
    print(f"artigos.json: {'copiado' if art.exists() else 'FALTA — rode gerar_artigos.py'}")
    if GABARITO:
        print(f"competicao  : {len(GABARITO)} perguntas valem pontos → copiar gabarito.json para "
              f"<app>/api/_gabaritos/{DECK_ID}.json (NUNCA para decks/)")
    print(f"\nescrito em {dest}")
    print("Publicar (pede autorização): copiar para <app>/decks/AULAID/ e rodar o deploy.")


if __name__ == "__main__":
    main()
