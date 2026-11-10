#!/bin/bash
# ============================================================
#  Cria uma aula nova a partir do deck molla.
#    ./nova-aula.sh <Tema>/<pasta-da-aula> <id-curto> "Título da aula"
#  Ex: ./nova-aula.sh LMA/lma-idoso lmaidoso "TCTH na LMA do idoso"
#
#  O <id-curto> é a pasta em decks/<id>/ do app da segunda tela e o que
#  entra no QR como d=<id>. Só letras minúsculas e números.
# ============================================================
set -e
MODELO="$(cd "$(dirname "$0")" && pwd)"
RAIZ="$(cd "$MODELO/../.." && pwd)"

DEST="$1"; ID="$2"; TITULO="$3"
[ -z "$DEST" ] || [ -z "$ID" ] || [ -z "$TITULO" ] && {
  echo "uso: ./nova-aula.sh <Tema>/<pasta> <id-curto> \"Título da aula\""; exit 1; }
[ -e "$RAIZ/$DEST" ] && { echo "já existe: $RAIZ/$DEST"; exit 1; }

mkdir -p "$RAIZ/$DEST"
cp -R "$MODELO/"* "$RAIZ/$DEST/"
rm -f "$RAIZ/$DEST/nova-aula.sh" "$RAIZ/$DEST/montar-vitrine.sh" "$RAIZ/$DEST/componentes.html"   # a vitrine e do modelo, nao da aula
cd "$RAIZ/$DEST"

# a capa e a despedida ja nascem prontas: troque SEU NOME, CRM e instituicao.
# Numa aula dentro de evento com identidade propria (simposio, congresso), troque
# depois por parts/modelo-capa-simposio.html e parts/modelo-despedida-simposio.html.
cp parts/modelo-capa.html      parts/capa.html
cp parts/modelo-despedida.html parts/despedida.html

# marcadores → os nomes desta aula
python3 - "$ID" "$TITULO" <<'PY'
import pathlib, sys
aulaid, titulo = sys.argv[1], sys.argv[2]
alvos = [p for e in ("*.py","*.sh","*.command","*.html","*.md") for p in pathlib.Path(".").glob(e)]
alvos += [p for p in pathlib.Path("parts").glob("*.html")]
for p in alvos:
    h = p.read_text(encoding="utf-8")
    n = h.replace("AULAID", aulaid).replace("TITULO DA AULA", titulo).replace("NOME-DO-ARQUIVO", aulaid)
    if n != h: p.write_text(n, encoding="utf-8")
PY

echo "criada em $RAIZ/$DEST"
echo ""
echo "  1. capa.html e despedida.html já estão lá: troque SEU NOME/CRM e img/capa.jpg e img/fim.jpg"
echo "  2. escreva as lâminas em parts/ (comece copiando as modelo-*.html)"
echo "  3. monte a ordem em montar_ordem.py e rode: python3 montar_ordem.py"
echo "  4. ./build.sh"
echo "  5. python3 qa_deck.py && python3 ../../tools/qa_laminas.py deck.html"
echo "  6. python3 build_qr.py && python3 qa_qr.py"
echo ""
echo "  (a segunda tela/votação no celular não faz parte do kit)"
