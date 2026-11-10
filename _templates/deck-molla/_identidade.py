#!/usr/bin/env python3
"""O que e de UMA aula e nao pode vir do modelo, ao trocar o motor.

    python3 _identidade.py ler                      -> JSON numa linha
    python3 _identidade.py aplicar '<json>' <id>    -> devolve tudo aos arquivos novos

Usado so pelo atualizar-aula.sh. Roda dentro da pasta da aula.

O titulo e a PARTE CURTA: no <title> "TCTH na mielofibrose — 2026 · SEU NOME",
e "TCTH na mielofibrose". O resto (o ano, o nome) o modelo ja escreve em volta, tanto
no <title> quanto na marca-d'agua — devolver o titulo longo duplicaria o nome.
"""
import html as HTML
import json
import pathlib
import re
import sys

HEAD = pathlib.Path("_shell_head.html")
ABRIR = pathlib.Path("Abrir aula.command")

# arquivos em que AULAID vira o id curto da segunda tela
COM_ID = ("build.sh", "build_qr.py", "gerar_segunda_tela.py", "gerar_artigos.py",
          "Abrir aula.command", "controle.html")


def titulo_curto(s):
    """Corta o sufixo da casa: '... — 2026 · SEU NOME'."""
    s = re.split(r"\s+[—–]\s+|\s+·\s+", s.strip())[0]
    return s.strip()


def ler():
    saida = {}
    if HEAD.exists():
        h = HEAD.read_text(encoding="utf-8")
        m = re.search(r"<title>(.*?)</title>", h, re.S)
        if m:
            saida["titulo"] = titulo_curto(m.group(1))
    if not saida.get("titulo"):
        # sem <title>: o h1 da capa serve
        for p in sorted(pathlib.Path("parts").glob("*capa*.html")):
            m = re.search(r"<h1[^>]*>(.*?)</h1>", p.read_text(encoding="utf-8"), re.S)
            if m:
                saida["titulo"] = HTML.unescape(re.sub(r"<[^>]+>", " ", m.group(1))).strip()
                break
    if ABRIR.exists():
        m = re.search(r'VERSAO="([^"]*)"', ABRIR.read_text(encoding="utf-8"))
        if m:
            saida["versao"] = m.group(1)
    return saida


def aplicar(ident, aulaid):
    titulo = ident.get("titulo", "")
    versao = ident.get("versao", "")

    if titulo and HEAD.exists():
        # o modelo escreve TITULO DA AULA no <title> e na marca-d'agua; um replace serve aos dois
        HEAD.write_text(HEAD.read_text(encoding="utf-8").replace("TITULO DA AULA", titulo),
                        encoding="utf-8")

    # o mesmo marcador vira o kicker da segunda tela, no celular da plateia
    if titulo:
        for nome in ("gerar_segunda_tela.py", "gerar_artigos.py"):
            g = pathlib.Path(nome)
            if g.exists():
                g.write_text(g.read_text(encoding="utf-8").replace("TITULO DA AULA", titulo),
                             encoding="utf-8")

    if aulaid:
        for nome in COM_ID:
            p = pathlib.Path(nome)
            if p.exists():
                p.write_text(p.read_text(encoding="utf-8").replace("AULAID", aulaid), encoding="utf-8")

    if ABRIR.exists():
        c = ABRIR.read_text(encoding="utf-8")
        if titulo:
            c = c.replace("TITULO DA AULA", titulo)
        # sem versao salva, a aula abre inteira — que e o estado de quem nunca usou a tecla O
        c = c.replace('VERSAO="NOME-DA-VERSAO"', 'VERSAO="%s"' % versao)
        ABRIR.write_text(c, encoding="utf-8")

    print("identidade: titulo=%r versao=%r id=%r" % (titulo, versao, aulaid))
    if not titulo:
        print("AVISO: nao achei o titulo da aula — escreva a mao em _shell_head.html")


if __name__ == "__main__":
    if sys.argv[1] == "ler":
        print(json.dumps(ler(), ensure_ascii=False))
    else:
        aplicar(json.loads(sys.argv[2]), sys.argv[3] if len(sys.argv) > 3 else "")
