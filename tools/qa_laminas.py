#!/usr/bin/env python3
"""QA geométrico de um deck (1920x1080): colisão com rodapé, sobreposição entre blocos,
transbordo do palco, subtítulo encoberto e título em mais de 1 linha. Uso: python3 tools/qa_laminas.py deck.html [--online] [--jev]
Título: h1 em mais de 1 linha OU folga < 60 px até a etiqueta reprova (o Safari desenha a Literata ~2% mais larga
que o Chromium; com folga menor o título quebra na tela do Vinícius e o portão não via — 04/11/2026).
Espera 900 ms por lâmina (animações de entrada). Precisa do playwright (Python do Framework).
--jev: fotografa cada lâmina e o Jev 1.14 dá nota de legibilidade "do fundo da sala" (o que a geometria não vê:
figura de artigo com letra miúda, texto demais). Lista as notas < 1,5 (com < 2 quase tudo caía). ~US$ 0,00012 por lâmina."""
import asyncio, json, pathlib, subprocess, sys, tempfile
from playwright.async_api import async_playwright
D=pathlib.Path(sys.argv[1]).resolve(); ONLINE="--online" in sys.argv; JEV="--jev" in sys.argv
TMP=pathlib.Path(tempfile.mkdtemp(prefix="qa_jev_")) if JEV else None
LEG={"leg":{"type":"score","instructions":"This `slide` will be projected in a lecture hall for hematologists. How readable is it from the back row (font size of text, axis labels and numbers in figures; amount of text)?",
     "criteria":["Unreadable: tiny text or figure labels, or a wall of text","Hard: some key labels or numbers too small","Fine: everything important is readable","Excellent: large, clean, instantly readable"]}}
JS=r"""(()=>{
  const sl=document.querySelector('.slide.active'); const st=sl.querySelector('.stage')||sl; const out={rod:[],sob:[],tra:[],sub:[],tit:[]};
  const R=e=>e.getBoundingClientRect(); const vis=e=>{const r=R(e);const cs=getComputedStyle(e);return r.width>4&&r.height>4&&cs.visibility!=='hidden'&&cs.display!=='none'};
  const SEL='.leitura,.card,.callout,.chip,.statcard,.figwrap,table,.ficha,.colvoz,.g,.mg,.pm,.nv,.aa2,.mx,.grp,.agw,.tri,.stage>div[data-reveal],.stage>div[style*="position:absolute"]';
  const bl=[...st.querySelectorAll(SEL)].filter(vis);
  const ft=st.querySelector('footer.fonte');
  if(ft){const f=R(ft); for(const e of bl){const b=R(e); if(e.contains(ft)||ft.contains(e))continue;
    if(b.bottom>f.top+3&&b.top<f.bottom&&b.right>f.left&&b.left<f.right) out.rod.push([(e.className||'').toString().slice(0,22),Math.round(b.bottom-f.top)]);}}
  // sobreposição entre blocos irmãos (nem ancestral nem descendente)
  for(let i=0;i<bl.length;i++)for(let j=i+1;j<bl.length;j++){const a=bl[i],b=bl[j]; if(a.contains(b)||b.contains(a))continue;
    const ra=R(a),rb=R(b); const w=Math.min(ra.right,rb.right)-Math.max(ra.left,rb.left), h=Math.min(ra.bottom,rb.bottom)-Math.max(ra.top,rb.top);
    if(w>6&&h>6&&w*h>600) out.sob.push([(a.className||'').toString().slice(0,18),(b.className||'').toString().slice(0,18),Math.round(w),Math.round(h)]);}
  // transbordo do palco (1920x1080 em coordenadas do stage)
  const s=R(st); for(const e of [...st.querySelectorAll('*')].filter(vis)){const b=R(e);
    if(b.right>s.right+2||b.bottom>s.bottom+2||b.left<s.left-2||b.top<s.top-2){ if(getComputedStyle(e).position==='fixed')continue; if(/\b(halo|accent|grid-dots|veu|veu-sec|capa-bg|secao-bg)\b/.test(e.className||''))continue; out.tra.push([(e.className||e.tagName).toString().slice(0,22),Math.round(Math.max(b.right-s.right,b.bottom-s.bottom,s.left-b.left,s.top-b.top))]); if(out.tra.length>3)break;}}
  // subtítulo encoberto
  const sub=st.querySelector('.sub'); if(sub){const a=R(sub); for(const e of bl){if(e.contains(sub)||sub.contains(e))continue; const b=R(e);
    const inv=Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top); if(inv>2&&a.right>b.left&&a.left<b.right){out.sub.push([(e.className||'').toString().slice(0,22),Math.round(inv)]);break;}}}
  // título em mais de uma linha (regra principal: h1 sempre em 1 linha)
  const h1=st.querySelector('.topbar h1'); if(h1&&vis(h1)){const rg=document.createRange(); rg.selectNodeContents(h1);
    const tops=new Set([...rg.getClientRects()].filter(r=>r.width>1).map(r=>Math.round(r.top/8))); if(tops.size>1) out.tit.push([tops.size+' linhas',h1.textContent.trim().slice(0,40)]);
    else{const tg=st.querySelector('.topbar .tag'),tb=st.querySelector('.topbar'),fim=R(rg).right; const folga=Math.round((tg&&vis(tg)?R(tg).left:R(tb).right)-fim);
      if(folga<60) out.tit.push(['folga '+folga+' px (Safari quebra)',h1.textContent.trim().slice(0,40)]);}}
  return {id:sl.dataset.id,...out};})()"""
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); pg=await b.new_page(viewport={"width":1920,"height":1080})
        await pg.goto(D.as_uri()); await pg.wait_for_timeout(1200)
        # usa o proprio modoOnline do deck quando existe: ele recalcula o encaixe
        # (so ligar a classe deixava figura e ficha com a geometria do modo normal)
        if ONLINE:
            await pg.evaluate("()=>{ if(typeof modoOnline==='function') modoOnline(true);"
                              " else document.body.classList.add('online'); }")
            await pg.wait_for_timeout(700)
        n=await pg.evaluate("document.querySelectorAll('#deck .slide').length"); tot={"rod":0,"sob":0,"tra":0,"sub":0,"tit":0}
        for i in range(n):
            await pg.evaluate(f"show({i})"); await pg.wait_for_timeout(900)
            r=await pg.evaluate(JS)
            if JEV:   # como no PDF (deck_html_to_pdf.py): tudo revelado e sem a UI do deck; tira o estilo depois p/ não mexer na geometria
                st=await pg.add_style_tag(content="[data-reveal],.bignum .bn,.impacto .w{opacity:1 !important;transform:none !important;filter:none !important}"
                                                  "#progress,#counter,#hint,#editbtn,#editpanel,#pergbadge{display:none !important}")
                await pg.evaluate("document.querySelectorAll('.slide.active [data-passo]').forEach(e=>e.classList.add('on'))")   # passos/autopassos
                await pg.wait_for_timeout(600); await pg.screenshot(path=str(TMP/f"{i:03d}_{r['id']}.png")); await st.evaluate("e=>e.remove()")
            for k,lab in [("rod","rodapé"),("sob","sobreposição"),("tra","transbordo"),("sub","sub encoberto"),("tit","título >1 linha")]:
                if r[k]: tot[k]+=1; print(f"{r['id']:<24} {lab:<14} {r[k][:2]}")
        print(f"RESUMO {'on-line' if ONLINE else 'normal'} · rodapé {tot['rod']} · sobreposição {tot['sob']} · transbordo {tot['tra']} · sub {tot['sub']} · título {tot['tit']}")
        await b.close()
    if JEV:
        fs=sorted(TMP.glob("*.png"))
        out=json.loads(subprocess.run([sys.executable,str(pathlib.Path.home()/".claude/skills/jev/jev.py"),"-"],capture_output=True,text=True,
            input=json.dumps({"items":[{"slide":f"@img:{f}"} for f in fs],"questions":LEG})).stdout)
        ruins=[(f.stem.split("_",1)[1],res["answers"]["leg"]) for f,res in zip(fs,out["results"]) if "answers" in res and res["answers"]["leg"]["score"]<1.5]
        for sid,a in ruins: print(f"{sid:<24} legibilidade   {a['score']:.1f}/3 (conf {a['confidence']:.2f})")
        print(f"LEGIBILIDADE (Jev) · {len(ruins)} de {len(fs)} lâminas abaixo de 1,5 · US$ {out['total_cost_usd']:.4f} · capturas em {TMP}")
asyncio.run(main())
