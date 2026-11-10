#!/usr/bin/env python3
"""Le a revisao que ele anotou no palco e devolve tudo em texto, pronto para eu agir.

    /Library/Frameworks/Python.framework/Versions/3.13/bin/python3 ler_revisao.py

Junta o que foi digitado (tecla A) com o que foi ditado (botao de audio), na ordem
do deck. Os audios sao transcritos com o mlx_whisper large-v3-turbo — o mesmo
modelo das orientacoes por audio — e a transcricao fica guardada no revisao.json,
para nao transcrever de novo a cada leitura.

--refazer  transcreve tudo outra vez, ignorando o que ja estava guardado.
"""
import json
import pathlib
import subprocess
import sys
import tempfile

BASE = pathlib.Path(__file__).resolve().parent
MODELO = "mlx-community/whisper-large-v3-turbo"


def transcreve(caminho: pathlib.Path) -> str:
    """webm/opus -> wav 16 kHz mono -> texto. O whisper nao le webm direto."""
    import mlx_whisper
    with tempfile.TemporaryDirectory() as tmp:
        wav = pathlib.Path(tmp) / "a.wav"
        r = subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", str(caminho),
             "-ac", "1", "-ar", "16000", str(wav)],
            capture_output=True)
        if r.returncode or not wav.exists():
            return f"[nao deu para converter o audio: {r.stderr.decode()[:120]}]"
        # condition_on_previous_text=False: sem isso o modelo inventa continuidade
        # entre trechos e repete frases (ver memoria gravacao-de-orientacoes)
        out = mlx_whisper.transcribe(str(wav), path_or_hf_repo=MODELO,
                                     language="pt", condition_on_previous_text=False)
        return (out.get("text") or "").strip()


def main():
    refazer = "--refazer" in sys.argv
    j = BASE / "revisao.json"
    if not j.exists():
        print("nenhuma revisao anotada ainda (revisao.json nao existe).")
        return 0
    dados = json.loads(j.read_text(encoding="utf-8"))
    if not dados:
        print("revisao.json esta vazio.")
        return 0

    mudou = False
    for pid, d in dados.items():
        a = d.get("audio")
        if not a:
            continue
        if d.get("transcricao") and not refazer:
            continue
        arq = BASE / a
        if not arq.exists():
            d["transcricao"] = "[arquivo de audio nao encontrado]"
            mudou = True
            continue
        print(f"transcrevendo {a}…", file=sys.stderr)
        d["transcricao"] = transcreve(arq)
        mudou = True
    if mudou:
        j.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")

    ordem = sorted(dados.items(), key=lambda kv: (kv[1].get("n") or 0, kv[0]))
    print(f"# Revisao — {len(ordem)} lamina(s)\n")
    for pid, d in ordem:
        print(f"## {d.get('n') or '?'} · {pid} — {d.get('titulo','')}")
        if d.get("nota"):
            print(d["nota"])
        if d.get("transcricao"):
            print(f"(ditado) {d['transcricao']}")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
