# deck molla — kit para aulas médicas em HTML com o Claude Code

Deck de lâminas em HTML (16:9) pensado para aulas de hematologia: ficha de dados no alto da lâmina de
estudo, curva original do artigo, leitura-chave curta, rodapé só com a fonte, componentes animados
(forest plot, funil, cronograma, algoritmo…) e portões de QA que reprovam título longo, texto
transbordando e lâmina sem fonte.

O kit traz **o motor, os modelos de lâmina e a skill do Claude Code**. Não traz aulas prontas.

## Instalar

```bash
git clone https://github.com/vcm-sudo/deck-molla-kit.git
cp -R deck-molla-kit/skill/deck-molla ~/.claude/skills/
pip install playwright pillow segno && python3 -m playwright install chromium
```

## Usar

Abra o Claude Code na pasta do kit e peça em português: *"quero fazer uma aula sobre X no deck molla"*.
A skill conduz o resto. Na mão:

```bash
cd _templates/deck-molla
./nova-aula.sh Tema/minha-aula minhaaula "Título da aula"   # cria Tema/minha-aula/ na raiz do kit
cd ../../Tema/minha-aula
# escreva as lâminas em parts/ (copie os parts/modelo-*.html) e liste a ordem em order.txt
./build.sh && open deck.html
python3 qa_deck.py && python3 ../../tools/qa_laminas.py deck.html
```

No deck: ← → navegam, **G** busca lâmina, **F** tela cheia, **O** reorganiza/oculta, **E** edita texto, **N** numeração.
`componentes.html` mostra todos os componentes animados.

## O que fica de fora

Segunda tela (votação no celular da plateia — os interativos aparecem, mas sem servidor de votos),
identidade visual e logos do autor, aulas e material de patrocinadores. Na capa e na despedida,
troque `SEU NOME`, `CRM 000000` e a instituição, e as imagens em `img/`.

Regras de conteúdo (siglas, fonte em todo número, curva original, sem dado de paciente identificável)
estão na skill: `skill/deck-molla/SKILL.md`.

Licença MIT.
