# Interativos

Os interativos são o núcleo da aula, não o enfeite: numa revisão de tempo, cortam-se lâminas de
conteúdo antes deles. Um por bloco, alternando o tipo entre blocos vizinhos.

Todo interativo precisa do bloco `<!--QR:<nome>-->…<!--/QR:<nome>-->`, que o `build.sh` preenche com
o SVG gerado por `build_qr.py`. Os nomes disponíveis estão nesse script.

## Votação de alternativas

```html
<section class="slide quiz" data-quiz="q2" data-nota="instrução de palco e a resposta">
  <div class="kick">Votação · o ponto de corte</div>
  <h2>A pergunta</h2>
  <div class="opts">
    <div class="opt" data-k="A"><div class="letra">A</div><div class="corpo">
      <div class="txt">Alternativa</div><div class="track"><div class="fill"></div></div></div>
      <div class="pct">—</div></div>
    …
  </div>
  <div class="qr">…<!--QR:quiz-q2-->…<!--/QR:quiz-q2-->…</div>
  <div class="tot">aguardando votos…</div>
</section>
```

A lâmina seguinte é a **resposta**: as quatro alternativas com o veredicto de cada uma e os cartões
de prova. Sem ela a votação fica no ar.

**Se nenhum estudo decide a questão**, não force uma resposta certa. Vire enquete de conduta: kick
"Enquete de conduta · sem resposta certa", pergunta na forma de prática, e a lâmina seguinte mostra
os esquemas lado a lado com o que cada série traz.

## Mito ou fato

`.slide.quiz.mfq` com `.afirm` (a afirmação entre aspas), `.mfbars` com dois `.mfb[data-k]` e o
`.mfrev` com a revelação. **Tecla R alterna** a revelação, e ela volta escondida ao reabrir a lâmina.
Também precisa da lâmina de resposta depois.

## Estimativa com controle deslizante

`.slide.quiz.estq` com `data-guess="<id>"`, `data-min`, `data-max`. No celular vira um slider; no
telão, um histograma dos palpites (`.esthist`) e a linha do valor real (`.estreal`), revelada com R.

Cuidado no gerador: `poll.json` espera **mapa** `{"<id>": {title,q,min,max,step,unit}}`. Como objeto
único com campo `id`, o slider não aparece no celular e ninguém tem o que apertar.

## Nuvem de palavras

`.slide.quiz` com `id="s-nuvem"` e `data-wordq="a pergunta"`. Uma palavra por pessoa. Vale voltar às
palavras no fim da aula.

## Cortina

Comparador arrastável. **Só funciona com blocos curtos ou imagens.** Com duas listas longas de
texto, qualquer posição intermediária corta uma frase no meio — nesse caso use comparação campo a
campo, com as dimensões pareadas em linhas.

## Bignum

`.slide.bignum` com `.tri`, `.tri.quatro`, `.solo` ou `.duo`. Escolha pelo dado: número que fala
sozinho → solo; tensão entre dois → duo; retrato de coorte → tri ou quatro.

**O bignum não pode ser só a repetição da lâmina anterior.** Se o número já apareceu, reapresente em
outra forma ("1 em 8" em vez de "12,5%") e use o texto para o argumento clínico, não para recitar os
mesmos HR.

## Impacto

`.slide.impacto` com `.frase` e cada palavra num `span.w` com `animation-delay` crescente. Uma frase
só, que vira o raciocínio — não resume o que passou. É a única lâmina onde frase de efeito é o ponto.

## Take-home

Numerado, uma linha por ponto, cada uma cabendo numa linha só. Seis pontos é o teto útil.

## Componentes animados

Não são interativos de votação: são lâminas de conteúdo que se constroem por passos. Estão em
`_templates/deck-molla/parts/modelo-comp-*.html` e na vitrine `componentes.html`
(`./montar-vitrine.sh` no template): **funil** de atrito, **cronograma** (Gantt de ponte/washout/
aférese/infusão), **sinapse** (mecanismo CAR ↔ CD19 em SVG), **algoritmo** (nós ligados por setas que
se traçam — nunca caixas soltas), **ciclo** (calendário de 28 dias) e **veia a veia** (cadeia de
produção). Tudo CSS + SVG sobre `data-passo`; sem biblioteca e sem script.

Regra de construção: o que entra novo leva `data-passo="n"`; o que precisa **mudar** algo já na tela
(mover a célula, pintar os dias, encher o trilho) usa um elemento vazio `<div data-passo="n">`
colocado antes do alvo e o seletor de irmão `[data-passo="n"].on ~ .alvo`. Sempre com o fallback
`html.nofx` / `#org`, senão a impressão e o organizador saem sem o estado final. Quando um deles
entrar numa aula, o selo Didático só fica se os números forem ilustrativos — com dado de artigo,
o rodapé vira citação como em qualquer lâmina.
