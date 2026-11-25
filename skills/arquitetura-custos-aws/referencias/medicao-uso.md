# Medição do uso (últimos 30 dias)

Para o que se mede pela métrica, use `get-metric-statistics` com `--period 86400` e a estatística indicada:
`Sum` para contagens e bytes, `Average` para LCU e tamanhos. Converta bytes para GB com 2^30.

Ponto de partida sempre: `list-metrics` para descobrir as dimensões reais. Exemplo do NAT regional, que vem por zona:

```bash
aws cloudwatch list-metrics --namespace AWS/NATGateway --dimensions Name=NatGatewayId,Value=<nat> --query 'Metrics[].[MetricName,Dimensions[].Name|join(`,`,@)]'
```

## Por componente

| Componente | Fonte | Métrica e dimensões | O que vira na calculadora |
|---|---|---|---|
| Serviço ECS (API) | `ecs describe-services` + task definition | `desiredCount`, `cpu/1024`, `memory/1024` | tarefas × vCPU × 730 h |
| Job agendado | `logs describe-log-streams` do grupo do job (ordem por `LastEventTime`) | duração = último evento − primeiro evento | execuções por mês (premissa pela agenda) × (duração + 1 min para baixar a imagem e subir) |
| ALB | AWS/ApplicationELB, `LoadBalancer=app/<nome>/<id>` | `ConsumedLCUs` (Average), `ProcessedBytes` (Sum), `RequestCount` (Sum) | LCU médio × 730; `ProcessedBytes` como teto da saída para a internet |
| IPv4 públicos | `ec2 describe-network-interfaces` | ENIs do ALB (`Name=description,Values=ELB app/<nome>/<id>`), ENI da tarefa (pelo `describe-tasks`), banco com `PubliclyAccessible` | IPs × 730 h |
| NAT | AWS/NATGateway, `NatGatewayId` e `AvailabilityZone` | `BytesOutToDestination` + `BytesOutToSource` (Sum, somado por zona) | GB processados (toda a VPC); zonas ativas × 730 h |
| RDS | `rds describe-db-instances`; AWS/RDS, `DBInstanceIdentifier` | `AllocatedStorage`, `StorageType`, `TotalBackupStorageBilled` (último valor) | GB do armazenamento; GB de backup cobrado |
| S3 | AWS/S3, `BucketName` e `StorageType=StandardStorage` / `AllStorageTypes` | `BucketSizeBytes`, `NumberOfObjects` (último valor diário) | GB-mês. Requisições viram premissa se o bucket não tiver métricas de requisição. |
| ECR | `ecr describe-images` | soma de `imageSizeInBytes` | GB-mês. Avise se não houver política de limpeza. |
| CloudWatch Logs | AWS/Logs, `LogGroupName`; `logs describe-log-groups` | `IncomingBytes` (Sum), `storedBytes` | GB ingeridos; GB guardados |
| Secrets Manager | `secretsmanager list-secrets` com o prefixo do projeto | contagem | segredos; chamadas como premissa |
| CodeBuild | `codebuild list-builds-for-project` + `batch-get-builds` | soma do teto em minutos de cada build | minutos por mês |
| CodePipeline V2 | `codepipeline list-action-executions` | soma do teto em minutos de cada ação (`startTime` → `lastUpdateTime`) | minutos de ação |
| Amplify | `amplify list-jobs` (branch); AWS/AmplifyHosting, `App` | duração dos builds; `Requests`, `BytesDownloaded` (Sum) | minutos de build, GB servidos e requisições. A parcela SSR e a duração viram premissas. |
| Bedrock | AWS/Bedrock, `ModelId` (o id do perfil, ex.: `global.anthropic.claude-sonnet-5`) | `InputTokenCount`, `OutputTokenCount`, `CacheReadInputTokenCount`, `CacheWriteInputTokenCount`, `Invocations` (Sum) | milhões de tokens por tipo. Avise que a métrica soma todos os sistemas que usam o perfil. |
| GuardDuty Fargate | derivado | (vCPU da API × 730 + vCPU-hora do job) / 730 | vCPU-mês |
| Alarmes | `cloudwatch describe-alarms --alarm-name-prefix <projeto>` | contagem | alarme-mês |
| Transit Gateway | métricas na conta dona do TGW | geralmente sem acesso | premissa 0, marcada "sem medição" |

## Cuidados

- **Datas:** neste CLI, `startTime` vem como epoch (número) no ECS e no CodePipeline e como ISO no CodeBuild e no
  Amplify. Trate os dois.
- **Tarefas paradas:** o ECS só guarda tarefas paradas por cerca de 1 hora. A duração do job sai do log, não do
  `describe-tasks`.
- **Contagem de execuções:** conta também as manuais. Para o mês típico, use a agenda (ex.: 30 execuções) e escreva
  a contagem medida na origem da premissa.
- **Métrica de filtro de log:** só conta eventos posteriores à criação do filtro. Para um alarme novo de "rodou com
  sucesso", registre a última conclusão real com `put-metric-data`, usando o timestamp do evento encontrado com
  `filter-log-events`.
- **Atribuição:** recurso compartilhado (NAT, TGW, zona DNS, IPs do NAT) vai para o grupo `Compartilhado` com o
  valor cheio, mesmo que o tráfego do projeto seja pequeno.
- **Origem da premissa:** escreva o que foi medido, de onde veio e a janela ("Medido em 12/11/2026, últimos 30 dias:
  ConsumedLCUs (média)").
