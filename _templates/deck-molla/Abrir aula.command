#!/bin/bash
# ============================================================
#  TITULO DA AULA — abrir a aula (duplo-clique neste arquivo)
#  Sobe um servidor local e abre a aula JA NA VERSAO DO PALCO.
#  É ESTE jeito que faz a segunda tela funcionar ao vivo:
#  aberto por file:// o navegador bloqueia o envio do slide atual.
#  NÃO feche a janela do Terminal durante a apresentação.
# ============================================================
cd "$(dirname "$0")" || exit 1

VERSAO="NOME-DA-VERSAO"          # seleção salva no organizador (versoes.json)
SESSAO="AULAID"
APP="https://AULAID-segunda-tela.vercel.app"

PORT=8080
for p in 8080 8081 8082 8083 8084 8085; do
  if ! lsof -i :"$p" >/dev/null 2>&1; then PORT=$p; break; fi
done

python3 servidor_aula.py "$PORT" >/dev/null 2>&1 &
SRV=$!
# NADA interrompe a aula: -d display, -i ocioso, -s sistema na tomada e
# -u "usuario ativo", que e o unico que segura o PROTETOR DE TELA (foi ele
# que travou a aula de 17-set-2026, nao o sleep). A assertion -u expira, por
# isso o laco renova de minuto em minuto enquanto o servidor viver -- com teto
# de 4h: janela esquecida aberta fazia o -u acordar o Mac de tampa fechada a
# cada minuto, por dias (883 acordadas em 06-out-2026).
( FIM=$(( $(date +%s) + 4*3600 ))
  while kill -0 $SRV 2>/dev/null && [ "$(date +%s)" -lt "$FIM" ]; do caffeinate -disu -t 60; done ) >/dev/null 2>&1 &
CAFF=$!
trap 'kill $CAFF 2>/dev/null' EXIT
sleep 1

# zera votos, nuvem, perguntas e estimativas da turma antes de começar
curl -s -o /dev/null "$APP/api/reset-all?session=$SESSAO" && echo "  ✅ Sessão zerada."

VURL=$(python3 -c "import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1]))" "$VERSAO")
open "http://localhost:$PORT/deck.html?v=$VURL"

echo ""
N=$(grep -vc '^\s*#\|^\s*$' order.txt)
echo "  ✅ Aula aberta — versão $VERSAO ($N lâminas)."
echo "     http://localhost:$PORT/deck.html?v=$VURL"
echo ""
echo "  TECLAS   ← →  ou espaço navegar · G ir para uma lâmina · F tela cheia"
echo "           O organizador · E editar texto · A anotar revisão · N números · W modo on-line · R revelar · P perguntas"
echo "           A abre a anotação da lâmina: escrever ou 🎤 ditar · enter grava e vai para a próxima"
echo "           tudo cai em REVISAO.md (e revisao-audio/) — depois é só me dizer que terminou"
echo ""
# TODOS os IPs do Mac: cabo e Wi-Fi podem estar em redes diferentes, e o celular so alcanca
# o servidor pelo IP da rede em que ELE esta (o cabo do hospital costuma isolar o Wi-Fi).
IPS=$(ifconfig | awk '/inet / && $2 != "127.0.0.1" {print $2}')
echo "  CONTROLE NO CELULAR — o celular precisa estar na MESMA rede de um destes IPs"
for IP in $IPS; do echo "   • http://$IP:$PORT/controle.html"; done
echo "     (cabo e Wi-Fi em redes separadas? ligue o Wi-Fi do Mac na mesma rede do celular, ou use o hotspot do celular)"
echo "     (passa lâmina, ponteiro no telão e o roteiro da lâmina atual)"
echo ""
echo "  PELA INTERNET — funciona de qualquer lugar, mas o comando leva ~0,4 s"
echo "   • Roteiro e controle:  $APP/presenter.html?d=AULAID&s=$SESSAO"
echo "   • Moderar perguntas:   $APP/tela.html?d=AULAID&s=$SESSAO"
echo "   • O que a plateia vê:  $APP/?d=AULAID&s=$SESSAO"
echo ""
echo "  ⚠️  MANTENHA esta janela aberta durante a apresentação."
echo "     Para encerrar: feche a janela (ou Ctrl+C)."
echo ""
wait $SRV
