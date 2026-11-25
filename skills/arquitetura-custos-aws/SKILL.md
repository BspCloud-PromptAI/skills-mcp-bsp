---
name: arquitetura-custos-aws
description: Levanta a infraestrutura AWS real de um projeto lendo a conta com o perfil do usuário, desenha a arquitetura no Lucid com ícones AWS 2024 no padrão BSP (o dos diagramas do Conecta e do Radar) e monta a calculadora de custo mensal com a AWS Pricing API e o uso medido no CloudWatch (planilha .xlsx com fórmulas, relatório .md e script para recalcular). Use quando o usuário pedir arquitetura ou diagrama AWS de um projeto, desenho no Lucid, levantamento ou revisão de infraestrutura, estimativa de custo ou calculadora AWS.
---

# Arquitetura AWS no Lucid e calculadora de custos (padrão BSP)

Três entregas por projeto, sempre a partir da conta real; nada inventado:

| Entrega | Onde salvar (dentro da pasta do projeto) |
|---|---|
| Levantamento técnico | `arquitetura/ARQUITETURA-<PROJETO>-AWS.md` |
| Diagrama no Lucid e gerador | `arquitetura/gerar-diagrama-lucid.py`, `diagrama-<projeto>-lucid.json`, `DIAGRAMA-LUCID.md` |
| Calculadora de custos | `custos/calcular_custos.py`, `precos-aws.json`, `uso-medido.json`, `calculadora-custos-<projeto>.xlsx`, `CUSTOS-<PROJETO>.md` |

Referência de qualidade, aprovada pelo usuário:
- Diagrama do Radar: https://lucid.app/lucidchart/e03b2a92-7b41-4251-816a-51010c2cc027/edit
- Diagrama do Conecta: https://lucid.app/lucidchart/85a74f75-18d4-4543-95bf-19ab8cfdf1a7/edit

Exporte um deles em PNG (`lucid_export_document_as_PNG`) antes de desenhar e imite o padrão.

Arquivos desta skill (caminhos relativos à pasta da skill):
- `referencias/levantamento-aws.md`: o que consultar na conta, comandos e achados de segurança.
- `referencias/layout-lucid.md`: padrão visual, grade, ícones, linhas, peculiaridades do Lucid e checklist do PNG.
- `referencias/precos-pricing-api.md`: catálogo de códigos de serviço e tipos de uso da Pricing API, com as armadilhas.
- `referencias/medicao-uso.md`: métricas e APIs para medir 30 dias de uso de cada componente.
- `modelos/gerar_diagrama_lucid.py`: o gerador do Radar, para copiar e adaptar.
- `modelos/calcular_custos.py`: a calculadora do Radar, para copiar e adaptar.
- `modelos/validar_planilha.py`: valida as fórmulas sem LibreOffice.
- `exemplos/`: documentos prontos do Radar e o gerador do Conecta, que tem a variante com zonas em colunas.

## 0. Antes de começar

- Ferramenta: Lucid (MCP `lucid`), **nunca Miro**. O MCP exige ler `lucid://skills/readme` e `lucid://skills/diagram-specification` antes de criar.
- Confirme só o que faltar:
  - perfil AWS e região;
  - o que é "o projeto" (prefixos e nomes dos recursos);
  - pasta do projeto;
  - se há documento Lucid existente (link) ou se é para criar um novo.
- Leia antes a documentação do projeto: `CLAUDE.md`, README, `buildspec.yml`, IaC e diagramas antigos. Trate tudo isso como hipótese a conferir na conta.
- **Só leitura por padrão.** Criar, alterar ou apagar recursos só com pedido explícito do usuário para aquela ação. Ler dados de banco de cliente também precisa de autorização para a ação.
- **Nunca imprima segredo**: compare valores em memória e imprima só verdadeiro ou falso. Scripts de inspeção ficam em `%TEMP%` e são apagados no fim.
- Use uma lista de tarefas com: levantamento, desenho, validação, ajustes, calculadora, documentação.

## 1. Levantamento (detalhes em `referencias/levantamento-aws.md`)

1. **Mapeie por camada, com nomes reais:**
   - entrada: Route 53, Amplify ou CloudFront, ALB (listeners, WAF, ACM);
   - computação: serviços e task definitions do ECS, agendamentos;
   - rede: VPC, sub-redes públicas e privadas por zona, tabelas de rota, IGW, NAT (zonal ou regional), Transit Gateway ou peering, endpoints, security groups com as regras;
   - dados: RDS, S3, bancos em outra conta;
   - IA: Bedrock, com os modelos tirados das dimensões das métricas;
   - esteira: CodePipeline, CodeBuild, ECR, Amplify;
   - segurança: Secrets Manager (só nomes), papéis IAM, GuardDuty;
   - operação: logs, alarmes, SNS.
2. **Confira onde cada coisa roda de verdade:** sub-rede, IP público, papel da tarefa, caminho até o banco. A documentação antiga do Radar errava a sub-rede da API.
3. **Separe o que é compartilhado com outros projetos.** Olhe as ENIs da VPC, as tags `Project`, o NAT, o TGW, a zona DNS e os papéis usados por várias famílias de task definition.
4. **Procure e avise na hora os achados de segurança:**
   - credenciais em texto puro na task definition;
   - chave de acesso fixa;
   - papéis com `AdministratorAccess`;
   - banco público;
   - SG aberto;
   - ALB sem WAF;
   - nenhum alarme;
   - ECR sem scan.

   Não corrija sem pedido. Se o usuário pedir que o diagrama mostre o estado corrigido, desenhe assim e faça a correção como tarefa à parte, testando antes da troca.
5. **Escreva o `ARQUITETURA-<PROJETO>-AWS.md`** (modelo: `exemplos/radar/ARQUITETURA-RADAR-AWS.md`):
   - componentes por camada;
   - tabela de sub-redes;
   - fluxos numerados;
   - o que for incerto dito como incerto (ex.: "sem flow logs, não dá para afirmar o caminho");
   - pendências.

## 2. Diagrama no Lucid (detalhes em `referencias/layout-lucid.md`)

1. **Planeje a grade antes de escrever o JSON.**
   - O eixo vertical principal vai dos usuários ao banco: usuários → internet gateway → ALB → serviço → banco.
   - À esquerda, os grupos da esteira de deploy e de segurança e operação.
   - À direita, a coluna de serviços regionais (Bedrock, S3, Scheduler).
   - Embaixo, a outra conta (banco do cliente).
   - Por último, o rodapé com "Como funciona", "Segurança e operação" e "Pendências".
   - Aplique a **regra do ciclo** e a das faixas de título (estão na referência).
2. **Gere o JSON** com Python, a partir de `modelos/gerar_diagrama_lucid.py`:
   - funções `icone`, `grupo`, `rotulo`, `linha`;
   - fontes em pt;
   - rótulo ao lado do ícone, com título em 8pt negrito e corpo em 7pt, em `<p>` separados.
3. **Valide** com `lucid_validate_diagram_specification`.
   - Zere os erros.
   - Ignore os avisos text-fit e shape-clearance entre ícone e o próprio rótulo.
   - Confirme que não sobrou connector-path-clearance nem label-placement.
4. **Crie** com `lucid_create_diagram_from_specification` e `use_assisted_layout=false`.
5. **Ajuste por RunScript** (carregue a documentação de `basecanvasediting`, `text` e `lines` com o `document_id`):
   - `setText({itemId, text: ""})` em todos os ícones: o nome padrão aparece mesmo com `"text": ""` no JSON;
   - `setTextAlignment({textVAlign: "top"})` nos blocos do rodapé;
   - `validateCanvas` com `blockOverlap`, `lineThroughBlock`, `lineTextOverlapsBlock`, `textOverflow` e `disconnectedEndpoint`;
   - correções pontuais: alargar o bloco que transborda e mover o rótulo de linha com `lines.setTextPosition`.
6. **Exporte o PNG, revise** com a checklist da referência e itere até ficar limpo.
7. **Leve cada ajuste de volta ao gerador**, que precisa reproduzir o documento.
8. **Escreva o `DIAGRAMA-LUCID.md`** (modelo em `exemplos/radar/`) com os links, o que o diagrama mostra, o que mudou e como regenerar.
9. **Ao substituir um documento antigo**, renomeie-o com o prefixo "[obsoleto]" (`lucid_update_document_metadata`) em vez de apagar.

## 3. Calculadora de custos

Os detalhes estão em `referencias/precos-pricing-api.md` e `referencias/medicao-uso.md`.

1. **Copie e adapte** `modelos/calcular_custos.py`: as constantes (perfil, região, nomes dos recursos), `PRECOS`, `medir()`, `montar_premissas()` e `montar_itens()`. Mantenha a estrutura.
2. **Preços só da AWS Pricing API** (`aws pricing get-products --region us-east-1`).
   - Um item por dimensão cobrada.
   - Filtro exato por `usagetype` e faixa inicial.
   - A checagem de ambiguidade faz o script parar se o filtro devolver preços diferentes.
   - Antes de fixar um filtro novo, explore com `describe-services` e o filtro `CONTAINS`.
3. **Uso medido nos últimos 30 dias** (CloudWatch e as APIs de cada serviço). O que não dá para medir vira premissa, com origem escrita ("Premissa: …").
4. **Separe três grupos.**
   - `Projeto` (o nome do projeto, ex.: "Radar"): recursos exclusivos.
   - `Compartilhado`: NAT, TGW, zona DNS, IPs do NAT. Entra com o valor cheio e uma premissa de rateio, que começa em 0.
   - Fora da conta: só uma nota, sem custo na conta.

   Franquias grátis divididas com outros sistemas não são descontadas por padrão (premissa 0).
5. **Monte a planilha** seguindo a skill `anthropic-skills:xlsx`.
   - Abas `Resumo`, `Itens`, `Premissas` e `Precos`.
   - Nomes definidos `u_*` para as premissas e `p_*` para os preços.
   - Quantidade = fórmula das premissas; custo = quantidade × preço.
   - `Resumo` com `SUMIFS` por grupo e por serviço, mais uma linha em R$ se a cotação for preenchida.
   - Entradas em azul, ligações entre abas em verde, fundo amarelo nas premissas que mais pesam.
   - Arial e `fullCalcOnLoad`.
   - Rode com `uv run --quiet --no-project --with openpyxl python -I calcular_custos.py`, sem instalar nada no Python do usuário.
6. **Valide** com `uv run --quiet --no-project --with formulas --with openpyxl python -I modelos/validar_planilha.py <xlsx>`. O resultado precisa ter zero células com erro e totais iguais aos do script. Sem LibreOffice, este é o recálculo.
7. **Escreva o relatório `CUSTOS-<PROJETO>.md`** em pt-BR, com vírgula decimal e sem notação científica: resumo, por serviço, itens, uso que mais pesa, o que ficou fora do cálculo e como recalcular.
8. **Confira à mão 2 ou 3 linhas** (ex.: 730 h × 0,5 vCPU × US$ 0,03238 = US$ 11,82).

## 4. Fechamento

- Ligue os documentos entre si: arquitetura ↔ diagrama ↔ custos.
- Atualize o `CLAUDE.md` do projeto com o estado datado, os links e as pendências.
- Responda ao usuário com:
  - o link do diagrama;
  - o que estava errado ou mudou;
  - os achados de segurança;
  - o total mensal exclusivo e o compartilhado, com os maiores itens;
  - as premissas que mais pesam;
  - o que depende de decisão dele.

## Regras que valem sempre

1. **Nada inventado.** Nome, CIDR, porta, tamanho e preço vêm da conta ou da Pricing API. O que não deu para confirmar aparece como incerto.
2. **Português do Brasil** no diagrama, nos documentos e na planilha. Textos para leitura de diretoria, sem siglas soltas.
3. **Lucid, nunca Miro.** Ícones AWS 2024 do catálogo do MCP (`lucid://shape-libraries/aws-2024/<categoria>`). Nunca adivinhe o nome da classe.
4. **Segurança:** leitura por padrão, nenhum segredo impresso, correção só com pedido. Antes de trocar algo em produção, teste numa tarefa avulsa.
5. **Diagrama legível acima de tudo:**
   - nenhuma linha atravessa ícone, rótulo ou título de grupo;
   - nenhum contêiner sobreposto;
   - security group vira regra no rótulo, não caixa;
   - nenhum nome padrão de ícone visível.
6. **Custos rastreáveis:** cada preço tem SKU e vigência na aba `Precos`, e cada quantidade tem origem na aba `Premissas`.
