#!/usr/bin/env python3
"""Inspeciona videos brutos e devolve ficha tecnica + sinais de qualidade.

Somente leitura: nunca escreve, move ou altera os arquivos de entrada.
Nao acessa rede. Nao le arquivo de credencial.

Uso:
    python inspecionar_brutos.py <pasta-ou-arquivo> [...] [--json saida.json] [--rapido]

Saida: tabela legivel em stdout e, com --json, o mesmo conteudo estruturado.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

EXTENSOES = {".mp4", ".mov", ".mkv", ".avi", ".m4v", ".mts", ".m2ts", ".webm", ".mpg", ".mpeg"}

# Limiares de exposicao sobre o Y medio (0-255) de cada amostra.
ESCURO = 45.0
ESTOURADO = 215.0
# Fracao de amostras fora da faixa que ja merece aviso.
FRACAO_AVISO = 0.25
# Diferenca entre amostras consecutivas (escala scdet). Medido nesta maquina em
# 22/09/2026 com material sintetico: imagem estatica = 0.000; movimento suave =
# pico 0.94; corte seco entre dois videos = pico 30.7.
# LIMIARES PROVISORIOS: calibrados em material sintetico, nao em captacao real.
# Conferir e ajustar no primeiro uso com material de verdade.
MOVIMENTO_PARADO = 0.3   # pico abaixo disto = quadro praticamente imovel
CORTE_INTERNO = 15.0     # pico acima disto = corte ja existente dentro do arquivo


def exigir_ferramentas() -> None:
    faltando = [f for f in ("ffprobe", "ffmpeg") if shutil.which(f) is None]
    if faltando:
        sys.exit(f"ERRO: nao encontrei {', '.join(faltando)} no PATH desta maquina.")


def listar_arquivos(alvos: list[str]) -> list[Path]:
    achados: list[Path] = []
    for alvo in alvos:
        p = Path(alvo)
        if p.is_dir():
            achados.extend(f for f in sorted(p.rglob("*")) if f.suffix.lower() in EXTENSOES)
        elif p.is_file():
            achados.append(p)
        else:
            print(f"AVISO: nao encontrei {alvo}", file=sys.stderr)
    return achados


def ffprobe(caminho: Path) -> dict:
    cmd = [
        "ffprobe", "-v", "error", "-show_format", "-show_streams",
        "-of", "json", str(caminho),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        return {}
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return {}


def fracao(texto: str) -> float:
    if not texto or "/" not in texto:
        try:
            return float(texto)
        except (TypeError, ValueError):
            return 0.0
    a, _, b = texto.partition("/")
    try:
        a_f, b_f = float(a), float(b)
    except ValueError:
        return 0.0
    return a_f / b_f if b_f else 0.0


def ficha(dados: dict) -> dict:
    fmt = dados.get("format", {}) or {}
    video = next((s for s in dados.get("streams", []) if s.get("codec_type") == "video"), None)
    audio = next((s for s in dados.get("streams", []) if s.get("codec_type") == "audio"), None)

    rotacao = 0
    if video:
        for lado in video.get("side_data_list", []) or []:
            if "rotation" in lado:
                try:
                    rotacao = int(float(lado["rotation"]))
                except (TypeError, ValueError):
                    pass

    largura = int(video.get("width", 0)) if video else 0
    altura = int(video.get("height", 0)) if video else 0
    if abs(rotacao) in (90, 270):
        largura, altura = altura, largura

    return {
        "duracao_s": round(float(fmt.get("duration", 0) or 0), 2),
        "tamanho_mb": round(int(fmt.get("size", 0) or 0) / 1_048_576, 1),
        "largura": largura,
        "altura": altura,
        "fps": round(fracao(video.get("avg_frame_rate", "0/0")) if video else 0.0, 3),
        "codec_video": video.get("codec_name") if video else None,
        "rotacao": rotacao,
        "tem_audio": audio is not None,
        "codec_audio": audio.get("codec_name") if audio else None,
        "canais_audio": audio.get("channels") if audio else None,
    }


def analisar_imagem(caminho: Path, rapido: bool) -> dict:
    """Uma passagem de ffmpeg: exposicao amostrada, trechos pretos e trechos congelados."""
    amostras_por_s = 2 if rapido else 4
    filtro = (
        f"blackdetect=d=0.3:pix_th=0.10,"
        f"freezedetect=n=0.003:d=1.0,"
        f"fps={amostras_por_s},signalstats,scdet=s=0,metadata=print:file=-"
    )
    cmd = ["ffmpeg", "-nostdin", "-v", "info", "-i", str(caminho), "-an", "-vf", filtro, "-f", "null", "-"]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")

    y = [float(m) for m in re.findall(r"lavfi\.signalstats\.YAVG=([\d.]+)", r.stdout)]
    ymin = [float(m) for m in re.findall(r"lavfi\.signalstats\.YMIN=([\d.]+)", r.stdout)]
    ymax = [float(m) for m in re.findall(r"lavfi\.signalstats\.YMAX=([\d.]+)", r.stdout)]

    pretos = re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", r.stderr)
    congelados = re.findall(r"freeze_start: ([\d.]+)", r.stderr)

    # scdet mede o quanto cada amostra difere da anterior (0 = identica, 100 = nada a ver).
    scores = [float(m) for m in re.findall(r"lavfi\.scd\.score=([\d.]+)", r.stdout)]

    total = len(y) or 1
    escuras = sum(1 for v in y if v < ESCURO)
    estouradas = sum(1 for v in y if v > ESTOURADO)

    movimento = sum(scores) / len(scores) if scores else 0.0
    movimento_pico = max(scores) if scores else 0.0
    # Score muito alto entre duas amostras indica corte ja existente dentro do arquivo.
    cortes_internos = sum(1 for s in scores if s > CORTE_INTERNO)

    return {
        "amostras": len(y),
        "brilho_medio": round(sum(y) / total, 1) if y else None,
        "brilho_min": round(min(ymin), 1) if ymin else None,
        "brilho_max": round(max(ymax), 1) if ymax else None,
        "fracao_escura": round(escuras / total, 2),
        "fracao_estourada": round(estouradas / total, 2),
        "movimento_medio": round(movimento, 3),
        "movimento_pico": round(movimento_pico, 3),
        "cortes_internos": cortes_internos,
        "trechos_pretos": [[float(a), float(b)] for a, b in pretos],
        "trechos_congelados": [float(t) for t in congelados],
    }


def vereditos(f: dict, img: dict) -> list[str]:
    saida: list[str] = []
    if img.get("fracao_escura", 0) >= FRACAO_AVISO:
        saida.append("ESCURO: boa parte do take esta abaixo do ponto de leitura; levantar sombras na cor")
    if img.get("fracao_estourada", 0) >= FRACAO_AVISO:
        saida.append("ESTOURADO: ha branco sem informacao; nao da para recuperar no ajuste de cor")
    if img.get("trechos_pretos"):
        saida.append(f"PRETO: {len(img['trechos_pretos'])} trecho(s) preto(s) - aparar antes de usar")
    if img.get("trechos_congelados"):
        saida.append(f"CONGELADO: {len(img['trechos_congelados'])} trecho(s) sem movimento - provavel falha de captura")
    if img.get("movimento_pico", 0) < MOVIMENTO_PARADO and f.get("duracao_s", 0) > 3:
        saida.append("PARADO: quadro quase sem mudanca; serve de pano de fundo, nao de plano principal")
    if img.get("cortes_internos"):
        saida.append(f"JA CORTADO: {img['cortes_internos']} corte(s) dentro do arquivo - escolher um trecho entre eles")
    if not f.get("tem_audio"):
        saida.append("SEM SOM: entra mudo; nao serve para bloco de fala")
    if f.get("rotacao"):
        saida.append(f"ROTACAO {f['rotacao']}deg registrada no arquivo; conferir orientacao no corte")
    if f.get("duracao_s", 0) < 2:
        saida.append("CURTO: menos de 2s, dificil de cortar com entrada e saida limpas")
    if not saida:
        saida.append("OK: sem problema tecnico detectado")
    return saida


def main() -> None:
    ap = argparse.ArgumentParser(description="Inspeciona videos brutos (somente leitura).")
    ap.add_argument("alvos", nargs="+", help="pastas ou arquivos de video")
    ap.add_argument("--json", dest="json_saida", help="grava o resultado estruturado neste arquivo")
    ap.add_argument("--rapido", action="store_true", help="amostra 1x por segundo em vez de 2x")
    args = ap.parse_args()

    exigir_ferramentas()
    arquivos = listar_arquivos(args.alvos)
    if not arquivos:
        sys.exit("ERRO: nenhum arquivo de video encontrado.")

    resultado = []
    for i, caminho in enumerate(arquivos, 1):
        print(f"[{i}/{len(arquivos)}] lendo {caminho.name} ...", file=sys.stderr)
        dados = ffprobe(caminho)
        if not dados:
            resultado.append({"arquivo": str(caminho), "erro": "ffprobe nao conseguiu ler"})
            continue
        f = ficha(dados)
        img = analisar_imagem(caminho, args.rapido)
        resultado.append({"arquivo": str(caminho), "nome": caminho.name, **f, "imagem": img,
                          "vereditos": vereditos(f, img)})

    print()
    print(f"{'ARQUIVO':<34} {'DUR':>7} {'RESOLUCAO':>11} {'FPS':>6} {'SOM':>4}  VEREDITO")
    print("-" * 110)
    for r in resultado:
        if "erro" in r:
            print(f"{Path(r['arquivo']).name[:33]:<34} {'-':>7} {'-':>11} {'-':>6} {'-':>4}  ERRO: {r['erro']}")
            continue
        dur = f"{r['duracao_s']:.1f}s"
        res = f"{r['largura']}x{r['altura']}"
        som = "sim" if r["tem_audio"] else "nao"
        print(f"{r['nome'][:33]:<34} {dur:>7} {res:>11} {r['fps']:>6.2f} {som:>4}  {r['vereditos'][0]}")
        for extra in r["vereditos"][1:]:
            print(f"{'':<34} {'':>7} {'':>11} {'':>6} {'':>4}  {extra}")

    resolucoes = {(r.get("largura"), r.get("altura")) for r in resultado if "erro" not in r}
    taxas = {r.get("fps") for r in resultado if "erro" not in r}
    print()
    if len(resolucoes) > 1:
        print(f"ATENCAO: {len(resolucoes)} resolucoes diferentes no material - a montagem vai padronizar todas.")
    if len(taxas) > 1:
        print(f"ATENCAO: {len(taxas)} taxas de quadro diferentes - a montagem vai padronizar todas.")

    if args.json_saida:
        Path(args.json_saida).write_text(json.dumps(resultado, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nFicha completa gravada em {args.json_saida}")


if __name__ == "__main__":
    main()
