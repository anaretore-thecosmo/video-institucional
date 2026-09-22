#!/usr/bin/env bash
# Instala a skill video-institucional na pasta de skills do Claude Code.
# Somente copia. Nao instala dependencia, nao mexe em configuracao.
set -euo pipefail

ORIGEM="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DESTINO="${HOME}/.claude/skills/video-institucional"

echo "Origem : ${ORIGEM}"
echo "Destino: ${DESTINO}"

if [ -d "${DESTINO}" ]; then
  echo
  echo "Ja existe uma skill instalada nesse caminho."
  read -r -p "Substituir o conteudo dela? [s/N] " resposta
  case "${resposta}" in
    s|S|sim|SIM) ;;
    *) echo "Nada foi alterado."; exit 0 ;;
  esac
fi

mkdir -p "${DESTINO}/references" "${DESTINO}/scripts"
cp "${ORIGEM}/SKILL.md" "${DESTINO}/"
cp "${ORIGEM}/LICENSE" "${DESTINO}/"
cp "${ORIGEM}/references/"*.md "${DESTINO}/references/"
cp "${ORIGEM}/scripts/"*.py "${DESTINO}/scripts/"

echo
echo "Instalado. Conferindo o que chegou:"
find "${DESTINO}" -type f | sort

echo
echo "Conferindo as ferramentas que a skill usa:"
for f in ffmpeg ffprobe python; do
  if command -v "${f}" >/dev/null 2>&1; then
    echo "  ${f}: presente"
  else
    echo "  ${f}: AUSENTE - a skill precisa dele"
  fi
done
if python -c "import faster_whisper" >/dev/null 2>&1; then
  echo "  faster-whisper: presente (legenda automatica disponivel)"
else
  echo "  faster-whisper: ausente (opcional; sem ele nao ha legenda automatica)"
fi
