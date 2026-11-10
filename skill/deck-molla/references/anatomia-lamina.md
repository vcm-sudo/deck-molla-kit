# Anatomia da lâmina

Cada lâmina é um arquivo em `parts/`, com exatamente uma `<section class="slide …">` e um
`<div class="stage">` dentro. O `build.sh` costura tudo na ordem de `order.txt`.

## Lâmina de estudo — o arquétipo principal

```html
<section data-card="45-jain-cibmtr" class="slide figura">
  <div class="stage">
    <style>
    [data-id="45-jain-cibmtr"] .col{position:absolute;left:1330px;right:66px;top:322px;bottom:104px}
    </style>
    <div class="selo-fase" data-reveal><i class="pre">Retrospectivo</i></div>
    <div class="topbar"><h1>Título com o número</h1><span class="tag">Bloco</span></div>
    <div class="sub">Desenho, população e o que a figura mostra</div>
    <div class="ficha" data-reveal style="top:196px">…</div>
    <div class="figwrap" data-reveal style="left:66px;right:620px;top:322px;bottom:104px">
      <img class="plana crisp" src="img/fig/…png" alt="">
    </div>
    <div class="col">…chips…</div>
    <div class="leitura" data-reveal><div class="t">15 a 20 palavras.</div></div>
    <footer class="fonte"><span class="badge-pdf">Artigo publicado</span>
      <span class="txt">Jain T, et al. <i>Blood Adv.</i> 2024</span></footer>
  </div>
</section>
```

`.figura` na `<section>` é o que faz o `.figwrap` ser posicionado. Sem ela a figura sobe para o topo.

## Armadilhas de CSS que já custaram caro

**Todo estilo local tem de ser prefixado** por `[data-id="<nome-do-part>"]`, senão vaza para o deck
inteiro. `qa_deck.py` avisa.

**Nome curto de classe colide com o motor.** `.fx`, `.it`, `.cx`, `.pt`, `.card`, `.kick`, `.opts`
existem no motor e alguns são posicionados de forma absoluta. Reusar o nome faz o bloco herdar
`left/top/right/bottom` e estourar a lâmina. Prefixe com a inicial do part: `.b6-fx`, `.c6-it`.

**`ajustarFiguras` apaga `top` e `bottom` inline do `.figwrap`.** Geometria de figura vai no CSS
local, nunca no atributo `style`.

**Estilo inline vence a folha.** Se a lâmina precisar de ajuste no modo on-line
(`body.online [data-id="…"] .leitura{bottom:…}`), tire a geometria do atributo `style` e ponha no
bloco `<style>`, senão a regra do modo on-line não pega.

**`display:flex` transforma cada `<b>` em item.** Um `.cel{display:flex}` com texto solto dentro
espalha os negritos pela linha. Envolva o conteúdo num `<span>`.

## Componentes do motor

| Classe | Para quê |
|---|---|
| `.ficha` / `.it` / `.rot` / `.val` / `destaque` | a faixa de dados do estudo |
| `.figwrap` (+ `duo`, `trio`) | moldura de figura, posicionada e escalada pelo motor |
| `.chip` (+ `alerta`) / `.v` / `.k` | cartão de número ao lado da figura |
| `.leitura` / `.t` / `.ress` | faixa de conclusão; `.ress` é a ressalva em letra menor |
| `.topbar h1` / `.tag` | título e etiqueta do bloco |
| `.selo-fase i.f1|f2|f3|pre|reg|meta|curso` | desenho do estudo, cartão com ícone |
| `.mtbl` | tabela nativa |
| `.donut[data-pct][data-color]` | rosca animada — nunca troque por SVG estático |
| `.hbar .fill[data-w]` / `.barrow` | barra horizontal animada |
| `.bignum` + `.tri[.quatro]` / `.solo` / `.duo` | lâmina de número |
| `.impacto` + `.frase` + `span.w` | frase palavra a palavra |
| `.secao` + `.trilho.n9` | divisória com índice dos blocos |
| `data-passo="N"` | revela por etapas com a barra de espaço |
| `data-autopassos="1100"` na section | revela sozinho, sem clique |
| `data-reveal` | entra com fade ao abrir a lâmina |
| `data-nota="…"` na section | nota de palco, só para o apresentador |

## Tabela de artigo

Tabela fotografada do artigo é ilegível no palco. Reconstrua em `.mtbl`, em português. Se a tabela
for muito larga, destaque a coluna que decide a lâmina (fundo próprio e corpo maior) — foi o que
resolveu as duas tabelas gêmeas de ruxolitinibe peritransplante.

Imagem só para: curva de sobrevida, forest plot, foto, histologia e esquema do artigo.

## Divisória de bloco

Tem o trilho com os nove blocos, marcando o atual com `.it.on`. Os nomes do trilho, os da agenda e os
do `PLANO` em `montar_ordem.py` têm de ser os mesmos, e todos em linguagem técnica — "Falha de
enxertia", não "O enxerto".

## montar_ordem.py

O `PLANO` é a fonte da ordem. O que existe em `parts/` e não está no plano entra **comentado** no fim
do `order.txt`: nada se perde, e reativar é tirar o `#`. Aposentar uma lâmina é tirá-la do plano,
nunca apagar o arquivo.
