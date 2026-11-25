---
name: gastos
description: Mostra o gasto de tokens e custo por modelo (ccusage). Sem argumento = hoje; aceite "semana" ou "mes".
argument-hint: [hoje | semana | mes]
allowed-tools: Bash(npx --yes ccusage@latest:*), Bash(node "$HOME/.claude/tools/kiro-ledger.mjs":*)
model: haiku
---

Relatórios do ccusage (já executados):

HOJE:
!`npx --yes ccusage@latest claude daily --last 1 --breakdown --compact`

SEMANA:
!`npx --yes ccusage@latest claude weekly --last 1 --breakdown --compact`

MÊS:
!`npx --yes ccusage@latest claude monthly --last 1 --breakdown --compact`

Consumo do Kiro (já executado, registrado pelo kiro-run):

KIRO HOJE:
!`node "$HOME/.claude/tools/kiro-ledger.mjs" hoje`

KIRO SEMANA:
!`node "$HOME/.claude/tools/kiro-ledger.mjs" semana`

KIRO MÊS:
!`node "$HOME/.claude/tools/kiro-ledger.mjs" mes`

Período pedido pelo usuário: "$ARGUMENTS" (vazio = hoje).

Instruções:
- Mostre SOMENTE a tabela do período pedido, exatamente como veio, seguida da linha "Kiro" do mesmo período (dos blocos KIRO), que não é da tabela do ccusage.
- Abaixo dela, em no máximo 3 linhas: a fatia de cada modelo (Opus / Sonnet / Haiku) em % dos tokens e do custo.
- Se algum custo aparecer como 0 ou vazio para modelos do Bedrock, avise em uma linha que o preço do modelo não foi reconhecido (os tokens continuam corretos).
- Não rode nenhum outro comando nem faça recomendações.
