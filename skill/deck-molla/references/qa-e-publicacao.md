# Portões e publicação

## Os cinco portões

```bash
python3 qa_deck.py                                    # estrutura
python3 qa_figuras.py                                 # resolução das figuras
python3 qa_qr.py                                      # QR apontam para ESTA aula
python3 ../../tools/qa_laminas.py deck.html           # geometria, modo normal
python3 ../../tools/qa_laminas.py deck.html --online  # geometria, modo on-line
```

`qa_deck.py` checa uma `<section>` por arquivo, balanço de `<div>`, tokens de cor inexistentes,
estilo local sem prefixo, rodapé presente e **sendo citação**, palavras proibidas e título longo.

`qa_laminas.py` abre o deck no navegador e mede: texto sobre o rodapé, blocos sobrepostos,
transbordo do palco, subtítulo encoberto. **Rode nos dois modos** — o modo on-line sobe os pisos de
tipografia e quebra lâminas que passam no normal.

`qa_qr.py` decodifica cada QR do deck montado e reprova se faltar `d=<id>`. Sem ele, uma pasta
copiada de outra aula leva a plateia para o conteúdo errado, e nada mais acusa.

Tudo fecha em zero antes de fechar a aula.

## Derivados

```bash
python3 gerar_artigos.py                                  # ARTIGOS.md + artigos.json
python3 gerar_segunda_tela.py --versao "<nome>"           # cards, poll, falas, tópicos
python3 ../../tools/deck_slides_json.py deck.html segunda-tela/slides.json --versao "<nome>"
python3 ../../tools/deck_roteiro.py deck.html Roteiro.html --minutos 60 \
    --falas roteiro-falas.json --versao "<nome>"
python3 ../../tools/deck_standalone.py deck.html           # HTML com tudo embutido
python3 ../../tools/deck_html_to_pdf.py deck.html          # PDF
```

## Roteiro

Duas formas do mesmo conteúdo, ancoradas no `data-id` (sobrevivem a reordenação):

- `roteiro-falas.json` — a fala, uma a três frases por lâmina
- `roteiro-topicos.json` — de um a quatro tópicos de 3 a 9 palavras

Os tópicos são o que se lê de relance no palco. Escreva o que se **diz**, não o que está na lâmina:
o que o número significa, a ressalva que precisa ser dita, o que muda na conduta. Nas interativas, a
instrução de palco vem primeiro ("30 s de votação", "revelar com R depois dos votos").

Com 100+ lâminas, vale um workflow com um agente por bloco e uma passada de costura no fim, para
amarrar as transições entre blocos e tirar repetição.

## Git

Fonte vai para o git: `parts/`, `_shell_*`, scripts, `order.txt`, `versoes.json`, JSON do roteiro.
Derivado pesado (standalone, PDF, QA) fica fora do git. Não
misture aulas diferentes no mesmo commit.

## Conflitos de interesse

A lâmina `modelo-disclosure.html` traz a grade por categoria; preencha com as suas empresas.
