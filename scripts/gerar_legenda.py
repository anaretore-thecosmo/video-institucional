#!/usr/bin/env python3
"""Gera arquivo .srt a partir da fala de um video ou audio, rodando local.

Usa faster-whisper (Whisper local). Nada sai da maquina, nenhuma chave de API.
Nao altera o arquivo de entrada.

Uso:
    python gerar_legenda.py <video-ou-audio> [-o saida.srt] [--modelo small]
                            [--idioma pt] [--linha 42]

Modelos, do mais rapido ao mais preciso: tiny, base, small, medium, large-v3.
O padrao 'small' da bom resultado em portugues e roda em CPU comum.
O modelo e baixado na primeira vez e fica em cache no computador.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

LIMITE_LINHA = 42      # caracteres por linha de legenda
MAX_LINHAS = 2         # linhas por bloco


def tempo_srt(segundos: float) -> str:
    if segundos < 0:
        segundos = 0.0
    total_ms = int(round(segundos * 1000))
    h, resto = divmod(total_ms, 3_600_000)
    m, resto = divmod(resto, 60_000)
    s, ms = divmod(resto, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def quebrar(texto: str, limite: int) -> list[str]:
    """Quebra o texto em linhas de no maximo `limite` caracteres, sem cortar palavra."""
    palavras = texto.split()
    linhas: list[str] = []
    atual = ""
    for palavra in palavras:
        candidato = f"{atual} {palavra}".strip()
        if len(candidato) <= limite or not atual:
            atual = candidato
        else:
            linhas.append(atual)
            atual = palavra
    if atual:
        linhas.append(atual)
    return linhas


def extrair_audio(entrada: Path, destino: Path) -> Path:
    """Extrai a faixa de audio em 16 kHz mono, que e o que o Whisper espera."""
    if shutil.which("ffmpeg") is None:
        sys.exit("ERRO: ffmpeg nao encontrado no PATH.")
    saida = destino / "audio.wav"
    cmd = [
        "ffmpeg", "-nostdin", "-y", "-v", "error", "-i", str(entrada),
        "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(saida),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        cauda = "\n".join(r.stderr.strip().splitlines()[-10:])
        sys.exit(f"ERRO ao extrair o audio:\n{cauda}")
    return saida


def main() -> None:
    ap = argparse.ArgumentParser(description="Gera .srt a partir da fala, rodando local.")
    ap.add_argument("entrada", help="arquivo de video ou audio")
    ap.add_argument("-o", "--saida", help="arquivo .srt (padrao: mesmo nome da entrada)")
    ap.add_argument("--modelo", default="small",
                    help="tiny, base, small (padrao), medium ou large-v3")
    ap.add_argument("--idioma", default="pt", help="codigo do idioma (padrao: pt)")
    ap.add_argument("--linha", type=int, default=LIMITE_LINHA,
                    help=f"caracteres por linha (padrao: {LIMITE_LINHA})")
    args = ap.parse_args()

    try:
        from faster_whisper import WhisperModel
    except ImportError:
        sys.exit(
            "ERRO: faster-whisper nao esta instalado.\n"
            "Instalar com:  python -m pip install faster-whisper"
        )

    entrada = Path(args.entrada)
    if not entrada.is_file():
        sys.exit(f"ERRO: arquivo nao encontrado -> {entrada}")
    saida = Path(args.saida) if args.saida else entrada.with_suffix(".srt")

    temporaria = Path(tempfile.mkdtemp(prefix="legenda_"))
    try:
        print(f"Extraindo o audio de {entrada.name} ...", file=sys.stderr)
        audio = extrair_audio(entrada, temporaria)

        print(f"Carregando o modelo '{args.modelo}' (a primeira vez baixa e demora) ...",
              file=sys.stderr)
        modelo = WhisperModel(args.modelo, device="cpu", compute_type="int8")

        print("Transcrevendo ...", file=sys.stderr)
        segmentos, info = modelo.transcribe(str(audio), language=args.idioma)

        blocos: list[str] = []
        contador = 0
        for seg in segmentos:
            texto = seg.text.strip()
            if not texto:
                continue
            linhas = quebrar(texto, args.linha)[:MAX_LINHAS]
            contador += 1
            blocos.append(
                f"{contador}\n{tempo_srt(seg.start)} --> {tempo_srt(seg.end)}\n"
                + "\n".join(linhas) + "\n"
            )
            print(f"  [{seg.start:7.2f} -> {seg.end:7.2f}] {texto[:60]}", file=sys.stderr)

        if not blocos:
            sys.exit("ERRO: nenhuma fala reconhecida. Conferir se o arquivo tem audio com voz.")

        saida.write_text("\n".join(blocos), encoding="utf-8")
        print(f"\nPronto: {saida}")
        print(f"Idioma detectado: {info.language} | duracao lida: {info.duration:.2f}s")
        print(f"Blocos de legenda gerados: {contador}")
        print("CONFERIR o texto antes de queimar no video - transcricao automatica erra "
              "nome proprio, numero e termo tecnico.")
    finally:
        shutil.rmtree(temporaria, ignore_errors=True)


if __name__ == "__main__":
    main()
