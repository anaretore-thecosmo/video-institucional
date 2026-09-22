# video-institucional

Skill para Claude Code que monta **vídeo institucional** a partir de vários
vídeos brutos — drone, câmera, celular — com critério de videomaker sênior.

Autoria: **Ana Retore — THE COSMO**. Licença MIT.

---

## O que ela faz

Não é um juntador de arquivos. A skill conduz o trabalho na ordem em que um
profissional trabalha: **o roteiro nasce antes dos arquivos**, e o material
passa a servir ao roteiro, em vez de o vídeo ficar refém do que por acaso foi
gravado.

O fluxo tem cinco passos:

1. **Tipo** — apresenta dez tipos de institucional (quem somos, manifesto,
   depoimento, bastidores, produto, perfil, ambiente, convite, retrospectiva,
   recrutamento) e você escolhe um.
2. **Duração** — pergunta o tempo mínimo e máximo. Tudo depois respeita essa
   janela, e no fim a duração real é medida e comparada com ela.
3. **Jornada** — investiga, com perguntas feitas uma por vez, a experiência que
   o vídeo vai provocar: quem assiste, onde assiste, o que sente no primeiro
   segundo, com o que fica no fim, o que deve fazer depois. Daí sai o roteiro
   em blocos, que você aprova antes de qualquer corte.
4. **Material** — só então pede os arquivos, e não pede "manda os vídeos":
   pede, bloco a bloco, o que cada um precisa. Inspeciona cada bruto e escolhe
   os trechos aplicando gramática de montagem.
5. **Montagem** — corta, padroniza, aplica as camadas ligadas, mede o resultado
   e entrega o vídeo com uma folha de montagem que diz de onde veio cada peça.

## A inteligência

O valor da skill está nas referências que ela consulta na hora certa:

- **Gramática de montagem** — ordem de eliminação de takes, escala de plano e
  variação, quanto tempo cada plano fica no ar, onde cortar (cortar no
  movimento, respiro depois da fala), continuidade de direção e de luz, arcos
  narrativos, e a lista de erros que denunciam montagem amadora.
- **Luz e cor** — o que dá e o que não dá para consertar (branco estourado não
  volta), a ordem correta de ajuste, climas prontos apresentados em linguagem
  simples, e o procedimento para **casar material de drone com câmera de solo**
  — o ajuste que mais separa profissional de amador.
- **Performance** — o destino decide duração, proporção, som e texto. Vídeo de
  recepção roda mudo em loop; vídeo de feed precisa prender em dois segundos;
  vídeo de reunião pode respirar. Inclui tamanho mínimo de texto, zona segura,
  normalização de volume e loop sem piscada.
- **Tipos e jornadas** — as jornadas padrão de cada tipo e as perguntas de
  investigação.

## Camadas opcionais

Quatro chaves, ligadas conforme o objetivo do vídeo:

| Chave | O que faz |
|---|---|
| Som original | mantém ou corta a fala gravada |
| Trilha de fundo | música por baixo; com fala ligada, a música abaixa sozinha |
| Legenda na tela | texto queimado no vídeo |
| Cartela de abertura e fecho | tela com marca e título |

E quatro receitas prontas: vitrine muda, vitrine com música, depoimento e
institucional completo.

## Privacidade

Roda **inteiramente na sua máquina**. Não usa serviço de nuvem, não usa chave
de API, não abre arquivo de credencial, e nenhum vídeo sai do computador. Os
arquivos brutos nunca são alterados — todo resultado sai em arquivo novo.

## Requisitos

- **ffmpeg** e **ffprobe** no PATH (testado com ffmpeg 8.1).
- **Python 3.10+** (`python3` em Linux e macOS, `python` no Git Bash do Windows).
- Opcional, só para legenda automática: `faster-whisper`, que transcreve
  localmente. Sem ele a skill funciona, apenas sem legenda automática.
  ```bash
  python3 -m pip install faster-whisper
  ```

## Instalação

```bash
git clone https://github.com/anaretore-thecosmo/video-institucional.git
cd video-institucional
bash instalar.sh
```

Ou copie a pasta manualmente para `~/.claude/skills/video-institucional`.

Depois, dentro do Claude Code, peça um vídeo institucional em linguagem
natural ("quero montar um institucional com esses vídeos") e a skill ativa.

## Estado conhecido

Honestidade sobre o que foi e o que não foi provado:

- Montagem testada ponta a ponta com ffmpeg 8.1: cartelas, trilha, redução
  automática da música na fala (queda medida de 5,6 dB) e legenda queimada,
  todas funcionando.
- Geração de legenda testada com fala real em português: `.srt` válido, tempos
  e acentuação corretos, modelo `small` rodando em CPU.
- Os limiares de detecção de movimento e de corte interno do
  `inspecionar_brutos.py` foram calibrados em **material sintético**, não em
  captação real. São provisórios e estão marcados como tal dentro do script.
  Conferir no primeiro uso com material de verdade.
- A skill não reenquadra para vertical automaticamente e usa corte seco (sem
  crossfade entre blocos).
- Transcrição automática erra nome próprio, número e termo técnico. A skill
  manda conferir o texto antes de queimar no vídeo.

## Estrutura

```
SKILL.md                          o fluxo e as regras
references/tipos-e-jornadas.md    os dez tipos, jornadas, investigação
references/gramatica-montagem.md  seleção de take, ritmo, corte, continuidade
references/luz-e-cor.md           sombreamento, casar drone com solo
references/performance.md         destino, primeiros segundos, entrega, loop
references/plano-de-montagem.md   formato do plano.json
scripts/inspecionar_brutos.py     ficha técnica e vereditos (somente leitura)
scripts/gerar_legenda.py          transcreve a fala e escreve o .srt, local
scripts/montar.py                 motor de montagem
```
