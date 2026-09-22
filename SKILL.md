---
name: video-institucional
description: >
  Constroi video institucional completo a partir de varios videos brutos (drone,
  camera, celular), com criterio de videomaker senior: escolhe os melhores takes,
  monta na gramatica certa (escala de plano, ritmo, onde cortar), sugere
  sombreamento e ajuste de cor, casa material de drone com camera de solo, e
  otimiza para onde o video vai rodar. Conduz do zero: pergunta o tipo de
  institucional, a duracao minima e maxima, investiga a jornada de experiencia,
  escreve o roteiro em blocos, e so depois pede os arquivos. Roda 100% local com
  ffmpeg, sem nuvem e sem chave de API. Usar quando pedirem "video institucional",
  "juntar meus videos", "montar um video da empresa", "editar os videos do drone",
  "video para o site/recepcao/feed", "video de depoimento", "video de bastidores",
  "manifesto em video", "video de apresentacao da empresa", ou quando houver
  varios arquivos de video brutos para virar uma peca unica.
author: Ana Retore — THE COSMO
license: MIT
compartilhamento: livre
categoria: skills-autorais-genericas
metadata:
  criado_em: 2026-09-22
  requer: ffmpeg e ffprobe no PATH (testado com ffmpeg 8.1)
---

# Video institucional

Monta video institucional com criterio profissional. O roteiro nasce antes dos
arquivos: o material serve ao roteiro, nao o contrario.

## Regras da skill

1. **Tudo local.** Nenhum arquivo sai da maquina. Nao usar servico de nuvem,
   nao usar chave de API, nao abrir nem imprimir arquivo de credencial.
2. **Os brutos nunca sao alterados.** Todo resultado sai em arquivo novo.
3. **Nada de numero inventado.** Duracao, resolucao e tamanho sempre MEDIDOS com
   ffprobe e ditos como medida. Nunca dizer "ficou bom" sem o numero.
4. **Parar para aprovacao** em dois pontos: depois do roteiro, e depois da
   selecao de trechos. Nao renderizar sem aval.
5. **Linguagem simples.** Quem usa nao e tecnica. Nada de jargao sem uma linha
   de explicacao. Nunca mostrar comando de cor ao usuario - mostrar o nome do
   clima ("fim de tarde quente").
6. **Trabalhar na pasta da estacao aberta.** Usar `<raiz do projeto>/video/`
   com `brutos/`, `trilha/`, `marca/`, `legendas/` e `prontos/`. Nao levar
   material de uma jurisdicao para pasta de outra.

## Conferir o ambiente antes de comecar

```bash
ffmpeg -version | head -1 && ffprobe -version | head -1
```

Sem ffmpeg, parar e dizer que falta - **nao instalar nada por conta propria**.
Propor o comando e esperar ordem.

**Nome do interpretador:** os exemplos abaixo usam `python`. Em Linux e macOS
costuma ser `python3`. Conferir com `python --version` antes e usar o que existir.

## O fluxo, em cinco passos

### Passo 1 - Tipo

Mostrar os dez tipos de `references/tipos-e-jornadas.md` e deixar escolher um.

### Passo 2 - Duracao

Perguntar o tempo **minimo** e **maximo**. Tudo depois respeita essa janela, e
no fim o script mede o resultado e avisa se saiu fora.

### Passo 3 - Investigar a jornada

Ler `references/tipos-e-jornadas.md`, secao 3. Fazer as perguntas **uma por
vez**, esperando resposta. A primeira (onde o video vai rodar) e a que mais
muda o resultado - ver tambem `references/performance.md`, secao 1.

Com as respostas, escrever o roteiro em blocos: numero, nome, tempo alvo, o que
acontece na tela, e que peca da jornada ele carrega. Somar os tempos e conferir
contra a janela **antes** de mostrar.

**Apresentar o roteiro e esperar aprovacao explicita.**

### Passo 4 - Pedir os arquivos

Nao pedir "manda os videos". Pedir, bloco a bloco, o material que cada um
precisa. Quando chegarem:

```bash
python scripts/inspecionar_brutos.py <pasta-dos-brutos> --json ficha.json
```

Somente leitura. Devolve ficha tecnica e vereditos por arquivo (escuro,
estourado, trecho preto, congelado, parado, ja cortado, sem som).

Com a ficha em maos, ler `references/gramatica-montagem.md` e escolher os
trechos: qual arquivo, qual trecho, em que ordem, com que duracao. Aplicar os
criterios de selecao, escala de plano, ritmo e ponto de corte.

Se faltar material para um bloco, **nao inventar e nao travar**: dizer qual
bloco ficou sem e propor cartela com texto, foto parada com movimento leve, ou
encurtar o roteiro. O usuario decide.

Ler `references/luz-e-cor.md` e propor o clima, em nome simples. Se houver
drone e camera de solo no mesmo video, casar os dois (secao 4 daquele arquivo)
- e o ajuste que mais separa profissional de amador.

**Apresentar a selecao e esperar aprovacao.**

### Passo 5 - Montar

Escrever o `plano.json` conforme `references/plano-de-montagem.md`, conferir e
renderizar:

```bash
python scripts/montar.py plano.json --so-conferir
python scripts/montar.py plano.json
```

O script padroniza resolucao/proporcao/fps de todos os blocos, aplica cartelas,
trilha (com ducking quando ha fala), legenda queimada e volume normalizado em
-16 LUFS, mede a duracao final e grava a folha de montagem em
`<saida>.montagem.md`.

Entregar: o caminho do arquivo, a **duracao medida**, o tamanho medido, e a
folha de montagem. Se a duracao saiu fora da janela, dizer isso.

## Legenda

A legenda exige um arquivo `.srt`. Duas origens:

1. **Transcricao automatica local** - gerar com o script da propria skill:
   ```bash
   python scripts/gerar_legenda.py <video-ou-audio> -o legendas/final.srt
   ```
   Roda Whisper nesta maquina: nada sai do computador, nenhuma chave de API.
   Depende do pacote `faster-whisper`; conferir com
   `python -c "import faster_whisper"`. Se faltar, **nao instalar sozinho**:
   dizer que falta e propor `python -m pip install faster-whisper`.

   **Sempre conferir o texto com o usuario antes de queimar no video.**
   Transcricao automatica erra nome proprio, numero e termo tecnico - e no
   institucional esses sao justamente os que nao podem sair errados.
2. **Texto escrito a mao**, quando o video tem locucao planejada - o texto ja
   existe no roteiro, so precisa virar `.srt` com os tempos.

Sem `.srt`, montar sem legenda e avisar.

## Arquivos desta skill

- `references/tipos-e-jornadas.md` - os dez tipos, jornadas padrao, perguntas
  de investigacao, e como virar roteiro em blocos. Ler nos passos 1 e 3.
- `references/gramatica-montagem.md` - escolher take, escala de plano, ritmo,
  onde cortar, continuidade, arcos, erros que denunciam amador. Ler no passo 4.
- `references/luz-e-cor.md` - o que da e o que nao da para consertar, ordem de
  ajuste, casar drone com camera de solo, filtros e climas prontos. Ler no
  passo 4.
- `references/performance.md` - destino decide duracao/proporcao/som, primeiros
  segundos, texto na tela, entrega e loop. Ler nos passos 3 e 5.
- `references/plano-de-montagem.md` - formato do `plano.json`. Ler no passo 5.
- `scripts/inspecionar_brutos.py` - ficha tecnica e vereditos (somente leitura).
- `scripts/gerar_legenda.py` - transcreve a fala e escreve o `.srt`, local.
- `scripts/montar.py` - motor de montagem.

## Estado conhecido, em 22/09/2026

- Testado com ffmpeg 8.1: montagem com cartelas, trilha, ducking (queda medida
  de 5,6 dB) e legenda queimada funcionando ponta a ponta.
- `gerar_legenda.py` testado com fala real em portugues: 2 blocos, tempos e
  acentuacao corretos, `.srt` valido. Modelo `small` em CPU.
- Os limiares de movimento e de corte interno do `inspecionar_brutos.py` foram
  calibrados em **material sintetico**, nao em captacao real. Conferir e
  ajustar no primeiro uso com material de verdade.

---

Skill autoral de **Ana Retore — THE COSMO**.
Metodo e conteudo das referencias sao dela. Livre para uso e redistribuicao
com o credito preservado.
