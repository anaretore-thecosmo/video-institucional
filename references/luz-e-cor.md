# Luz, sombreamento e cor

Indice:
1. O que da para consertar e o que nao da
2. Ler o material antes de mexer
3. Ordem de ajuste
4. Casar drone com camera de solo
5. Receitas de filtro ffmpeg
6. Climas prontos

---

## 1. O que da para consertar e o que nao da

| Problema | Da para consertar? |
|---|---|
| Sombra fechada demais (escuro, mas com informacao) | Sim, levantando sombras |
| Branco estourado (255 chapado) | **Nao.** A informacao nao foi gravada |
| Temperatura errada (azulado ou amarelado) | Sim, quase sempre |
| Contraste baixo / imagem lavada | Sim |
| Saturacao exagerada da camera | Sim, reduzindo |
| Ruido de ISO alto | Parcialmente, e custa nitidez |
| Foco errado | Nao |

Dizer isso ao usuario de forma direta quando o script apontar ESTOURADO: nao
prometer recuperacao que nao existe.

---

## 2. Ler o material antes de mexer

Usar os numeros do `inspecionar_brutos.py`:

- `brilho_medio` perto de 110-130 = exposicao saudavel.
- `brilho_medio` abaixo de 60 = subexposto; levantar sombras e meio-tom.
- `brilho_max` colado em 255 com `fracao_estourada` alta = ha estouro real.
- `brilho_min` bem acima de 0 = imagem lavada; falta preto, abaixar sombras.

Comparar os numeros ENTRE os takes. A diferenca entre eles importa mais que o
valor absoluto de cada um: e a diferenca que o olho percebe no corte.

---

## 3. Ordem de ajuste

Sempre nesta ordem. Trocar a ordem produz resultado sujo.

1. **Ponto de preto e de branco** - definir onde comeca o preto e onde termina
   o branco, sem estourar.
2. **Exposicao geral** - subir ou descer o meio-tom.
3. **Contraste** - separar claro e escuro.
4. **Temperatura e matiz** - tirar o azulado ou o amarelado.
5. **Saturacao** - por ultimo, e com a mao leve.
6. **Clima** (o "sombreamento" propriamente dito) - inclinar sombras e altas
   para uma direcao de cor.

Regra de ouro: se o ajuste esta obvio, esta forte demais. Tirar metade.

---

## 4. Casar drone com camera de solo

Esse e o problema de cor mais comum em institucional, e o que mais entrega
montagem amadora. Drone e camera de solo tem sensores e perfis diferentes:
o drone costuma sair mais frio, mais contrastado e mais saturado no azul.

Procedimento:

1. Escolher **um** take como referencia - normalmente o mais importante do
   video, geralmente da camera de solo com gente.
2. Medir `brilho_medio` dos dois grupos com o script.
3. Aproximar o drone da referencia, nao o contrario: costuma pedir
   temperatura mais quente, saturacao um pouco menor e sombras um pouco mais
   abertas.
4. Conferir num corte direto entre um plano de cada. Se o olho percebe a
   troca de camera, ainda nao casou.

Aplicar o ajuste por bloco, usando o campo `cor` do bloco no plano de montagem.

---

## 5. Receitas de filtro ffmpeg

Entram no campo `cor` de um bloco (so aquele bloco) ou no campo `cor` do plano
inteiro (todos). Encadear com virgula.

**Levantar sombras sem estourar o branco:**
```
curves=all='0/0.06 0.25/0.34 0.5/0.55 1/1'
```

**Exposicao e saturacao (eq):**
```
eq=brightness=0.05:contrast=1.08:saturation=1.05
```
brightness vai de -1 a 1 (mexer entre -0.1 e 0.1); contrast e saturation em
torno de 1.0. Passar de 1.2 em saturation ja fica artificial.

**Esquentar (tirar o azulado tipico de drone):**
```
colorbalance=rs=0.04:gs=0.01:bs=-0.05
```
rs/gs/bs mexem nas sombras; rm/gm/bm nos meios; rh/gh/bh nas altas.

**Esfriar:**
```
colorbalance=rs=-0.04:bs=0.05
```

**Dar preto real a uma imagem lavada:**
```
curves=all='0.04/0 0.5/0.5 0.96/1'
```

**Proteger o branco de estourar depois de subir exposicao:**
```
curves=all='0/0 0.5/0.54 0.85/0.88 1/0.98'
```

**Aplicar uma LUT, se o usuario tiver uma:**
```
lut3d=filename=caminho/para/arquivo.cube
```

Conferir sempre depois: rodar o `inspecionar_brutos.py` no resultado e checar
que `fracao_estourada` nao subiu.

---

## 6. Climas prontos

Combinacoes testaveis, para oferecer ao usuario em linguagem simples.

**Manha clara** (leve, arejado, para ambiente e bastidores):
```
eq=brightness=0.03:contrast=1.05:saturation=1.02,colorbalance=rs=0.02:bh=0.02
```

**Fim de tarde quente** (acolhedor, para quem somos e perfil):
```
colorbalance=rs=0.05:rm=0.03:bs=-0.04,eq=contrast=1.06:saturation=1.06
```

**Sobrio corporativo** (serio, pouca cor, para manifesto e retrospectiva):
```
eq=contrast=1.12:saturation=0.9,curves=all='0.03/0 0.5/0.5 1/0.97'
```

**Noite urbana** (contraste alto, sombras azuis):
```
colorbalance=bs=0.06:rh=0.03,eq=contrast=1.15:brightness=-0.02
```

**Neutro** (nao mexe; usar quando o material ja esta tratado):
```
(deixar o campo cor vazio)
```

Apresentar esses nomes ao usuario, nunca os comandos.
