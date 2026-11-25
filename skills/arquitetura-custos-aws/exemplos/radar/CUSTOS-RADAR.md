# Radar de Perdas: custo mensal na AWS

- Conta athie-digital-prod (912668123297), us-east-1. Levantado em 12/11/2026.
- Preços: AWS Pricing API (`pricing:GetProducts`), sob demanda, sem impostos, créditos ou descontos.
- Uso: medido nos últimos 30 dias (CloudWatch, ECS, ECR, CodeBuild, CodePipeline, Amplify); o que não dá para medir está marcado como premissa na planilha.
- Calculadora editável: [calculadora-custos-radar.xlsx](./calculadora-custos-radar.xlsx). Arquitetura: [../arquitetura/ARQUITETURA-RADAR-AWS.md](../arquitetura/ARQUITETURA-RADAR-AWS.md).

## Resumo

| Total por mês | US$ |
|---|---:|
| **Radar: recursos exclusivos** | **US$ 71,24** |
| Infra compartilhada da VPC e da conta (valor cheio, atende outros sistemas) | US$ 193,55 |

A infra compartilhada (NAT regional do digital-lab, anexo do Transit Gateway e zona do Route 53) não entra no total do Radar. A planilha tem uma premissa de rateio para atribuir uma parte dela.

## Por serviço (recursos exclusivos)

| Serviço | US$ por mês | Parte |
|---|---:|---:|
| VPC | US$ 18,25 | 26% |
| Elastic Load Balancing | US$ 16,43 | 23% |
| ECS Fargate | US$ 14,45 | 20% |
| RDS | US$ 13,98 | 20% |
| Bedrock | US$ 3,95 | 6% |
| Secrets Manager | US$ 1,20 | 2% |
| GuardDuty | US$ 0,75 | 1% |
| Amplify | US$ 0,69 | 1% |
| ECR | US$ 0,57 | 1% |
| CodePipeline | US$ 0,50 | 1% |
| CodeBuild | US$ 0,42 | 1% |
| S3 | US$ 0,03 | 0% |
| Transferência de dados | US$ 0,01 | 0% |
| CloudWatch | US$ 0,01 | 0% |
| EventBridge Scheduler | US$ 0,00 | 0% |

## Itens

| Grupo | Componente | Quantidade por mês | Preço (US$) | US$ por mês |
|---|---|---:|---:|---:|
| Radar | API: vCPU | 365 vCPU-hora | 0,03238 | US$ 11,82 |
| Radar | API: memória | 730 GB-hora | 0,00356 | US$ 2,60 |
| Radar | Job diário: vCPU | 0,765 vCPU-hora | 0,03238 | US$ 0,02 |
| Radar | Job diário: memória | 3,06 GB-hora | 0,00356 | US$ 0,01 |
| Radar | Monitoramento das tarefas | 0,501 vCPU-mês | 1,5 | US$ 0,75 |
| Radar | ALB: horas | 730 hora | 0,0225 | US$ 16,43 |
| Radar | ALB: capacidade (LCU) | 0,00803 LCU-hora | 0,008 | US$ 0,00 |
| Radar | IPv4 públicos (ALB, API e banco do chat) | 3.650 IP-hora | 0,005 | US$ 18,25 |
| Radar | Saída de dados para a internet | 0,114 GB | 0,09 | US$ 0,01 |
| Radar | Banco do chat: instância db.t4g.micro | 730 hora | 0,016 | US$ 11,68 |
| Radar | Banco do chat: armazenamento gp2 | 20 GB-mês | 0,115 | US$ 2,30 |
| Radar | Banco do chat: backup acima da franquia | 0 GB-mês | 0,095 | US$ 0,00 |
| Radar | Resultados: armazenamento | 0,3467 GB-mês | 0,023 | US$ 0,01 |
| Radar | Resultados: PUT, COPY e LIST | 3.000 requisição | 0,000005 | US$ 0,02 |
| Radar | Resultados: GET | 30.000 requisição | 0,0000004 | US$ 0,01 |
| Radar | Imagens da API e do job | 5,723 GB-mês | 0,1 | US$ 0,57 |
| Radar | Logs: ingestão | 0,0156 GB | 0,5 | US$ 0,01 |
| Radar | Logs: armazenamento | 0,0141 GB-mês | 0,03 | US$ 0,00 |
| Radar | Segredos | 3 segredo-mês | 0,4 | US$ 1,20 |
| Radar | Chamadas aos segredos | 300 chamada | 0,000005 | US$ 0,00 |
| Radar | Front-end: minutos de build | 55 minuto | 0,01 | US$ 0,55 |
| Radar | Front-end: artefatos guardados | 1 GB | 0,023 | US$ 0,02 |
| Radar | Front-end: dados servidos | 0,032 GB | 0,15 | US$ 0,00 |
| Radar | Front-end: requisições SSR | 4.078 requisição | 0,0000003 | US$ 0,00 |
| Radar | Front-end: duração SSR | 2.039 GB-segundo | 0,0000555556 | US$ 0,11 |
| Radar | Build da imagem | 124 minuto | 0,0034 | US$ 0,42 |
| Radar | Pipeline V2 | 248 minuto | 0,002 | US$ 0,50 |
| Radar | Agendamento do job | 0 invocação | 0,000001 | US$ 0,00 |
| Radar | Claude Sonnet 5: tokens de entrada | 0,008666 milhão de tokens | 2 | US$ 0,02 |
| Radar | Claude Sonnet 5: tokens de saída | 0,1971 milhão de tokens | 10 | US$ 1,97 |
| Radar | Claude Sonnet 5: tokens de leitura de cache | 1,207 milhão de tokens | 0,2 | US$ 0,24 |
| Radar | Claude Sonnet 5: tokens de escrita de cache | 0,6863 milhão de tokens | 2,5 | US$ 1,72 |
| Radar | Claude Haiku 5.5: tokens de entrada | 0,000017 milhão de tokens | 0,1 | US$ 0,00 |
| Radar | Claude Haiku 5.5: tokens de saída | 0,000004 milhão de tokens | 0,5 | US$ 0,00 |
| Radar | Claude Haiku 5.5: tokens de leitura de cache | 0 milhão de tokens | 0,01 | US$ 0,00 |
| Radar | Claude Haiku 5.5: tokens de escrita de cache | 0 milhão de tokens | 0,125 | US$ 0,00 |
| Compartilhado | NAT regional: horas por zona | 2.190 zona-hora | 0,045 | US$ 98,55 |
| Compartilhado | NAT regional: dados processados | 1.045 GB | 0,045 | US$ 47,01 |
| Compartilhado | NAT: IPs elásticos | 2.190 IP-hora | 0,005 | US$ 10,95 |
| Compartilhado | Transit Gateway: anexo da VPC | 730 hora | 0,05 | US$ 36,50 |
| Compartilhado | Transit Gateway: dados processados | 0 GB | 0,02 | US$ 0,00 |
| Compartilhado | Zona awdigitallab.com | 1 zona-mês | 0,5 | US$ 0,50 |
| Compartilhado | Consultas de DNS | 100.000 consulta | 0,0000004 | US$ 0,04 |

## Uso medido que mais pesa

- API: 1 tarefa de 0,5 vCPU e 1 GB o mês todo.
- ALB: 0,000011 LCU por hora em média e 27.615 requisições em 30 dias.
- Bedrock: Sonnet 5 com 8.666 tokens de entrada e 197.099 de saída; Haiku 5.5 com 17 e 4.
- Job: 16 execuções com log em 30 dias, 32 s em média.
- NAT regional: 3 zonas e 1.045 GB processados (toda a VPC).

## Fora do cálculo

- O RDS db-vetorial-prd-clean e o DMS ficam na conta athie-vector e são pagos pela Athié.
- Franquias grátis da conta (100 GB de saída e 100 minutos de CodePipeline por mês), porque são divididas com outros sistemas; Savings Plans, créditos, suporte da AWS e impostos.
- O Bedrock é medido por perfil de inferência: se outro sistema da conta usar o mesmo perfil, o consumo dele entra aqui.

## Como recalcular

```bash
MSYS_NO_PATHCONV=1 uv run --with openpyxl python -I calcular_custos.py
```

O script consulta a Pricing API e as métricas com o perfil `athie-digital-prod` e regrava os quatro arquivos desta pasta (`precos-aws.json`, `uso-medido.json`, a planilha e este relatório).
