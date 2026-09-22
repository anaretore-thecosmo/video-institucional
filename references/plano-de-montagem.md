# Formato do plano de montagem (plano.json)

Indice:
1. Exemplo completo
2. Campos da raiz
3. Campos de bloco
4. Trilha
5. Cartelas
6. O que o script faz sozinho
7. O que o script NAO faz
8. Conferir antes de renderizar

---

O `montar.py` le este arquivo. Escrever o plano so DEPOIS do roteiro aprovado
e dos arquivos entregues.

## Exemplo completo

```json
{
  "saida": "prontos/institucional.mp4",
  "largura": 1920,
  "altura": 1080,
  "fps": 30,
  "crf": 18,
  "preset": "slow",
  "duracao_minima_s": 60,
  "duracao_maxima_s": 90,
  "cor": "",
  "cartela_abertura": {"imagem": "marca/abertura.png", "duracao": 3, "aparece_devagar": true},
  "cartela_fecho": {"imagem": "marca/fecho.png", "duracao": 4, "aparece_devagar": true},
  "trilha": {
    "arquivo": "trilha/tema.mp3",
    "volume_db": -18,
    "abaixar_na_fala": true,
    "fade_in": 1,
    "fade_out": 2
  },
  "legenda": {"arquivo": "legendas/final.srt"},
  "blocos": [
    {
      "rotulo": "1. chegada",
      "arquivo": "brutos/aereo_01.mp4",
      "inicio": "00:00:04.5",
      "fim": "00:00:10.0",
      "som": "mudo",
      "cor": "colorbalance=rs=0.04:bs=-0.04"
    },
    {
      "rotulo": "2. a fala principal",
      "arquivo": "brutos/entrevista_02.mp4",
      "inicio": "00:01:12",
      "fim": "00:01:27",
      "som": "original"
    }
  ]
}
```

## Campos

### Raiz

| Campo | Obrigatorio | Padrao | O que faz |
|---|---|---|---|
| `saida` | nao | `institucional.mp4` | caminho do arquivo entregue |
| `largura` / `altura` | nao | 1920 / 1080 | formato final; todos os blocos sao padronizados nele |
| `fps` | nao | 30 | quadros por segundo do resultado |
| `crf` | nao | 18 | qualidade (menor = melhor e mais pesado) |
| `preset` | nao | `medium` | velocidade de compressao; `slow` para entrega final |
| `duracao_minima_s` / `duracao_maxima_s` | nao | - | janela pedida; o script **mede** o final e avisa se saiu fora |
| `cor` | nao | vazio | filtro de cor aplicado a TODOS os blocos |
| `blocos` | **sim** | - | lista, na ordem do video |

### Bloco

| Campo | Obrigatorio | O que faz |
|---|---|---|
| `arquivo` | **sim** | caminho do bruto |
| `inicio` / `fim` | nao | trecho usado; formato `HH:MM:SS` ou `HH:MM:SS.mmm` |
| `rotulo` | nao | nome do bloco na folha de montagem |
| `som` | nao | `original` (padrao) ou `mudo` |
| `cor` | nao | filtro so deste bloco; substitui o `cor` da raiz |

### Trilha

`abaixar_na_fala: true` liga o ducking: a musica abaixa sozinha quando ha som
nos blocos e volta quando acaba. Medido em 22/09/2026 nesta maquina: queda de
5,6 dB na musica durante a fala.

Se nenhum bloco tem som original, deixar `abaixar_na_fala: false`.

### Cartelas

`imagem` aceita PNG ou JPG, de preferencia ja no formato final do video.
`aparece_devagar: true` coloca meio segundo de fade na entrada e na saida.

## O que o script faz sozinho

- Padroniza resolucao, proporcao (com faixa preta quando precisa), fps e SAR.
- Cria trilha de audio silenciosa para bloco mudo ou bruto sem som.
- Normaliza o volume final para -16 LUFS.
- Grava a folha de montagem em `<saida>.montagem.md`.
- Mede a duracao final e compara com a janela pedida.

## O que o script NAO faz

- Nao gera legenda: o `.srt` precisa existir (ver SKILL.md).
- Nao reenquadra para vertical automaticamente.
- Nao aplica crossfade entre blocos (corte seco e o padrao).
- Nao altera nenhum arquivo bruto.

## Conferir antes de renderizar

```
python montar.py plano.json --so-conferir
```

Valida o plano e diz se algum arquivo nao foi encontrado, sem renderizar nada.
