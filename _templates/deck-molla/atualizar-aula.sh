#!/bin/bash
# ============================================================
#  Traz uma aula JÁ EXISTENTE para o deck molla.
#    ./atualizar-aula.sh <Tema>/<pasta-da-aula> [id-curto]
#
#  Troca o motor (CSS+JS) e a ferramentaria, preservando a identidade da aula
#  (título, marca-d'água, versão do palco) e SEM tocar em parts/, order.txt,
#  img/, fig/ ou ref/. O motor antigo fica em _motor-anterior/<data>/.
#
#  Depois de rodar, os portões de QA dizem o que a troca mexeu — é normal
#  algumas lâminas precisarem de ajuste, porque o motor novo tem pisos de
#  tipografia diferentes e regras de rodapé e de leitura-chave que não existiam.
# ============================================================
set -e
MODELO="$(cd "$(dirname "$0")" && pwd)"
RAIZ="$(cd "$MODELO/../.." && pwd)"
ALVO="$RAIZ/$1"; ID="$2"

[ -z "$1" ] && { echo "uso: ./atualizar-aula.sh <Tema>/<pasta> [id-curto]"; exit 1; }
[ -d "$ALVO" ] || { echo "não existe: $ALVO"; exit 1; }
[ -d "$ALVO/parts" ] || { echo "$ALVO não parece uma aula (sem parts/)"; exit 1; }

cd "$ALVO"
CARIMBO=$(date +%Y%m%d-%H%M)
mkdir -p "_motor-anterior/$CARIMBO"
for f in _shell_head.html _shell_tail.html build.sh build_qr.py gerar_segunda_tela.py \
         gerar_artigos.py qa_deck.py qa_figuras.py "Abrir aula.command"; do
  [ -f "$f" ] && cp "$f" "_motor-anterior/$CARIMBO/"
done
echo "motor anterior guardado em _motor-anterior/$CARIMBO/"

# --- o que é desta aula e não pode vir do modelo -------------------------
IDENT=$(python3 "$MODELO/_identidade.py" ler)

# --- o motor e a ferramentaria, do modelo --------------------------------
for f in _shell_head.html _shell_tail.html build.sh build_qr.py gerar_segunda_tela.py \
         gerar_artigos.py qa_deck.py qa_figuras.py qa_qr.py qa_vazamento.py render_lamina.py \
         servidor_aula.py controle.html "Abrir aula.command"; do
  cp "$MODELO/$f" .
done
chmod +x "Abrir aula.command" build.sh

# --- devolve a identidade e troca o id da segunda tela -------------------
python3 "$MODELO/_identidade.py" aplicar "$IDENT" "$ID"

echo ""
echo "motor atualizado. Agora, na pasta da aula:"
echo "  ./build.sh && python3 qa_deck.py && python3 qa_figuras.py && python3 qa_qr.py"
echo "  python3 qa_vazamento.py            # vazamento, faixa por cima, figura perdida"
echo "  python3 ../../tools/qa_laminas.py deck.html"
echo "  python3 ../../tools/qa_laminas.py deck.html --online"
echo ""
echo "Para voltar atrás:  cp _motor-anterior/$CARIMBO/* ."
