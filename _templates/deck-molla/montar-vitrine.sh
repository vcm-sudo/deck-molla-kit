#!/bin/bash
# ============================================================
#  Monta a VITRINE dos componentes animados: componentes.html
#  (um deck só com parts/modelo-comp-*.html), sem tocar em aula nenhuma.
#  Para ver: abra componentes.html e avance com a seta — cada passo
#  revela uma etapa do componente.
# ============================================================
set -e
T="$(cd "$(dirname "$0")" && pwd)"
TMP="$(mktemp -d)"
cp -R "$T/_shell_head.html" "$T/_shell_tail.html" "$T/parts" "$TMP/"
printf "%s\n" modelo-comp-vitrine modelo-comp-funil modelo-comp-cronograma modelo-comp-sinapse \
               modelo-comp-algoritmo modelo-comp-ciclo modelo-comp-veia-a-veia \
               modelo-comp-forest modelo-comp-escore modelo-comp-escada modelo-comp-swimmer modelo-comp-dose > "$TMP/order.txt"
python3 "$T/../../tools/deck_assemble.py" "$TMP" --saida deck.html >/dev/null
sed 's/TITULO DA AULA/Componentes animados — vitrine/g' "$TMP/deck.html" > "$T/componentes.html"
rm -rf "$TMP"
echo "vitrine: $T/componentes.html"
