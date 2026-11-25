# Modelos (copiados do Radar em 12/11/2026)

Copie para a pasta do projeto e adapte. A estrutura funcionou de ponta a ponta e foi aprovada pelo usuário.

Versões vivas, que podem ter avançado:
- `Projetos/radar/arquitetura/gerar-diagrama-lucid.py`
- `Projetos/radar/custos/calcular_custos.py`

## `gerar_diagrama_lucid.py` → `<projeto>/arquitetura/gerar-diagrama-lucid.py`

1. **Constantes da grade:**
   - `X_A`: eixo de usuários, IGW, ALB, API e banco;
   - `X_J`: job;
   - `X_R`: coluna de serviços regionais;
   - `X_P`: esteira;
   - `X_S`: grupo de segurança.
2. **Bloco "Contêineres":** contas, região, VPC, faixas de sub-rede e grupos genéricos, em ordem de fora para dentro.
3. **Ícones e rótulos:** um par `icone(...)` + `rotulo(...)` por componente, com nomes reais da conta.
4. **Rodapé:** listas `COMO`, `SEGURANCA` e `PENDENCIAS`, um item por fluxo numerado ou achado.
5. **Linhas:** `linha(id, origem, ponta, destino, ponta, tipo, tracejada, rotulo_, posicao)`, sempre com as pontas
   fixadas.
6. **Rodar:** `python -I gerar-diagrama-lucid.py > diagrama-<projeto>-lucid.json`.
7. **Depois:** validar, criar sem layout assistido e fazer os ajustes por RunScript (ver `SKILL.md`).

## `calcular_custos.py` → `<projeto>/custos/calcular_custos.py`

1. **Constantes:** `PERFIL`, `CLUSTER`, `BUCKET`, `NAT`, `APP_AMPLIFY`, `MODELOS` e os nomes de serviço, task
   definition, ALB, banco e grupos de log usados em `medir()`.
2. **`PRECOS`:** tire o que o projeto não usa e inclua o que faltar, com o filtro do catálogo
   (`referencias/precos-pricing-api.md`). O script para se um filtro devolver preços diferentes.
3. **`medir()`:** um bloco por componente, com a métrica de `referencias/medicao-uso.md`. Tudo vai para
   `uso-medido.json`.
4. **`montar_premissas()`:** `(chave, rótulo, valor, unidade, origem)`. As seções têm `rótulo=None`. Toda premissa
   vira o nome `u_<chave>`.
5. **`montar_itens()`:** `(grupo, componente, serviço, expressão, unidade, chave do preço)`.
   - A expressão usa só nomes `u_*`, números, `+ - * /` e `MAX(...)`.
   - É a mesma fórmula no Excel e no Python, e o relatório sai dela.
6. **Nome do projeto:** troque "Radar" nos grupos, títulos e relatório. O grupo exclusivo aparece nos `SUMIFS` do
   `Resumo` e em `montar_relatorio`.
7. **Rodar:** `MSYS_NO_PATHCONV=1 uv run --quiet --no-project --with openpyxl python -I calcular_custos.py`.

## `validar_planilha.py`

```bash
uv run --quiet --no-project --with formulas --with openpyxl python -I validar_planilha.py calculadora.xlsx "Resumo!B6=<total do script>"
```

Precisa sair com `células com erro: 0` e com os totais iguais aos do script. Sem LibreOffice nesta máquina, este é
o recálculo.
