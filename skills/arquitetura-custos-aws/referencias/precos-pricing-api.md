# Preços pela AWS Pricing API

- A API só responde em `us-east-1`, `eu-central-1` ou `ap-south-1`. Chame com `--region us-east-1`, seja qual for a
  região do projeto, e filtre a região do recurso pelo `location`.
- Preço sempre **sob demanda** (`terms.OnDemand`). Guarde o SKU e a `effectiveDate` de cada item na aba `Precos`.

## Como achar o filtro certo

```bash
aws pricing describe-services --region us-east-1 --service-code <Codigo>          # nomes dos atributos
aws pricing get-attribute-values --region us-east-1 --service-code <Codigo> --attribute-name usagetype
aws pricing get-products --region us-east-1 --service-code <Codigo> --max-items 40 \
  --filters '[{"Type":"TERM_MATCH","Field":"location","Value":"US East (N. Virginia)"},{"Type":"CONTAINS","Field":"usagetype","Value":"<trecho>"}]'
```

- **Filtros em JSON.** Com a sintaxe curta (`Type=…,Field=…,Value=a,b`), o CLI transforma o valor em lista e quebra
  o `ANY_OF`.
- **Tipos de filtro:** `TERM_MATCH` (exato), `CONTAINS`, `ANY_OF` e `NONE_OF`.
- **Faixas:** um produto pode ter várias (`beginRange` "0", "14000000" etc.). Escolha a que se aplica ao uso.
- **Variantes com o mesmo preço:** é comum o mesmo `usagetype` aparecer em várias (por `operation`). O script aceita
  quando todas têm o mesmo preço e **para** quando há preços diferentes. Nesse caso, refine com `trecho` (parte da
  descrição) ou com outro atributo.
- **Prefixo regional:** em us-east-1, alguns tipos de uso não têm o prefixo `USE1-` (ex.: `LoadBalancerUsage`,
  `TimedStorage-ByteHrs` do S3 e do ECR, `HostedZone`). Em outras regiões, o prefixo muda (ex.: `SAE1-` em São
  Paulo).

## Catálogo usado no Radar (us-east-1, consultado em 12/11/2026)

Os preços servem para conferir a ordem de grandeza. A calculadora sempre busca o valor do dia.

| Chave | Código | `usagetype` e filtros extras | Unidade | Preço |
|---|---|---|---|---|
| `fargate_vcpu` | AmazonECS | `USE1-Fargate-ARM-vCPU-Hours:perCPU` | vCPU-hora | 0,03238 |
| `fargate_gb` | AmazonECS | `USE1-Fargate-ARM-GB-Hours` | GB-hora | 0,00356 |
| (x86) | AmazonECS | `USE1-Fargate-vCPU-Hours:perCPU`, `USE1-Fargate-GB-Hours` | — | conferir |
| `guardduty_fargate` | AmazonGuardDuty | `USE1-PaidFargatevCPUMonitored`, faixa 0 | vCPU-mês | 1,50 (até 500) |
| `alb_hora` | AWSELB | `LoadBalancerUsage` + `productFamily=Load Balancer-Application` | hora | 0,0225 |
| `alb_lcu` | AWSELB | `LCUUsage` + `productFamily=Load Balancer-Application` | LCU-hora | 0,008 |
| `ipv4` | AmazonVPC | `USE1-PublicIPv4:InUseAddress` | IP-hora | 0,005 |
| `nat_hora` (regional) | AmazonEC2 | `RegionalNatGateway-Hours` | hora por zona ativa | 0,045 |
| `nat_gb` (regional) | AmazonEC2 | `USE1-RegionalNatGateway-Bytes` | GB | 0,045 |
| NAT zonal | AmazonEC2 | `USE1-NatGateway-Hours` e `USE1-NatGateway-Bytes` | — | 0,045 |
| `tgw_hora` | AmazonVPC | `USE1-TransitGateway-Hours` + trecho "VPC Attachment Hour" | hora | 0,05 |
| `tgw_gb` | AmazonVPC | `USE1-TransitGateway-Bytes` + trecho "VPC Attachment" | GB | 0,02 |
| `rds_hora` | AmazonRDS | `InstanceUsage:db.t4g.micro` + `databaseEngine=PostgreSQL` + `deploymentOption=Single-AZ` | hora | 0,016 |
| `rds_gp2` | AmazonRDS | `RDS:GP2-Storage` + PostgreSQL + Single-AZ (gp3: `RDS:GP3-Storage`) | GB-mês | 0,115 |
| `rds_backup` | AmazonRDS | `RDS:ChargedBackupUsage` + PostgreSQL + Single-AZ | GB-mês acima da franquia | 0,095 |
| `s3_gb` | AmazonS3 | `TimedStorage-ByteHrs`, faixa 0 | GB-mês | 0,023 |
| `s3_put` | AmazonS3 | `Requests-Tier1` | requisição | 0,000005 |
| `s3_get` | AmazonS3 | `Requests-Tier2` | requisição | 0,0000004 |
| `ecr_gb` | AmazonECR | `TimedStorage-ByteHrs` | GB-mês | 0,10 |
| `logs_ingestao` | AmazonCloudWatch | `USE1-DataProcessing-Bytes` + trecho "ingested in Standard" | GB | 0,50 |
| `logs_armazenamento` | AmazonCloudWatch | `USE1-TimedStorage-ByteHrs` | GB-mês | 0,03 |
| alarme | AmazonCloudWatch | `CW:AlarmMonitorUsage` | alarme-mês | 0,10 |
| `segredo` | AWSSecretsManager | `USE1-AWSSecretsManager-Secrets` | segredo-mês | 0,40 |
| `segredo_api` | AWSSecretsManager | `USE1-AWSSecretsManagerAPIRequest` | chamada | 0,000005 |
| `r53_zona` | AmazonRoute53 | `HostedZone`, faixa 0, sem `location` | zona-mês | 0,50 |
| `r53_consulta` | AmazonRoute53 | `DNS-Queries`, faixa 0, sem `location` | consulta | 0,0000004 |
| `amplify_build` | AWSAmplify | `USE1-BuildDuration` | minuto | 0,01 |
| `amplify_armazenamento` | AWSAmplify | `USE1-DataStorage` | GB | 0,023 |
| `amplify_transferencia` | AWSAmplify | `USE1-DataTransferOut` | GB | 0,15 |
| `amplify_requisicao` | AWSAmplify | `USE1-HostingComputeRequestCount` | requisição SSR | 0,0000003 |
| `amplify_gb_segundo` | AWSAmplify | `USE1-HostingComputeRequestDuration` | GB-segundo | 0,0000556 |
| `codebuild_minuto` | CodeBuild | `USE1-Build-Min:ARM:g1.small` (x86: `USE1-Build-Min:Linux:g1.small`, conferir) | minuto | 0,0034 |
| `codepipeline_minuto` | AWSCodePipeline | `USE1-actionExecutionMinute` (V2; a V1 cobra `USE1-activePipeline`) | minuto de ação | 0,002 |
| `scheduler` | AWSEvents | `USE1-ScheduledInvocation`, faixa 14000000 | invocação | 0,000001 (os primeiros 14 milhões são grátis) |
| `saida_internet` | AWSDataTransfer | `DataTransfer-Out-Bytes` + `fromLocation=US East (N. Virginia)` + `transferType=AWS Outbound`, faixa 0, sem `location` | GB | 0,09 |
| Claude (cada tipo) | AmazonBedrockFoundationModels | `USE1-MP:USE1_<tipo>_global_standard-Units` + `model=<nome>`, sem `location` | milhão de tokens | ver abaixo |

**Claude no Bedrock (Marketplace).** Os tipos são `input_tokens`, `output_tokens`, `cache_read_tokens`,
`cache_write_tokens` e `cache_write_tokens_1h`. Preços globais por milhão de tokens em 12/11/2026:

| Modelo | Entrada | Saída | Leitura de cache | Escrita de cache (5 min) |
|---|---|---|---|---|
| Claude Sonnet 5 | 2,00 | 10,00 | 0,20 | 2,50 |
| Claude Haiku 5.5 | 0,10 | 0,50 | 0,01 | 0,125 |

- **Perfil regional:** sem `_global` no tipo de uso, custa cerca de 10% a mais.
- **Contexto longo:** tem variantes `_long_ctx_`.
- **Nome do modelo:** vem do atributo `model` (ex.: "Claude Sonnet 5", "Claude Haiku 5.5", "Claude Opus 5.5").
- **Modelos antigos** (Claude 2, 3 e Instant) ficam no código `AmazonBedrock`, por 1.000 tokens.

## Armadilhas que já custaram tempo

- **NAT regional:** não tem `SubnetId`, tem um IP por zona e as métricas vêm por zona. Cobra a hora **por zona
  ativa**: no Radar foram 3 × 730 h × 0,045 = US$ 98,55. Conte as zonas pela dimensão `AvailabilityZone` das
  métricas do NAT.
- **IPv4 público:** cada IP cobra US$ 3,65 por mês. Inclua os do ALB (um por zona), o da tarefa com IP público, o do
  banco marcado como público e os do NAT. No Radar, os IPs foram o maior item exclusivo.
- **GuardDuty Runtime Monitoring:** cobra por vCPU-mês de Fargate monitorado. Vale para todas as tarefas da conta;
  conte só as do projeto.
- **Franquias da conta** (100 GB de saída, 100 minutos de CodePipeline, Scheduler grátis até 14 milhões): são
  divididas com outros sistemas. Deixe como premissa (padrão 0) e diga isso no relatório.
- **Anexo do Transit Gateway compartilhado:** a cobrança pode cair na conta do anexo ou na dona do TGW. Marque
  "confirmar na fatura".
- **Banco em outra conta** (ex.: o do cliente): não entra nos totais; vira nota de "fora da conta".
