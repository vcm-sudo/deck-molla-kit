#!/usr/bin/env python3
"""Acha o que o qa_laminas.py nao ve: conteudo vazando do proprio cartao,
a faixa de leitura por cima de alguma coisa, e figura perdida na prancha.

    /Library/Frameworks/Python.framework/Versions/3.13/bin/python3 qa_vazamento.py [--online]

O qa_laminas compara blocos IRMAOS. Estes tres defeitos escapam dele:

  VAZA      um filho passa da borda do pai (cartao com altura fixa e texto que
            cresceu: o "onde / ambulatorio" saindo por baixo do cartao).
  LEITURA   a faixa escura da leitura-chave cobrindo cartao ou figura.
  FIGURINHA a imagem ocupando menos de 55% da prancha — sobra branca do recorte,
            que e o que faz a curva ficar minuscula no telao.

E dentro do SVG, onde as tres primeiras sao cegas porque medem caixas do HTML:

  SVG-TEXTO   dois <text> um por cima do outro (rotulo de curva sobre rotulo).
  SVG-FORA    <text> passando da borda do proprio <svg> (rotulo cortado).
  SVG-COBERTO <text> tapado por forma opaca desenhada depois dele no DOM.
"""
import argparse
import asyncio
import pathlib
import sys

from playwright.async_api import async_playwright

MEDIR = """() => {
  const s = document.querySelector('#deck .slide.active');
  if (!s) return null;
  const st = s.querySelector('.stage').getBoundingClientRect();
  const k = st.width / 1920;
  const box = e => { const r = e.getBoundingClientRect();
    return {t:(r.top-st.top)/k, b:(r.bottom-st.top)/k, l:(r.left-st.left)/k, r:(r.right-st.left)/k,
            w:r.width/k, h:r.height/k}; };
  const nome = e => e.className && typeof e.className === 'string'
      ? e.tagName.toLowerCase() + '.' + e.className.trim().split(/\\s+/).slice(0,2).join('.')
      : e.tagName.toLowerCase();
  const vis = e => { const c = getComputedStyle(e);
    return c.display !== 'none' && c.visibility !== 'hidden' && parseFloat(c.opacity) > .05; };
  const out = [];

  // 1. filho passando da borda do pai, quando o pai nao rola nem esconde
  s.querySelectorAll('.stage *').forEach(p => {
    if (!vis(p)) return;
    const cs = getComputedStyle(p);
    if (cs.overflow !== 'visible' || cs.position === 'static') return;
    if (!p.classList.length) return;
    const P = box(p);
    if (P.h < 40 || P.w < 40) return;
    [...p.children].forEach(c => {
      if (!vis(c) || getComputedStyle(c).position === 'absolute') return;
      const C = box(c);
      const fora = Math.max(C.b - P.b, C.r - P.r, P.t - C.t, P.l - C.l);
      if (fora > 6) out.push(['VAZA', nome(c) + ' sai ' + Math.round(fora) + 'px de ' + nome(p)]);
    });
  });

  // 2. a faixa de leitura por cima de conteudo
  const L = s.querySelector('.leitura');
  if (L && vis(L)) {
    const B = box(L);
    s.querySelectorAll('.stage > *').forEach(e => {
      if (!vis(e) || L.contains(e) || e.contains(L)) return;
      if (e.classList.contains('leitura') || e.tagName === 'FOOTER') return;
      const ce = getComputedStyle(e);
      if (ce.position === 'static') return;
      const E = box(e);
      const ov = Math.min(B.b,E.b) - Math.max(B.t,E.t);
      const ox = Math.min(B.r,E.r) - Math.max(B.l,E.l);
      if (ov > 6 && ox > 20) out.push(['LEITURA', 'cobre ' + nome(e) + ' em ' + Math.round(ov) + 'px']);
    });
  }

  // 3. figura pequena dentro da prancha
  s.querySelectorAll('.figwrap').forEach(fw => {
    if (!vis(fw)) return;
    const F = box(fw);
    const imgs = [...fw.querySelectorAll('img')].filter(vis);
    if (!imgs.length || F.w < 40) return;
    const area = imgs.reduce((a,i) => { const I = box(i); return a + I.w*I.h; }, 0);
    const oc = area * 100 / (F.w * F.h);
    if (oc < 55) out.push(['FIGURINHA', 'imagem ocupa ' + Math.round(oc) + '% da prancha']);
  });

  // 4. dentro do SVG — o que as tres checagens acima nao alcancam, porque medem
  //    caixas do HTML. Aqui a unidade e o <text>: no palco, texto ilegivel e o
  //    defeito, e ele aparece de tres jeitos.
  const areas = r => Math.max(0, r.w) * Math.max(0, r.h);
  const cruza = (a, b) => {
    const x = Math.min(a.r, b.r) - Math.max(a.l, b.l);
    const y = Math.min(a.b, b.b) - Math.max(a.t, b.t);
    return (x > 0 && y > 0) ? x * y : 0;
  };
  s.querySelectorAll('svg').forEach(sv => {
    if (!vis(sv)) return;
    const S = box(sv);
    const txt = [...sv.querySelectorAll('text')].filter(vis)
      .map(e => ({e, B: box(e), s: e.textContent.trim()}))
      .filter(o => o.s && o.B.w > 6 && o.B.h > 6);

    // 4a. dois textos por cima um do outro
    for (let i = 0; i < txt.length; i++) {
      for (let j = i + 1; j < txt.length; j++) {
        const A = txt[i], C = txt[j];
        const ov = cruza(A.B, C.B);
        if (!ov) continue;
        const menor = Math.min(areas(A.B), areas(C.B));
        if (ov > menor * 0.32) {
          out.push(['SVG-TEXTO', '"' + A.s.slice(0,22) + '" sobre "' + C.s.slice(0,22) + '"']);
        }
      }
    }

    // 4b. texto passando da borda do proprio SVG
    txt.forEach(o => {
      const fora = Math.max(o.B.r - S.r, S.l - o.B.l, o.B.b - S.b, S.t - o.B.t);
      if (fora > 4) out.push(['SVG-FORA', '"' + o.s.slice(0,26) + '" sai ' + Math.round(fora) + 'px do svg']);
    });

    // 4c. forma opaca desenhada DEPOIS do texto, cobrindo-o
    const todos = [...sv.querySelectorAll('*')];
    const pos = new Map(todos.map((e, i) => [e, i]));
    // forma recortada por clip-path ou mask tem bbox MAIOR do que o que aparece:
    // medi-la daria falso positivo (a area sombreada da aplasia cobria o rotulo
    // do condicionamento so na caixa, nunca na tela)
    const recortado = e => {
      for (let n = e; n && n !== sv; n = n.parentElement) {
        const c = getComputedStyle(n);
        if (c.clipPath !== 'none' || c.mask !== 'none' || n.getAttribute('mask')) return true;
      }
      return false;
    };
    const formas = todos.filter(e => /^(rect|circle|ellipse|path|polygon)$/.test(e.tagName) && vis(e))
      .filter(e => !recortado(e))
      .filter(e => { const f = getComputedStyle(e).fill;
        return f && f !== 'none' && !/rgba\\(.*,\\s*0(\\.\\d+)?\\)/.test(f); })
      // um <path> de traco (area, curva) tem caixa enorme e vazia: so contam as
      // formas cheias e compactas, que sao as que de fato tapam texto
      .filter(e => e.tagName !== 'path' || areas(box(e)) < 60000);
    txt.forEach(o => {
      const it = pos.get(o.e);
      formas.forEach(f => {
        if (pos.get(f) < it) return;              // desenhada antes: fica atras
        if (f.contains(o.e) || o.e.contains(f)) return;
        const ov = cruza(o.B, box(f));
        if (ov > areas(o.B) * 0.25) {
          out.push(['SVG-COBERTO', '"' + o.s.slice(0,26) + '" coberto por ' + nome(f)]);
        }
      });
    });
  });
  return out;
}"""


async def main(a):
    deck = pathlib.Path(a.deck).resolve()
    achados = {}
    async with async_playwright() as pw:
        b = await pw.chromium.launch()
        p = await b.new_page(viewport={"width": 1600, "height": 900})
        await p.goto("file://" + str(deck))
        await p.wait_for_timeout(2200)
        if a.online:
            await p.evaluate("()=>document.body.classList.add('online')")
            await p.wait_for_timeout(400)
        n = await p.evaluate("()=>vis().length")
        for i in range(n):
            await p.evaluate("i=>show(vis()[i])", i)
            await p.wait_for_timeout(300)
            # sem isto a medida cai no meio da animação de entrada (o bignum tem
            # delay de até 1,46 s) e o deslocamento residual vira falso "VAZA"
            await p.evaluate("""async () => {
              const s = document.querySelector('#deck .slide.active'); if (!s) return;
              const as = s.getAnimations ? s.getAnimations({subtree:true}) : [];
              await Promise.race([
                Promise.allSettled(as.map(x => x.finished)),
                new Promise(r => setTimeout(r, 2600)),
              ]);
            }""")
            await p.wait_for_timeout(120)
            nome = await p.evaluate("()=>document.querySelector('#deck .slide.active').dataset.id||''")
            r = await p.evaluate(MEDIR)
            if r:
                achados[nome] = r
        await b.close()

    modo = "on-line" if a.online else "normal"
    if not achados:
        print(f"ok — nada vazando, nada coberto, nenhuma figura perdida ({modo})")
        return 0
    total = 0
    for nome, itens in achados.items():
        print(f"\n{nome}")
        for tipo, msg in itens:
            print(f"   {tipo:10s} {msg}")
            total += 1
    print(f"\n{total} achados em {len(achados)} lâminas ({modo})")
    return 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("deck", nargs="?", default="deck.html")
    ap.add_argument("--online", action="store_true")
    sys.exit(asyncio.run(main(ap.parse_args())))
