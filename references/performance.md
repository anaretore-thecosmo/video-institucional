# Performance: fazer o video render no lugar onde ele vai rodar

Indice:
1. O destino decide tudo
2. Os primeiros segundos
3. Proporcao e enquadramento
4. Texto na tela
5. Som
6. Entrega: formato e tamanho
7. Loop

---

## 1. O destino decide tudo

Perguntar onde o video vai rodar ANTES de montar. Cada destino muda duracao,
proporcao, texto e som.

| Destino | Duracao | Proporcao | Som | Observacao |
|---|---|---|---|---|
| Site, topo da pagina | 20-40s | 16:9 | **muda**, autoplay | Sem fala. Precisa funcionar sem som |
| Site, pagina "sobre" | 60-120s | 16:9 | com som | Aqui cabe fala e profundidade |
| Feed (Instagram, LinkedIn) | 30-60s | 4:5 ou 1:1 | com legenda | Maioria assiste sem som |
| Stories / Reels | 15-30s | 9:16 | com legenda | Prender em 2s |
| Recepcao, tela em loop | 30-90s | 16:9 | mudo | Loop perfeito, sem texto pequeno |
| Abertura de reuniao | 60-90s | 16:9 | com som | Pode respirar |
| Telao de evento | 45-90s | 16:9 | som alto | Contraste alto, texto grande |
| WhatsApp / envio direto | 30-60s | 9:16 ou 1:1 | com legenda | Arquivo leve, abaixo de 16 MB |
| YouTube | 90-180s | 16:9 | com som | Cabe versao longa |

Se o usuario quiser mais de um destino, montar o principal e depois derivar:
o corte vertical NAO e o 16:9 cortado no automatico. Ver secao 3.

---

## 2. Os primeiros segundos

- **Site e recepcao:** o primeiro plano precisa ser o mais bonito do material.
  Nao ha segunda chance e nao ha som para ajudar.
- **Feed:** 2 segundos. O primeiro quadro precisa ter movimento ou rosto.
  Logo na abertura derruba retencao - deixar a marca para o fim.
- **Cartela de abertura:** so quando o video vai ser assistido por escolha
  (reuniao, evento, "sobre"). Em feed, cartela na frente custa audiencia.

Regra pratica: se o video precisa de 5 segundos para "comecar", ele ja perdeu
quem rolou o feed. Comecar no melhor plano, e contextualizar depois.

---

## 3. Proporcao e enquadramento

- **16:9** e o formato base de institucional.
- **9:16 e 4:5** nao se fazem cortando o 16:9 no centro automaticamente: o
  assunto costuma ficar fora. Reenquadrar plano a plano, decidindo onde fica
  o assunto em cada um.
- Se o material foi filmado em 16:9 e o destino e vertical, considerar fundo
  desfocado do proprio plano em vez de barras pretas:

```
split[a][b];[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=20[bg];[b]scale=1080:-1[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2
```

- **Zona segura:** nao colocar nada importante nos 10% das bordas. Plataformas
  cortam, e tela de recepcao costuma ter moldura.

---

## 4. Texto na tela

- Minimo **2 segundos** no ar, mais 1s a cada 3 palavras alem das primeiras.
- Tamanho minimo: a altura da letra nao pode ser menor que 1/25 da altura do
  video (em 1080p, cerca de 43px).
- Contraste: texto claro sobre caixa escura semitransparente funciona em
  qualquer fundo. Texto puro sobre imagem some quando o fundo clareia.
- Legenda: no maximo 2 linhas, 42 caracteres por linha.
- Nunca encostar o texto na borda inferior - margem de pelo menos 6% da altura.

Estilo de legenda que funciona em qualquer fundo (ja e o padrao do `montar.py`):
```
FontSize=22,PrimaryColour=&H00FFFFFF,OutlineColour=&H90000000,BorderStyle=3,Outline=2,Shadow=0,Alignment=2,MarginV=60
```

---

## 5. Som

- **Normalizar sempre** para -16 LUFS (`loudnorm=I=-16:TP=-1.5:LRA=11`). E o
  alvo usado pelas plataformas; sem isso o video sai mais baixo ou mais alto
  que os vizinhos no feed.
- **Trilha:** entre -22 e -16 dB abaixo da fala. Com fala, ligar o ducking.
- **Fade da trilha:** 1s entrando, 2s saindo. Musica que corta seco no fim
  soa como erro.
- **Sem som:** se o destino e mudo, conferir que o video se explica so pela
  imagem e pelo texto. Assistir sem som antes de entregar.

---

## 6. Entrega: formato e tamanho

Padrao seguro para tudo:

```
-c:v libx264 -crf 18 -preset slow -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart
```

- `crf 18` = qualidade alta. Subir para 20-22 se o arquivo precisar ser leve.
- `-pix_fmt yuv420p` e obrigatorio: sem ele o video nao abre em varios players.
- `-movflags +faststart` faz o video comecar a tocar antes de baixar inteiro.
  Indispensavel para web.
- Para WhatsApp abaixo de 16 MB: `crf 24` e 1280x720.

Conferir o tamanho e a duracao do arquivo final com ffprobe e **dizer o numero
medido**, nunca "ficou bom".

---

## 7. Loop

Para tela de recepcao que roda o dia inteiro:

- O ultimo plano precisa emendar no primeiro sem salto. O arco circular
  (terminar no enquadramento inicial) resolve isso.
- Sem cartela de fecho com texto, ou o loop fica piscando texto.
- Sem fade para preto no fim: vira uma piscada preta a cada volta.
- Conferir rodando o video duas vezes seguidas e olhando a emenda.
