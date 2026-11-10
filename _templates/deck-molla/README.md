# deck molla — o modelo das aulas

O motor, a ferramentaria e uma lâmina exemplar de cada tipo, extraídos da aula de
**TCTH na mielofibrose** (set/2026), que é a referência viva do padrão.

## O jeito normal: você não roda nada

Peça em português, no Claude Code, dentro de `Aulas/`:

> *"quero fazer uma aula sobre TCTH na LMA do idoso, 40 minutos, para hematologistas"*
> *"pega minha aula de DECH crônica e traz para o deck molla"*

A skill `deck-molla` entra sozinha e faz o caminho inteiro: cria a pasta, monta o
plano de blocos, escreve as lâminas, confere os números na fonte primária, roda os
cinco portões de QA e publica a segunda tela. Os dois scripts abaixo são o
mecanismo por trás disso — estão aqui para quando você quiser rodar na mão.

## Na mão: aula nova

```bash
./nova-aula.sh LMA/lma-idoso lmaidoso "TCTH na LMA do idoso"
```

Cria a pasta, copia tudo e troca os marcadores. Depois é escrever as lâminas.

## Na mão: aula que já existe

```bash
./atualizar-aula.sh TMO/dech-cronica dechc
```

Troca só o **motor** (CSS + JS) e a **ferramentaria** de uma aula pronta, sem tocar
em `parts/`, `order.txt`, `img/` nem `ref/`. A aula ganha o buscador (G), os selos de
desenho de estudo, o controle remoto pelo celular, o modo on-line e os portões de QA
novos — mantendo as lâminas que ela já tem.

O motor antigo fica em `_motor-anterior/<data>/`; para voltar atrás é um `cp`.

Depois de rodar, **é esperado que o QA acuse algumas lâminas**: o motor novo tem
pisos de tipografia diferentes, e texto que cabia no motor antigo pode transbordar.
Rode os cinco portões e corrija lâmina a lâmina:

```bash
./build.sh && python3 qa_deck.py && python3 qa_figuras.py && python3 qa_qr.py
python3 ../../tools/qa_laminas.py deck.html
python3 ../../tools/qa_laminas.py deck.html --online
```

---

## O que vem junto

| Arquivo | Para quê |
|---|---|
| `_shell_head.html` | **CSS do motor**: tema, tipografia, `.ficha`, `.leitura`, `.bignum`, `.impacto`, `.figwrap`, selos de desenho, ponteiro remoto, modo on-line |
| `_shell_tail.html` | **JS do motor**: navegação, buscador (G), organizador (O), edição de texto no palco (E), números das lâminas (N), passos, gráficos, segunda tela, controle remoto |
| `build.sh` | monta `deck.html` a partir de `order.txt` + `parts/` e embute QR e versões |
| `montar_ordem.py` | gera `order.txt` a partir do plano de blocos; o que sobra entra comentado, nada se perde |
| `build_qr.py` | gera os QR da segunda tela **com `d=<id>`** |
| `gerar_artigos.py` | extrai as referências dos rodapés → `ARTIGOS.md` + `artigos.json` |
| `gerar_segunda_tela.py` | `cards`, `poll`, `falas`, `topicos` para o celular |
| `servidor_aula.py` | servidor local: serve o deck e faz o controle remoto (~46 ms) |
| `controle.html` | controle no celular: passa lâmina, ponteiro, tópicos do roteiro |
| `Abrir aula.command` | sobe tudo, abre na versão do palco e imprime os endereços |
| `qa_deck.py` | portão estrutural: `<section>`, tokens, rodapé, palavras proibidas, títulos |
| `qa_figuras.py` | resolução de cada figura contra o tamanho em que é exibida |
| `qa_qr.py` | decodifica os QR do deck montado e reprova se faltar `d=<id>` |
| `render_lamina.py` | renderiza UMA lâmina em PNG, para conferir uma edição |
| `parts/modelo-*.html` | uma lâmina pronta de cada arquétipo, para copiar |
| `nova-aula.sh` / `atualizar-aula.sh` | aula do zero / aula que já existe |
| `_identidade.py` | guarda título, marca-d'água e versão do palco enquanto o motor é trocado |

Fora daqui, em `tools/`: `qa_laminas.py` (geometria nos dois modos), `deck_roteiro.py`,
`deck_slides_json.py`, `deck_standalone.py`, `deck_html_to_pdf.py`.

## Os arquétipos em `parts/modelo-*.html`

- **capa** e **despedida** — título, assinatura (troque SEU NOME/CRM) e o QR dos artigos. `nova-aula.sh`
  já cria `parts/capa.html` e `parts/despedida.html` a partir desses modelos; troque só a imagem
  de fundo (`img/capa.jpg`, `img/fim.jpg`) pela do tema da aula.
- **capa-simposio** e **despedida-simposio** — a exceção: aula dentro de evento com identidade
  própria (congresso, simpósio), em que o
  logo na lâmina é o do congresso
- **aviso** — conflitos de interesse
- **segunda** — a lâmina que manda a plateia apontar a câmera
- **agenda** — os blocos, só títulos
- **sec-*** — divisória com trilho de índice
- **imp-*** — frase de impacto, palavra a palavra
- **big-*** — número grande com texto ao lado
- **42-a-hobbs-curvas** — lâmina de estudo: ficha em cima, curvas originais, chips
- **n-svr35-panorama** — comparação em barras, com o braço-controle marcado
- **n-esplen-vs-irradiacao** — comparação campo a campo
- **06-c-escores-tratamento** — dois escores lado a lado
- **syn-nrm-series** — gráfico de pontos por coorte
- **nuvem**, **perfil**, **q2**(+resposta), **mf1**(+resposta), **est-*** (+resposta) — interativos
- **levar** — take-home numerado
- **perguntas** — perguntas anônimas ao vivo
- **q-competicao** e **placar** — modo competição (abaixo)

## Modo competição com placar (out/2026)

Opt-in por pergunta. Pensado para residentes: apelido no celular, pontos por acerto rápido, placar animado.

1. **Pergunta que vale pontos** — na `<section>` do quiz, junto do `data-quiz`:
   `data-competicao data-correta="B"` (letra = `data-k` da alternativa certa). Modelo: `parts/modelo-q-competicao.html`.
   Só pergunta com resposta certa sustentada por estudo; enquete de conduta fica de fora.
2. **Placar** — `<section class="slide placar" data-placar="q1,q2">` com `.kick`, `h2`, `.tot` e `.placar-box`
   (modelo: `parts/modelo-placar.html`). Ao abrir, o deck busca `/api/leaderboard` e anima pódio (3 primeiros) e
   lista até o 10º. `data-placar` vazio = todas as competitivas. Pode haver placar parcial e final.
3. **Pontos** — acerto vale 1000, menos 25 por segundo desde que a lâmina abriu no telão (piso 500, aos 20 s).
   Erro vale 0. Voto dado depois que o deck sai da lâmina da pergunta não pontua; vale o horário do último voto.
4. **Gabarito** — `gerar_segunda_tela.py` põe só a lista de ids em `poll.json` (`competicao.quizzes`) e a resposta em
   `segunda-tela/gabarito.json`. Esse arquivo vai para `<app>/api/_gabaritos/<id>.json` (o `publicar_aula.sh` copia),
   **nunca** para `decks/<id>/`, que é público.
5. **Apelido** — o celular pede sozinho quando o `poll.json` tem `competicao`; dá para trocar pelo chip no topo.
6. **Zerar** — a tecla Z / `reset-all` zera apelidos, pontos e as perguntas competitivas (vêm do gabarito).
   Zere antes da aula: passar pela pergunta durante o ensaio abre e fecha o relógio dela.

## O que NÃO vem

Figuras, textos, referências e o `ref/` da aula de origem. `img/fig/` vem vazio.

## Componentes animados (vitrine)

Seis lâminas-modelo com animação por passos, todas CSS + SVG sobre o motor (nenhuma biblioteca,
nenhum script): `parts/modelo-comp-funil` (atrito etapa a etapa), `-cronograma` (Gantt de ponte,
washout, aférese e infusão), `-sinapse` (mecanismo CAR ↔ CD19), `-algoritmo` (fluxo com setas que se
traçam), `-ciclo` (calendário de 28 dias) e `-veia-a-veia` (cadeia de produção com trilho).

```bash
./montar-vitrine.sh      # gera componentes.html: abra e avance com a seta
```

Para usar numa aula: copie a part, renomeie, troque os números pelos da fonte e o selo Didático
pelo do artigo. A convenção de animação é a do motor — `data-passo="n"` avança com a seta; quando
um passo precisa mudar algo que já está na tela, um elemento vazio `<div data-passo="n">` colocado
ANTES do alvo faz o serviço por seletor de irmão (`[data-passo="2"].on ~ .alvo`). Cada componente
traz o fallback para `html.nofx` e para o organizador (`#org`), senão a impressão sai vazia.
A ideia da biblioteca de componentes veio do vídeo "Create instantly beautiful slides with Claude"
(robonuggets), fase 3; o resto do vídeo (skill frontend-slides e design system) já existe aqui.

## Conflitos de interesse (fonte única)

A lista de empresas por categoria mora em **`Aulas/_dados/conflitos-de-interesse.json`** — a mesma
para todas as aulas. A lâmina `parts/modelo-disclosure.html` (e a `02-disclosure.html` de cada aula)
é reescrita a partir dela:

```bash
python3 ../../tools/gerar_disclosure.py LNH/ldgcb-rr        # ou <aula> parts/<arquivo>.html
```

Mudou uma empresa? Edite o JSON e rode o gerador em cada aula que for apresentar de novo.

## Caso clínico (modelo)

`parts/modelo-sec-caso`, `modelo-q-caso` (enquete de conduta antes do caso, sem resposta certa),
`modelo-caso-01-historia` (retrato gerado por IA + chips de identificação + linha do tempo por passos),
`modelo-caso-02-decisao` (dois cartões: o que o hospedeiro permite × a janela), `modelo-caso-03-ponte`
(tabela de opções: controla a doença · preserva o linfócito T · por que foi ou não escolhida),
`modelo-caso-04-conduta` (linha do tempo da conduta + dois cartões), `modelo-caso-05-evolucao`
(PET esquemático antes/depois + chips de desfecho) e `modelo-big-caso` (bignum do desfecho).
Retrato: gerar com o Nano Banana em pintura digital (`gen-retrato-arte.mjs` na pasta do MM), rotular
"Retrato ilustrativo gerado por IA. Não corresponde ao paciente." As lâminas do caso levam
`data-semfonte`; só as que citam estudo têm rodapé.

## Portões (rodar todos antes de fechar)

```bash
python3 qa_deck.py                    # estrutura, rodapé, títulos
python3 qa_figuras.py                 # resolução das figuras
python3 qa_qr.py                      # QR apontam para ESTA aula
python3 qa_vazamento.py               # conteúdo fora do cartão, faixa por cima, figura perdida
python3 qa_vazamento.py --online      # e no modo on-line
python3 ../../tools/qa_laminas.py deck.html
python3 ../../tools/qa_laminas.py deck.html --online
```

**Toda lâmina com `.ficha` leva `selo-fase`** — `f1`/`f2`/`f3` (ensaio), `pre`
(retrospectivo ou coorte), `reg` (registro), `meta` (meta-análise), `curso` (em curso).
