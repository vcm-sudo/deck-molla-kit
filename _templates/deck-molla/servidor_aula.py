#!/usr/bin/env python3
"""Servidor local da aula: serve o deck e faz o controle remoto pela rede local.

    python3 servidor_aula.py [porta]

Por que local: o controle pela nuvem leva ~430 ms entre apertar no celular e a
lâmina virar (duas viagens até os EUA, onde ficam a função e o banco). Na mesma
rede Wi-Fi a viagem é de milissegundos, que é o que o Keynote faz por Bluetooth.

Endpoints (mesma origem do deck, sem CORS e sem banco):
  GET  /ctrl            → {seq, cmd, n, ptr, ts}   (o deck consulta)
  POST /ctrl            → {cmd} ou {ptr:{x,y,on}}  (o celular manda)
  POST /editar          → {edicoes:[{id,old,new}]} (tecla E no deck: grava na part)
  GET  /controle.html   → a página de controle, servida ao celular

Se a rede isolar os aparelhos (comum em hotel), o deck continua aceitando o
controle pela nuvem: os dois caminhos convivem.
"""
import html as _html
import json
import pathlib
import socket
import re
import sys
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

PASTA = str(pathlib.Path(__file__).resolve().parent)

ESTADO = {"seq": 0, "cmd": "", "n": 0, "ptr": None, "ts": 0}
TRAVA = threading.Lock()
CMDS = {"next", "prev", "first", "last", "goto", "revelar", "zerar", "perguntas"}
PARTS = pathlib.Path(PASTA) / "parts"
DECK = pathlib.Path(PASTA) / "deck.html"


def _pares(old: str, new: str):
    """O navegador entrega o texto DECODIFICADO; na part ele pode estar com entidades
    (&amp;, &nbsp;). Tenta as grafias na mesma ordem para old e new."""
    esc = lambda s: _html.escape(s, quote=False)
    nb = lambda s: s.replace("\xa0", "&nbsp;")
    vistos, out = set(), []
    for o, n in ((old, new), (esc(old), esc(new)), (nb(old), nb(new)), (nb(esc(old)), nb(esc(new)))):
        if o not in vistos:
            vistos.add(o); out.append((o, n))
    return out


def _trocar(texto: str, old: str, new: str):
    """Troca old por new se old ocorrer EXATAMENTE uma vez. Devolve (texto, motivo)."""
    maximo = 0
    for o, n in _pares(old, new):
        k = texto.count(o)
        if k == 1:
            return texto.replace(o, n), ""
        maximo = max(maximo, k)
    return None, ("trecho não achado na part" if maximo == 0 else f"trecho aparece {maximo}x na part, sem como saber qual")


def editar(edicoes):
    """Aplica cada edição na part de origem e, por cortesia, no deck.html montado
    (para recarregar a página não desfazer). A part é a fonte da verdade: o
    próximo build.sh regenera o deck a partir dela."""
    res = []
    for e in edicoes or []:
        pid, old, new = str(e.get("id") or ""), str(e.get("old") or ""), str(e.get("new") or "")
        arq = PARTS / f"{pid}.html"
        if not re.fullmatch(r"[\w.-]+", pid) or not arq.is_file():
            res.append({"ok": False, "motivo": f"{pid}: part não existe"}); continue
        if not old.strip():
            res.append({"ok": False, "motivo": f"{pid}: trecho vazio"}); continue
        novo, motivo = _trocar(arq.read_text(encoding="utf-8"), old, new)
        if novo is None:
            res.append({"ok": False, "motivo": f"{pid}: {motivo}"}); continue
        arq.write_text(novo, encoding="utf-8")
        deck_ok = False
        if DECK.is_file():
            d = DECK.read_text(encoding="utf-8")
            m = re.search(r'<section data-id="%s"' % re.escape(pid), d)
            fim = d.find("</section>", m.start()) if m else -1
            if m and fim > 0:
                trecho, _ = _trocar(d[m.start():fim], old, new)
                if trecho is not None:
                    DECK.write_text(d[:m.start()] + trecho + d[fim:], encoding="utf-8"); deck_ok = True
        res.append({"ok": True, "deck": deck_ok})
    return res


def ip_local() -> str:
    """O IP desta máquina na rede local (não precisa de internet para descobrir)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()



def revisao(b):
    """Grava a anotacao de UMA lamina e regera o REVISAO.md.

    A fonte de verdade e o revisao.json (um objeto por lamina); o .md e derivado
    e ordenado pela posicao no order.txt, para eu ler a revisao na ordem em que
    ele viu a aula. Campo vazio apaga a anotacao.
    """
    import time
    pid = str(b.get("id") or "").strip()
    if not pid:
        return {"error": "sem id"}
    base = pathlib.Path(PASTA)
    j = base / "revisao.json"
    try:
        dados = json.loads(j.read_text(encoding="utf-8")) if j.exists() else {}
    except Exception:
        dados = {}
    nota = str(b.get("nota") or "").strip()
    audio = (dados.get(pid) or {}).get("audio")      # o audio nao se perde ao reeditar o texto
    if nota or audio:
        dados[pid] = {"n": int(b.get("n") or 0),
                      "titulo": str(b.get("titulo") or "")[:160],
                      "nota": nota[:2000],
                      "ts": int(time.time())}
        if audio:
            dados[pid]["audio"] = audio
    else:
        dados.pop(pid, None)
    j.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")

    linhas = ["# Revisão da aula", "",
              "<!-- Anotado no palco com a tecla A. Uma entrada por lâmina, na ordem do deck. -->",
              f"<!-- {len(dados)} lâmina(s) com anotação. -->", ""]
    for pid2, d in sorted(dados.items(), key=lambda kv: (kv[1].get("n") or 0, kv[0])):
        linhas.append(f"## {d.get('n') or '?'} · `{pid2}` — {d.get('titulo','')}")
        if d.get("nota"):
            linhas.append(d["nota"])
        if d.get("audio"):
            linhas.append(f"🎤 áudio: `{d['audio']}` — transcrever antes de ler")
        linhas.append("")
    (base / "REVISAO.md").write_text("\n".join(linhas), encoding="utf-8")
    return {"ok": True, "total": len(dados)}



def _regera_md(dados):
    """O REVISAO.md e derivado do revisao.json, sempre na ordem do deck."""
    base = pathlib.Path(PASTA)
    linhas = ["# Revisão da aula", "",
              "<!-- Anotado no palco com a tecla A. Uma entrada por lâmina, na ordem do deck. -->",
              f"<!-- {len(dados)} lâmina(s) com anotação. -->", ""]
    for pid, d in sorted(dados.items(), key=lambda kv: (kv[1].get("n") or 0, kv[0])):
        linhas.append(f"## {d.get('n') or '?'} · `{pid}` — {d.get('titulo','')}")
        if d.get("nota"):
            linhas.append(d["nota"])
        if d.get("audio"):
            linhas.append(f"🎤 áudio: `{d['audio']}` — transcrever antes de ler")
        linhas.append("")
    (base / "REVISAO.md").write_text("\n".join(linhas), encoding="utf-8")


def revisao_audio(pid, n, titulo, dados_bin):
    """Salva o audio ditado para uma lamina e registra no revisao.json."""
    import time
    if not pid or not dados_bin:
        return {"error": "sem id ou sem audio"}
    base = pathlib.Path(PASTA)
    pasta = base / "revisao-audio"
    pasta.mkdir(exist_ok=True)
    seguro = re.sub(r"[^A-Za-z0-9._-]", "-", pid)[:60]
    nome = f"revisao-audio/{int(n or 0):03d}-{seguro}.webm"
    (base / nome).write_bytes(dados_bin)
    j = base / "revisao.json"
    try:
        d = json.loads(j.read_text(encoding="utf-8")) if j.exists() else {}
    except Exception:
        d = {}
    reg = d.get(pid) or {"nota": ""}
    reg.update({"n": int(n or 0), "titulo": str(titulo or "")[:160],
                "audio": nome, "ts": int(time.time())})
    d[pid] = reg
    j.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    _regera_md(d)
    return {"ok": True, "arquivo": nome, "bytes": len(dados_bin)}


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass                                   # silencia: o terminal é do palestrante

    def _json(self, obj, code=200):
        corpo = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(corpo)

    def do_GET(self):
        if self.path.split("?")[0] == "/revisao":
            j = pathlib.Path(PASTA) / "revisao.json"
            try:
                return self._json(json.loads(j.read_text(encoding="utf-8")) if j.exists() else {})
            except Exception:
                return self._json({})
        if self.path.split("?")[0] == "/ctrl":
            with TRAVA:
                return self._json(dict(ESTADO))
        return super().do_GET()

    def do_POST(self):
        from urllib.parse import urlparse, parse_qs, unquote
        rota = self.path.split("?")[0]
        if rota == "/revisao-audio":
            q = parse_qs(urlparse(self.path).query)
            n = int(self.headers.get("Content-Length") or 0)
            if n > 40 * 1024 * 1024:
                return self._json({"error": "audio grande demais"}, 413)
            corpo = self.rfile.read(n)
            with TRAVA:
                return self._json(revisao_audio(
                    unquote((q.get("id") or [""])[0]),
                    (q.get("n") or ["0"])[0],
                    unquote((q.get("titulo") or [""])[0]),
                    corpo))
        if rota not in ("/ctrl", "/editar", "/revisao"):
            return self.send_error(404)
        try:
            n = int(self.headers.get("Content-Length") or 0)
            b = json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            return self._json({"error": "bad json"}, 400)
        if rota == "/editar":
            with TRAVA:
                return self._json({"resultados": editar(b.get("edicoes"))})
        if rota == "/revisao":
            with TRAVA:
                return self._json(revisao(b))
        import time
        with TRAVA:
            if isinstance(b.get("ptr"), dict):
                p = b["ptr"]
                if p.get("on"):
                    lim = lambda v: max(0.0, min(1.0, float(v or 0)))
                    ESTADO["ptr"] = {"x": lim(p.get("x")), "y": lim(p.get("y")), "on": True}
                else:
                    ESTADO["ptr"] = None
                ESTADO["ts"] = int(time.time() * 1000)
                return self._json({"ok": True})
            cmd = str(b.get("cmd") or "")
            if cmd not in CMDS:
                return self._json({"error": "bad request"}, 400)
            ESTADO["seq"] += 1
            ESTADO["cmd"] = cmd
            ESTADO["n"] = max(1, min(999, int(b.get("n") or 1))) if cmd == "goto" else 0
            ESTADO["ts"] = int(time.time() * 1000)
            return self._json({"ok": True, "seq": ESTADO["seq"]})

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


def main():
    porta = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    # serve SEMPRE a pasta da aula, nao o diretorio de onde o comando foi chamado:
    # rodado de outro lugar, o deck.html e o controle.html davam 404.
    srv = ThreadingHTTPServer(("0.0.0.0", porta), partial(Handler, directory=PASTA))
    print(f"servidor local em http://{ip_local()}:{porta}")
    srv.serve_forever()


if __name__ == "__main__":
    main()
