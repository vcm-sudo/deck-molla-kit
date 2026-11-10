#!/bin/bash
# Monta deck.html (order.txt + parts/) e embute os QR da segunda tela.
#   POLL_SESSION=turma-x ./build.sh   (padrão: AULAID)
cd "$(dirname "$0")"
python3 ../../tools/deck_assemble.py .
SESSAO="${POLL_SESSION:-AULAID}"
BASE_URL="${POLL_BASE:-https://AULAID-segunda-tela.vercel.app}"
python3 - "$SESSAO" "$BASE_URL" <<'PY'
import re, pathlib, sys
sessao, base_url = sys.argv[1], sys.argv[2]
base=pathlib.Path(".")
html=(base/"deck.html").read_text(encoding="utf-8")
n=0
for svg in sorted((base/"qr").glob("*.svg")):
    nome=svg.stem
    pad=re.compile(r"(<!--QR:"+re.escape(nome)+r"-->).*?(<!--/QR:"+re.escape(nome)+r"-->)", re.S)
    html,k=pad.subn(lambda m,s=svg.read_text(encoding="utf-8"): m.group(1)+s+m.group(2), html); n+=k
html=re.sub(r'const POLL_SESSION = "[^"]*"', f'const POLL_SESSION = "{sessao}"', html)
vers=base/"versoes.json"
if vers.exists():
    html=html.replace("</head>", "<script>window.DECK_VERSOES="+vers.read_text(encoding="utf-8")+";</script>\n</head>",1)
    print("versoes.json embutido")
urls=base/"qr"/"urls.json"
if urls.exists():
    html=html.replace("</head>", "<script>window.QR_URLS="+urls.read_text(encoding="utf-8")+";</script>\n</head>",1)
html=re.sub(r'const POLL_BASE = "[^"]*"',    f'const POLL_BASE = "{base_url}"', html)
(base/"deck.html").write_text(html,encoding="utf-8")
print(f"QR embutidos: {n} · sessão={sessao}")
PY
