#!/usr/bin/env python3
"""Portao de QA estrutural das laminas (parts/*.html), antes de montar o deck.

    /usr/local/bin/python3 qa_deck.py

Checa, lamina a lamina:
  1. HTML — exatamente 1 <section>, balanco de <div>, sem <html>/<head>/<body>,
     sem estilos de runtime (transform: scale, transition-delay, data-reveal="")
  2. Tokens de cor var(--x) que nao existem no motor nem no <style> local
  3. Estilo local nao prefixado por [data-id="<nome-do-part>"] (vaza para o deck todo)
  4. Rodape de fonte presente, e selo (badge-pdf / badge-abs / badge-did / badge-reg) em lamina de conteudo
  5. Palavras proibidas: "Siglas:", "MSR", "geriatr", "Publico:", coloquialismo
  6. Titulo muito longo (> 62 caracteres quebra em duas linhas)
  7. Figuras referenciadas que nao existem
  8. order.txt — toda lamina citada existe, toda lamina existente esta citada
  9. Leitura-chave: sem rotulo visivel e ate 22 palavras (a ressalva .ress conta a parte)
"""
import re
import pathlib
import sys

BASE = pathlib.Path(__file__).parent
PARTS = sorted((BASE / "parts").glob("*.html"))

PROIBIDAS = [
    (r"Siglas\s*:", "bloco de siglas no rodape"),
    (r"\bMSR\b", "usar NRM, nao MSR"),
    # falar COM a plateia ("para geriatras", "o geriatra deve") e nao o profissional
    # que compoe a equipe nem o nome da revista (J Geriatr Oncol) no rodape
    (r"\bgeriatras\b|\bgeriatria\b|\b(para|ao|aos)\s+(o\s+)?geriatra\b", "mencao ao publico"),
    (r"P[uú]blico\s*:", "mencao ao publico"),
    (r"\bvamos ver\b|\bcomo eu disse\b|\bcomo falei\b|\bna real\b", "coloquialismo/meta-comentario"),
]
RUNTIME = [
    (r'transform:\s*scale\(', "estilo de runtime (transform: scale)"),
    (r"transition-delay:", "estilo de runtime (transition-delay)"),
    (r'data-reveal=""', 'data-reveal="" de runtime'),
]


import html as HTML

TAG_DIV = re.compile(r"<(/?)div\b[^>]*>", re.I)


def _bloco(h, i):
    """(inicio, fim) do conteudo do <div ...> que comeca em i, <div> internas balanceadas."""
    ini = TAG_DIV.match(h, i).end()
    nivel = 1
    for t in TAG_DIV.finditer(h, ini):
        nivel += -1 if t.group(1) else 1
        if nivel == 0:
            return ini, t.start()
    return ini, len(h)


def _palavras(s):
    """Palavras de verdade: tag inline nao separa numero de unidade, pontuacao nao conta."""
    s = re.sub(r"</?(b|i|em|span|sup|sub|small)[^>]*>", "", s)
    s = re.sub(r"<[^>]+>", " ", s)
    return [w for w in HTML.unescape(s).split() if re.search(r"[0-9A-Za-zÀ-ÿ]", w)]


def leituras(h):
    """(palavras da leitura, palavras da ressalva, tem rotulo) de cada bloco .leitura."""
    out = []
    for m in re.finditer(r'<div class="leitura"[^>]*>', h):
        a, b = _bloco(h, m.start())
        dentro = h[a:b]
        mk = re.search(r'<div class="k"[^>]*>', dentro)
        rotulo = False
        if mk:
            ka, kb = _bloco(dentro, mk.start())
            rotulo = bool(_palavras(dentro[ka:kb]))
        mt = re.search(r'<div class="t"[^>]*>', dentro)
        if not mt:
            continue
        ta, tb = _bloco(dentro, mt.start())
        txt = dentro[ta:tb]
        ress = ""
        mr = re.search(r'<div class="ress"[^>]*>', txt)
        if mr:
            ra, rb = _bloco(txt, mr.start())
            ress = txt[ra:rb]
            txt = txt[:mr.start()] + txt[rb:]
        out.append((len(_palavras(txt)), len(_palavras(ress)), rotulo))
    return out


def main():
    head = (BASE / "_shell_head.html").read_text(encoding="utf-8")
    # classes que o motor posiciona com position:absolute — nome reservado
    # nome curto (<= 4) que o motor posiciona de forma absoluta: reusar esse nome numa
    # lamina faz o bloco herdar left/top/right/bottom do deck e estourar o palco (caso .fx)
    MOTOR_RESERVADO = set()
    for m in re.finditer(r"(?:^|[\s,}])\.([a-zA-Z][\w-]*)\s*\{([^}]*)\}", head, re.M):
        if len(m.group(1)) <= 4 and "position:absolute" in m.group(2).replace(" ", ""):
            MOTOR_RESERVADO.add(m.group(1))
    tokens = set(re.findall(r"(--[a-z0-9-]+)\s*:", head))
    erros, avisos = [], []

    nomes_parts = set()
    for p in PARTS:
        nome = p.stem
        nomes_parts.add(nome)
        h = p.read_text(encoding="utf-8")
        E = lambda m: erros.append(f"{p.name}: {m}")
        A = lambda m: avisos.append(f"{p.name}: {m}")

        # 1. HTML
        # um valor de atributo (data-nota, alt, title) pode CITAR uma tag como texto
        # — "os <div data-passo> vazios sao os gatilhos". A contagem estrutural olha o
        # HTML com os valores de atributo esvaziados, senao acusa desbalanceamento falso.
        hh = re.sub(r'="[^"]*"', '=""', h)
        if hh.count("<section") != 1 or hh.count("</section>") != 1:
            E(f"{hh.count('<section')} <section> / {hh.count('</section>')} </section> (deve ser 1 e 1)")
        if hh.count("<div") != hh.count("</div>"):
            E(f"<div> {hh.count('<div')} x </div> {hh.count('</div>')} — desbalanceado")
        for tag in ("<html", "<head", "<body"):
            if tag in h.lower():
                E(f"contem {tag}> (o part e so a <section>)")
        for rx, msg in RUNTIME:
            if re.search(rx, h):
                E(msg)

        # 2. tokens
        locais = set(re.findall(r"(--[a-z0-9-]+)\s*:", h))
        usados = set(re.findall(r"var\((--[a-z0-9-]+)\)", h))
        for t in sorted(usados - tokens - locais):
            E(f"token inexistente {t}")

        # 2b. nome curto de classe local que ja existe no motor. Nomes curtos (.fx, .nm,
        # .sv) sao os que se reusam sem querer; se o motor posiciona a classe, o bloco
        # estoura a lamina. Nomes longos (.figwrap, .leitura, .ficha) sao componentes do
        # motor que as laminas refinam de proposito — esses nao entram aqui.
        for sel in sorted(set(re.findall(r'\[data-id="[^"]*"\]\s+\.([a-zA-Z][\w-]*)', h))):
            if sel in MOTOR_RESERVADO:
                # so e problema se a regra local NAO redefine position: nesse caso o bloco
                # herda o left/top/right/bottom do motor e estoura o palco (caso .fx)
                regra = re.search(r'\[data-id="[^"]*"\]\s+\.' + re.escape(sel) + r'\s*\{([^}]*)\}', h)
                if regra and "position:" not in regra.group(1).replace(" ", ""):
                    A(f"classe local .{sel} reusa nome do motor sem redefinir position — se a lâmina estourar, e isso (prefixe: .x-{sel})")

        # 3. estilo local sem prefixo
        for bloco in re.findall(r"<style>(.*?)</style>", h, re.S):
            for regra in re.findall(r"([^{}]+)\{", bloco):
                sel = regra.strip().splitlines()[-1].strip()
                if not sel or sel.startswith("@") or sel.startswith("/*"):
                    continue
                if f'[data-id="{nome}"]' not in sel:
                    A(f"regra local sem prefixo [data-id=\"{nome}\"]: {sel[:60]}")

        # 4. rodape
        tem_secao = 'class="slide secao' in h or 'class="slide capa' in h or 'class="slide despedida' in h
        tem_impacto = "slide impacto" in h or "slide quiz" in h
        # data-semfonte = lamina de moldura (evento, agenda, aviso): nao afirma dado, nao cita fonte
        sem_fonte = "data-semfonte" in h
        if not tem_secao and not tem_impacto and not sem_fonte:
            if "footer" not in h:
                E("sem <footer class=\"fonte\">")
            elif not re.search(r"badge-(pdf|abs|did|reg)", h) and "Slide do autor" not in h:
                A("rodape sem selo de evidencia (badge-pdf/abs/did)")
        # 4b. o rodape e PROCEDENCIA, nunca comentario sobre a propria lamina.
        # Vale so: "Autor X, et al. Revista. Ano" (ou Handbook, ou "Slide do autor").
        mtxt = re.search(r'<span class="txt">(.*?)</span>', h, re.S)
        if mtxt:
            t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", mtxt.group(1))).strip()
            ok_fonte = (re.search(r"\b(19|20)\d\d\b", t) and ("et al" in t or "Handbook" in t
                        or re.search(r"\b[A-ZÀ-Ý][\w'’-]+ [A-ZÀ-Ý]{1,3}\.\s", t))) \
                       or re.search(r"ClinicalTrials\.gov\s+NCT\d+", t) \
                       or re.search(r"\bANVISA\b|prescribing information|package insert|bula do produto", t, re.I) \
                       or t == "Slide do autor"
            # 4c. o rodape CITA, nunca comenta: nada de "sintese das laminas", "redesenhado
            # a partir de", "coortes independentes", "nao e comparacao direta".
            COMENTARIO = r"(?i)(s[ií]ntese das l[âa]minas|nesta aula|desta aula|redesenhad|reconstru[ií]d|" \
                         r"coortes independentes|estudos independentes|sem compara[çc][ãa]o direta|" \
                         r"n[ãa]o [ée] compara[çc][ãa]o|vale s[óo]|nunca entre|n[úu]meros repetidos|" \
                         r"com a proced[êe]ncia|cada linha vem)"
            if t and re.search(COMENTARIO, t):
                E(f"rodape explica em vez de citar: {t[:70]}")
            if t and not ok_fonte:
                E(f"rodape nao e citacao (comentario sobre a lamina): {t[:70]}")

        # 9. leitura-chave: e a faixa escura do rodape, nao um paragrafo. O rotulo
        # ("Leitura-chave:") saiu do padrao — o bloco se explica sozinho. Alvo 15 a 20
        # palavras; a ressalva de validade (.ress) conta a parte e nao se corta.
        for n_leit, n_ress, rotulo in leituras(h):
            if rotulo:
                E("leitura-chave com rotulo visivel (o padrao nao tem titulo na faixa)")
            if n_leit > 22:
                A(f"leitura-chave com {n_leit} palavras (alvo 15 a 20)")
            if n_ress > 20:
                A(f"ressalva da leitura com {n_ress} palavras (encurte ou vire chip)")

        # 5. proibidas
        for rx, msg in PROIBIDAS:
            if re.search(rx, h, re.I):
                E(msg)

        # 6. titulo
        m = re.search(r"<h1>(.*?)</h1>", h, re.S)
        if m:
            # o rotulo <small> dentro do h1 e' um subtitulo de linha propria (mesmo papel
            # do .sub separado) -- nao conta para o limite de caracteres do titulo principal.
            h1_sem_small = re.sub(r"<small>.*?</small>", "", m.group(1), flags=re.S)
            t = re.sub(r"<[^>]+>", "", h1_sem_small).strip()
            if len(t) > 62:
                A(f"titulo com {len(t)} caracteres (quebra em 2 linhas): {t[:70]}")

        # 7. figuras
        for src in re.findall(r'src="(img/[^"]+)"', h):
            if not (BASE / src).exists():
                E(f"figura ausente: {src}")

        # 7b. capa e despedida levam SEMPRE a plate com os quatro logos da casa:
        # os logos que voce definir em LOGOS. A unica dispensa e a lamina com
        # identidade propria de evento (class="slide capa simposio"), em que o logo e o
        # do congresso — foi o caso do Simposio Americas em TMO/tmo-mf.
        if re.search(r'class="slide (?:capa|despedida)\b', h):
            LOGOS = ()   # kit: sem logos obrigatórios; ponha os seus aqui se quiser exigir
            if re.search(r'class="slide (?:capa|despedida)[^"]*\b(?:simposio|evento)\b', h):
                pass                      # identidade do evento: o logo e outro
            else:
                faltam = [lg for lg in LOGOS if f"logos/{lg}.png" not in h]
                if faltam:
                    E("capa/despedida sem os logos da casa: falta " + ", ".join(faltam))
            for lg in LOGOS:
                if f"logos/{lg}.png" in h and not (BASE / "logos" / f"{lg}.png").exists():
                    E(f"logo ausente: logos/{lg}.png")

    # 8. order.txt
    ordem = BASE / "order.txt"
    if ordem.exists():
        citados = [l.strip().lstrip("#").strip() for l in ordem.read_text(encoding="utf-8").splitlines()
                   if l.strip() and not l.strip().startswith("# ")]
        citados = [c for c in citados if c]
        for c in citados:
            if c not in nomes_parts:
                erros.append(f"order.txt cita '{c}' que nao existe em parts/")
        for n in sorted(nomes_parts - set(citados)):
            avisos.append(f"parts/{n}.html existe mas nao esta no order.txt")
    else:
        avisos.append("order.txt ainda nao existe")

    print(f"laminas: {len(PARTS)}")
    if erros:
        print(f"\nERROS ({len(erros)})")
        for e in erros:
            print("  " + e)
    if avisos:
        print(f"\nAVISOS ({len(avisos)})")
        for a in avisos:
            print("  " + a)
    if not erros and not avisos:
        print("\nok — nada a corrigir")
    return 1 if erros else 0


if __name__ == "__main__":
    sys.exit(main())
