#!/usr/bin/env python3
"""Monta o video institucional a partir de um plano de montagem em JSON.

Somente local: nao acessa rede, nao usa chave de API, nao le arquivo de credencial.
Nunca altera os brutos - todo resultado sai em arquivo novo.

Uso:
    python montar.py plano.json [--so-conferir] [--trabalho <pasta-temp>]

--so-conferir valida o plano e imprime o que seria feito, sem renderizar nada.

Formato do plano: ver references/plano-de-montagem.md
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PADRAO = {"largura": 1920, "altura": 1080, "fps": 30, "crf": 18, "preset": "medium"}


def exigir_ferramentas() -> None:
    faltando = [f for f in ("ffmpeg", "ffprobe") if shutil.which(f) is None]
    if faltando:
        sys.exit(f"ERRO: nao encontrei {', '.join(faltando)} no PATH desta maquina.")


def rodar(cmd: list[str], descricao: str) -> None:
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        cauda = "\n".join(r.stderr.strip().splitlines()[-15:])
        sys.exit(f"ERRO em: {descricao}\n{cauda}")


def duracao(caminho: Path) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
         "default=nw=1:nk=1", str(caminho)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def tem_audio(caminho: Path) -> bool:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries",
         "stream=index", "-of", "csv=p=0", str(caminho)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return bool(r.stdout.strip())


def escapar_para_filtro(caminho: Path) -> str:
    """Caminho do Windows dentro de um filtro ffmpeg (subtitles=) precisa ser escapado."""
    texto = str(caminho.resolve()).replace("\\", "/")
    return texto.replace(":", "\\:").replace("'", "\\'")


def cadeia_video(plano: dict, extra: str = "") -> str:
    l, a, fps = plano["largura"], plano["altura"], plano["fps"]
    partes = [
        f"scale={l}:{a}:force_original_aspect_ratio=decrease",
        f"pad={l}:{a}:(ow-iw)/2:(oh-ih)/2:color=black",
        "setsar=1",
        f"fps={fps}",
    ]
    if extra:
        partes.append(extra)
    partes.append("format=yuv420p")
    return ",".join(partes)


def normalizar_bloco(bloco: dict, plano: dict, destino: Path, indice: int) -> Path:
    """Corta um trecho e o converte para o padrao comum da montagem."""
    origem = Path(bloco["arquivo"])
    if not origem.is_file():
        sys.exit(f"ERRO: bloco {indice}: arquivo nao encontrado -> {origem}")

    saida = destino / f"seg_{indice:03d}.mp4"
    cmd = ["ffmpeg", "-nostdin", "-y", "-v", "error"]

    if bloco.get("inicio"):
        cmd += ["-ss", str(bloco["inicio"])]
    if bloco.get("fim"):
        cmd += ["-to", str(bloco["fim"])]
    cmd += ["-i", str(origem)]

    mudo = bloco.get("som", "original") == "mudo"
    origem_tem_audio = tem_audio(origem)
    if mudo or not origem_tem_audio:
        cmd += ["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000"]
        mapa_audio = "1:a"
    else:
        mapa_audio = "0:a"

    cmd += [
        "-map", "0:v:0", "-map", mapa_audio,
        "-vf", cadeia_video(plano, bloco.get("cor", plano.get("cor", ""))),
        "-c:v", "libx264", "-crf", str(plano["crf"]), "-preset", plano["preset"],
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
        "-shortest", str(saida),
    ]
    rodar(cmd, f"normalizar bloco {indice} ({origem.name})")
    return saida


def cartela(spec: dict, plano: dict, destino: Path, nome: str) -> Path:
    """Gera um segmento a partir de uma imagem parada (abertura ou fecho)."""
    imagem = Path(spec["imagem"])
    if not imagem.is_file():
        sys.exit(f"ERRO: cartela {nome}: imagem nao encontrada -> {imagem}")
    dur = float(spec.get("duracao", 3))
    saida = destino / f"cartela_{nome}.mp4"

    extra = ""
    if spec.get("aparece_devagar", True):
        extra = f"fade=t=in:st=0:d=0.5,fade=t=out:st={max(dur - 0.5, 0):.2f}:d=0.5"

    cmd = [
        "ffmpeg", "-nostdin", "-y", "-v", "error",
        "-loop", "1", "-t", f"{dur}", "-i", str(imagem),
        "-f", "lavfi", "-t", f"{dur}", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
        "-map", "0:v:0", "-map", "1:a",
        "-vf", cadeia_video(plano, extra),
        "-c:v", "libx264", "-crf", str(plano["crf"]), "-preset", plano["preset"],
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
        "-shortest", str(saida),
    ]
    rodar(cmd, f"gerar cartela {nome}")
    return saida


def juntar(segmentos: list[Path], destino: Path) -> Path:
    lista = destino / "lista.txt"
    lista.write_text(
        "".join(f"file '{s.resolve().as_posix()}'\n" for s in segmentos), encoding="utf-8"
    )
    corpo = destino / "corpo.mp4"
    rodar(
        ["ffmpeg", "-nostdin", "-y", "-v", "error", "-f", "concat", "-safe", "0",
         "-i", str(lista), "-c", "copy", str(corpo)],
        "juntar os segmentos",
    )
    return corpo


def acabamento(corpo: Path, plano: dict, saida: Path) -> None:
    """Aplica trilha, legenda e normalizacao final de volume, e grava o arquivo entregue."""
    trilha = plano.get("trilha")
    legenda = plano.get("legenda")

    cmd = ["ffmpeg", "-nostdin", "-y", "-v", "error", "-i", str(corpo)]
    filtros_complexos: list[str] = []
    mapa_video, mapa_audio = "0:v", "0:a"

    if trilha:
        arquivo_trilha = Path(trilha["arquivo"])
        if not arquivo_trilha.is_file():
            sys.exit(f"ERRO: trilha nao encontrada -> {arquivo_trilha}")
        cmd += ["-stream_loop", "-1", "-i", str(arquivo_trilha)]
        dur = duracao(corpo)
        volume = trilha.get("volume_db", -18)
        fade_in = float(trilha.get("fade_in", 1.0))
        fade_out = float(trilha.get("fade_out", 2.0))
        musica = (
            f"[1:a]atrim=0:{dur:.3f},volume={volume}dB,"
            f"afade=t=in:st=0:d={fade_in},"
            f"afade=t=out:st={max(dur - fade_out, 0):.3f}:d={fade_out},"
            f"aformat=sample_rates=48000:channel_layouts=stereo[mus]"
        )
        filtros_complexos.append(musica)

        if trilha.get("abaixar_na_fala", True):
            filtros_complexos.append("[0:a]asplit=2[fala1][fala2]")
            filtros_complexos.append(
                "[mus][fala1]sidechaincompress=threshold=0.03:ratio=12:attack=20:release=500[musduck]"
            )
            filtros_complexos.append("[musduck][fala2]amix=inputs=2:normalize=0[amix]")
        else:
            filtros_complexos.append("[mus][0:a]amix=inputs=2:normalize=0[amix]")
        filtros_complexos.append("[amix]loudnorm=I=-16:TP=-1.5:LRA=11[aout]")
        mapa_audio = "[aout]"
    else:
        filtros_complexos.append("[0:a]loudnorm=I=-16:TP=-1.5:LRA=11[aout]")
        mapa_audio = "[aout]"

    if legenda:
        arquivo_legenda = Path(legenda["arquivo"])
        if not arquivo_legenda.is_file():
            sys.exit(f"ERRO: legenda nao encontrada -> {arquivo_legenda}")
        estilo = legenda.get(
            "estilo",
            "FontName=Arial,FontSize=22,PrimaryColour=&H00FFFFFF,OutlineColour=&H90000000,"
            "BorderStyle=3,Outline=2,Shadow=0,Alignment=2,MarginV=60",
        )
        filtros_complexos.append(
            f"[0:v]subtitles='{escapar_para_filtro(arquivo_legenda)}':force_style='{estilo}'[vout]"
        )
        mapa_video = "[vout]"

    cmd += ["-filter_complex", ";".join(filtros_complexos)]
    cmd += ["-map", mapa_video, "-map", mapa_audio]
    cmd += [
        "-c:v", "libx264", "-crf", str(plano["crf"]), "-preset", plano["preset"],
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart", str(saida),
    ]
    rodar(cmd, "acabamento final")


def folha_de_montagem(plano: dict, pecas: list[dict], saida: Path, dur_final: float) -> Path:
    destino = saida.with_suffix(".montagem.md")
    camadas = []
    if plano.get("cartela_abertura"):
        camadas.append("cartela de abertura")
    if plano.get("trilha"):
        ducking = " (abaixa quando ha fala)" if plano["trilha"].get("abaixar_na_fala", True) else ""
        camadas.append(f"trilha de fundo{ducking}")
    if plano.get("legenda"):
        camadas.append("legenda na tela")
    if plano.get("cartela_fecho"):
        camadas.append("cartela de fecho")

    linhas = [
        f"# Folha de montagem - {saida.name}",
        "",
        f"- Duracao final **medida**: {dur_final:.1f}s",
        f"- Formato: {plano['largura']}x{plano['altura']} a {plano['fps']} quadros por segundo",
        f"- Camadas ligadas: {', '.join(camadas) if camadas else 'nenhuma, so os videos'}",
        "",
        "| # | Peca | Vem de | Trecho | Som |",
        "|---|---|---|---|---|",
    ]
    for i, p in enumerate(pecas, 1):
        linhas.append(
            f"| {i} | {p['rotulo']} | `{p['origem']}` | {p['trecho']} | {p['som']} |"
        )
    linhas += ["", "Os arquivos brutos nao foram alterados em nenhum momento."]
    destino.write_text("\n".join(linhas), encoding="utf-8")
    return destino


def main() -> None:
    ap = argparse.ArgumentParser(description="Monta o video institucional a partir de um plano JSON.")
    ap.add_argument("plano", help="arquivo plano.json")
    ap.add_argument("--so-conferir", action="store_true", help="valida sem renderizar")
    ap.add_argument("--trabalho", help="pasta temporaria (padrao: temporaria do sistema)")
    args = ap.parse_args()

    exigir_ferramentas()
    plano = json.loads(Path(args.plano).read_text(encoding="utf-8"))
    for chave, valor in PADRAO.items():
        plano.setdefault(chave, valor)

    if not plano.get("blocos"):
        sys.exit("ERRO: o plano nao tem nenhum bloco.")
    saida = Path(plano.get("saida", "institucional.mp4"))
    saida.parent.mkdir(parents=True, exist_ok=True)

    if args.so_conferir:
        print(f"Plano valido: {len(plano['blocos'])} bloco(s), saida em {saida}")
        for i, b in enumerate(plano["blocos"], 1):
            existe = "ok" if Path(b["arquivo"]).is_file() else "NAO ENCONTRADO"
            print(f"  {i}. {b['arquivo']} [{b.get('inicio','0')} -> {b.get('fim','fim')}] ({existe})")
        return

    temporaria = Path(args.trabalho) if args.trabalho else Path(tempfile.mkdtemp(prefix="montagem_"))
    temporaria.mkdir(parents=True, exist_ok=True)
    try:
        segmentos: list[Path] = []
        pecas: list[dict] = []

        if plano.get("cartela_abertura"):
            spec = plano["cartela_abertura"]
            segmentos.append(cartela(spec, plano, temporaria, "abertura"))
            pecas.append({"rotulo": "cartela de abertura", "origem": spec["imagem"],
                          "trecho": f"{spec.get('duracao', 3)}s", "som": "mudo"})

        for i, bloco in enumerate(plano["blocos"], 1):
            print(f"[{i}/{len(plano['blocos'])}] preparando {Path(bloco['arquivo']).name} ...",
                  file=sys.stderr)
            segmentos.append(normalizar_bloco(bloco, plano, temporaria, i))
            pecas.append({
                "rotulo": bloco.get("rotulo", f"bloco {i}"),
                "origem": bloco["arquivo"],
                "trecho": f"{bloco.get('inicio', 'inicio')} -> {bloco.get('fim', 'fim')}",
                "som": "mudo" if bloco.get("som", "original") == "mudo" else "original",
            })

        if plano.get("cartela_fecho"):
            spec = plano["cartela_fecho"]
            segmentos.append(cartela(spec, plano, temporaria, "fecho"))
            pecas.append({"rotulo": "cartela de fecho", "origem": spec["imagem"],
                          "trecho": f"{spec.get('duracao', 3)}s", "som": "mudo"})

        print("juntando ...", file=sys.stderr)
        corpo = juntar(segmentos, temporaria)
        print("acabamento (trilha, legenda, volume) ...", file=sys.stderr)
        acabamento(corpo, plano, saida)

        dur_final = duracao(saida)
        folha = folha_de_montagem(plano, pecas, saida, dur_final)

        print(f"\nPronto: {saida}")
        print(f"Duracao final MEDIDA: {dur_final:.1f}s")
        minimo, maximo = plano.get("duracao_minima_s"), plano.get("duracao_maxima_s")
        if minimo is not None and dur_final < float(minimo):
            print(f"AVISO: ficou {float(minimo) - dur_final:.1f}s abaixo do minimo pedido ({minimo}s).")
        if maximo is not None and dur_final > float(maximo):
            print(f"AVISO: passou {dur_final - float(maximo):.1f}s do maximo pedido ({maximo}s).")
        print(f"Folha de montagem: {folha}")
    finally:
        if not args.trabalho:
            shutil.rmtree(temporaria, ignore_errors=True)


if __name__ == "__main__":
    main()
