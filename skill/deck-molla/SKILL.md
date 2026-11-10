---
name: deck-molla
description: Cria, revisa e conduz aulas médicas de hematologia no "deck molla" — deck HTML de lâminas com ficha de dados, curvas originais, interativos com votação, segunda tela no celular da plateia, roteiro do apresentador e controle remoto. Use sempre que o usuário falar em criar, montar, modernizar, converter ou revisar uma aula, palestra, deck ou apresentação de hematologia (TMO, linfoma, mieloma, leucemia, mielofibrose, DECH, CAR-T), ou quando pedir para mexer em lâmina, slide, lâmina de estudo, bignum, take-home, divisória, quiz, mito ou fato, nuvem de palavras, segunda tela, roteiro ou QR da aula — inclusive quando só disser "acha minha aula de X", "melhora esse slide", "traz essa aula para o meu padrão", "essa tabela está ilegível", "o gráfico ficou pequeno" ou mandar um print de uma lâmina.
---

# deck molla — as aulas de hematologia

**"Deck molla" é o nome do padrão**, não de uma pasta. A semente para começar é
`_templates/deck-molla/` (na raiz deste kit). Os `parts/modelo-*.html` mostram cada tipo de lâmina:
quando estiver em dúvida sobre como algo deve ficar, abra o modelo equivalente em vez de inventar.

O público é sempre **hematologista**. Isso decide quase tudo: granularidade alta, sigla sem
explicação básica, número com intervalo e valor de p, e ressalva de validade dita em voz alta.

## Fluxo

O usuário não precisa rodar comando. Ele pede em português — *"quero fazer uma aula sobre X"*, *"pega minha
aula de Y e traz para o deck molla"* — e **você** conduz o caminho inteiro do começo ao QA. Os
scripts abaixo são o seu mecanismo, não uma instrução para ele.

**Aula nova**

```bash
cd <kit>/_templates/deck-molla
./nova-aula.sh <Tema>/<pasta> <id-curto> "Título da aula"
```

O `<id-curto>` identifica a aula (só letras minúsculas e números).

Antes de escrever a primeira lâmina, levante o material: PDFs dos estudos em `ref/`, figuras
originais, o tempo de palco e o evento. Sem o PDF não existe lâmina de estudo.

**Aula que já existe, que ele quer no padrão**

Duas coisas diferentes, e vale perguntar qual ele quer se não estiver claro:

1. **Só o motor** — a aula já está no padrão mas é de uma safra anterior e não tem o buscador (G),
   os selos de desenho, o controle remoto ou os portões de QA novos:

   ```bash
   <kit>/_templates/deck-molla/atualizar-aula.sh <Tema>/<pasta> <id-curto>
   ```

   Troca CSS, JS e ferramentaria; **não toca** em `parts/`, `order.txt`, `img/` nem `ref/`. Guarda o
   motor anterior em `_motor-anterior/<data>/`. Depois rode os cinco portões: é esperado que algumas
   lâminas transbordem, porque os pisos de tipografia mudaram — corrija lâmina a lâmina.

2. **O conteúdo também** — a aula é antiga de verdade (bullets, tabela fotografada, sem ficha, sem
   interativos). Aí é atualizar o motor **e depois** varrer `parts/` bloco a bloco, aplicando as
   decisões abaixo. Trabalhe por bloco, mostrando o antes e o depois, e **preserve todas as ideias
   do original** — uma lâmina pode virar três, nenhuma pode sumir sem ele saber.

Em qualquer dos casos: trabalhe em `parts/*.html`, uma lâmina por arquivo, e rode `./build.sh`.
Nunca edite `deck.html`, que é gerado.

**Converter de PPTX ou Keynote**: exporte em PDF, leia lâmina a lâmina e preserve todas as ideias do
original — o usuário confere. Ver `references/anatomia-lamina.md`.

## As decisões que definem o padrão

**Figura antes de texto.** A lâmina começa pelo gráfico, pelo esquema ou pela tabela. Carga alta de
texto é defeito, não estilo. Curva de Kaplan-Meier usa **a figura original do artigo**, com
anotação — nunca reconstrução. Se o PDF não estiver na pasta, peça antes de escrever a lâmina.

**Título afirma com número, em linguagem técnica.** "Ganho de sobrevida com TCTH a partir do int-2",
não "o transplante vira o jogo". Sem metáfora, sem veredicto, sem verbo de interpretação sem número.
Máximo 62 caracteres, senão quebra em duas linhas.

**A ficha é a faixa de dados no alto** da lâmina de estudo: Desenho, N, Idade, Seguimento e os
desfechos, com `destaque` no que importa. Ela é o padrão e se mantém. **Os chips ao lado da figura
só entram com o que a ficha não diz** — intervalo de confiança, subgrupo, ressalva, heterogeneidade.
Chip que repete a ficha sai, e o espaço vai para a figura.

**A leitura-chave tem 15 a 20 palavras.** É a faixa escura no rodapé da lâmina, não um parágrafo.
Pode ser telegráfica, termos separados por `·`. Corte nesta ordem: a explicação do que o número
significa, a segunda frase, os advérbios, o que o título já disse. Não corte os números nem as
ressalvas de validade.

**O rodapé é só procedência.** `Autor X, et al. Revista. Ano`. Nunca comentário sobre a lâmina,
nunca explicação de método, nunca "síntese das lâminas desta aula". Lâmina que não afirma dado
clínico leva `data-semfonte` e fica sem rodapé. `qa_deck.py` reprova quem desobedecer.

**A cor codifica desfecho**, não decora: violeta é o da casa, verde-azulado favorável, âmbar
ressalva, vermelho dano.

**Quando um rótulo puder ser lido ao contrário, reescreva o rótulo.** "Redução do baço ≤ 30%" soa
como resposta e é o oposto; vira "baço não reduziu mais que 30%". Vale para qualquer escore em que
somar ponto seja ruim.

## Números e verificação

Todo número vai para a lâmina **conferido na fonte primária**, com autor, revista e ano. Isso não é
formalidade: na prática, a verificação encontrou medianas que não existiam no artigo (eram de outro
escore), taxas lidas a olho da curva, razão de risco bruta apresentada como ajustada, e o número de
doentes trocado pelo de transplantes.

Quando desconfiar de um dado — e principalmente quando o usuário desconfiar — **dispare o agente
`pesquisador`** pedindo conferência item a item contra o artigo, e diga explicitamente que "não
existe no artigo" é uma resposta aceitável. Depois corrija e conte o que mudou.

Diferencie sempre artigo completo de resumo de congresso, e marque com o selo de desenho
(`badge-pdf`, `badge-abs`, `badge-reg`).

## Ritmo e interativos

Um interativo por bloco, alternando o tipo entre blocos vizinhos. Uma lâmina de impacto ou de número
a cada seis ou sete de conteúdo. O `.bignum` varia entre solo, duo, tri e quatro — nunca dois
seguidos no mesmo formato.

**Toda votação tem lâmina de resposta logo depois.** E só existe votação onde existe resposta: se
nenhum estudo decide a questão, vire enquete de conduta ("como você maneja…", sem resposta certa) ou
lâmina de conteúdo.

Detalhes de marcação em `references/interativos.md`.

## Antes de fechar

```bash
python3 qa_deck.py                                    # estrutura, rodapé, títulos
python3 qa_figuras.py                                 # resolução das figuras
python3 ../../tools/qa_laminas.py deck.html           # geometria
python3 ../../tools/qa_laminas.py deck.html --online  # e no modo on-line
```

Tudo fecha em zero. Derivados (PDF, standalone): ver `references/qa-e-publicacao.md`.

Figura de artigo: `tools/recortar_figura.py <pdf> <pág> <x> <y> <larg> <alt> <saida.png> [--sem-letra]`
(caixa em pontos, 500 dpi, apaga filete/barra na borda e apara o branco) — conferir o PNG depois.

## Ao revisar a pedido do usuário

O usuário costuma mandar um print e uma frase curta. Traduza para o defeito estrutural antes de mexer:

| O que ele diz | O que costuma ser |
|---|---|
| "está ilegível", "gráfico pequeno" | tabela como imagem, ou figura espremida por texto ao lado |
| "tem sobreposição" | `.figwrap` com `top` inline (o motor apaga) ou classe local com nome do motor |
| "está confuso" | duas comparações diferentes no mesmo eixo |
| "parece ao contrário" | rótulo que se lê como favorável sendo desfavorável |
| "repetindo dado" | chip repetindo a ficha, ou lâmina de número repetindo a anterior |
| "muito grande", "muito explicativo" | leitura-chave acima de 20 palavras |

Renderize a lâmina com `python3 render_lamina.py <part> saida.png` e **olhe** antes e depois. Não
conclua que está resolvido sem ver.

## Arquivos de referência

- `references/anatomia-lamina.md` — arquétipos, classes do motor, armadilhas de CSS
- `references/interativos.md` — quiz, mito ou fato, estimativa, nuvem, cortina, bignum, impacto
- `references/qa-e-publicacao.md` — portões, derivados, PDF, standalone, git
