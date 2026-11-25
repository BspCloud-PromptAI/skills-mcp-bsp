# Arquitetura do Radar de Perdas na AWS (produção)

- Levantado em 12/11/2026 na conta athie-digital-prod (912668123297), região us-east-1, com o perfil `athie-digital-prod`.
- Diagrama: https://lucid.app/lucidchart/e03b2a92-7b41-4251-816a-51010c2cc027/edit (detalhes em [DIAGRAMA-LUCID.md](./DIAGRAMA-LUCID.md)).
- Custos: [../custos/CUSTOS-RADAR.md](../custos/CUSTOS-RADAR.md), com a calculadora editável
  `../custos/calculadora-custos-radar.xlsx` (preços da AWS Pricing API e uso medido em 30 dias).
- Nada aqui é gerenciado por infraestrutura como código: os recursos foram criados à mão (o CDK do back-end está vazio).

## Visão geral

O front-end Next.js roda no Amplify. A API FastAPI roda no ECS Fargate atrás de um ALB e serve os resultados que um
job diário calcula a partir do banco da Athié e grava no S3. O chat da API usa o Claude no Bedrock, consulta o banco da
Athié só para leitura e guarda as conversas num banco próprio. O login é o portal único da a|w.

## Componentes

### Front-end e login

- **Amplify** `dbcyul9zaxv7z` (radar-perdas-frontend), WEB_COMPUTE (Next.js com SSR), branch `main`, domínio
  radar.awdigitallab.com. Variáveis: `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_AUTH_HUB_URL`, `NEXT_PUBLIC_AUTH_MODE`.
- **Login único da a|w**: authentication.awdigitallab.com (portal aw-authentication, Cognito central
  `us-east-1_rLx1hmRa7` com o Microsoft Entra ID). Emite o app_token; a API confere pela chave pública
  (`AW_AUTH_ISSUER`, `AUTH_MODE=sso`).
- **Route 53** (zona awdigitallab.com): `radar` aponta para o CloudFront do Amplify e `radar-api` para o ALB.

### Rede: VPC-ATHIE-PRD (vpc-011ff85655182c587, 172.20.0.0/16)

| Zona | Pública (rota para o internet gateway) | Privada (rota para o NAT e o Transit Gateway) |
|---|---|---|
| us-east-1a | SUBNET-PUBLICA-A 172.20.0.0/20 | SUBNET-PRIVADA-A 172.20.128.0/20 |
| us-east-1b | SUBNET-PUBLICA-B 172.20.16.0/20 | SUBNET-PRIVADA-B 172.20.144.0/20 |
| us-east-1c | SUBNET-PUBLICA-C 172.20.32.0/20 | SUBNET-PRIVADA-C 172.20.160.0/20 |

- Internet gateway `igw-03a0abb23effede5f`; NAT gateway `nat-10a9a2c0a2a455b95` (IP público 54.90.145.18).
- Transit Gateway `tgw-04b78018f1a9f29ab`, de outra conta da Athié, anexado às sub-redes privadas com resolução de
  DNS ligada. Rotas: 172.22.0.0/16 (VPC do banco), 172.21.0.0/16, 172.23.0.0/16, 172.18.0.0/24 e 10.10.0.0/16.
- Único VPC endpoint: `guardduty-data` (o S3 e o Bedrock saem pela internet). Não há flow logs.

### Load balancer

- `alb-radar-prod`, internet-facing, nas três sub-redes públicas. Só existe o listener HTTPS 443
  (`ELBSecurityPolicy-TLS13-1-2-2021-06`, certificado ACM `*.awdigitallab.com`); não há listener na porta 80.
- Sem WAF. O security group `alb-sg-radar-prod` aceita tudo de 0.0.0.0/0, mas só a porta 443 responde.
- Target group `tg-radar-prod`: alvos por IP na porta 8000, health check `/healthz`.

### API (ECS)

- Cluster `cluster-radar-prod`; serviço `service-radar-prod` (FARGATE, 1 tarefa, rolling com circuit breaker e
  rollback, ECS Exec ligado). A tarefa ganha o agente do GuardDuty ao lado do app.
- Task definition `taksdef-radar-api:30`: ARM64, 0,5 vCPU, 1 GB, container `radar-container` na porta 8000, logs em
  `/ecs/taksdef-radar-api`.
- Roda nas sub-redes **públicas**, com IP público. O `SG-radar-api` só aceita a porta 8000 vinda do ALB.
- Papel da tarefa `role-radar-api-prod` (só da API): listar o bucket, ler e gravar em `prod/*`, chamar os modelos
  Anthropic no Bedrock e o ECS Exec. Papel de execução: `ecsTaskExecutionRole`, compartilhado com outros projetos.
- Segredos injetados pelo ECS: `CHAT_DATABASE_URL` (`radar/prod/chat-db-url`), `DB_PASSWORD` e `AGENTE_DB_PASSWORD`
  (campo `password` de `radar/prod/db-clean`). Nenhuma senha ou chave em texto puro.
- Configuração: `DATA_SOURCE=real`, `STORE_TYPE=s3`, `LLM_PROVIDER=bedrock`, modelos
  `global.anthropic.claude-sonnet-5` (o auxiliar da Trilha usa `global.anthropic.claude-haiku-5-5`),
  `CHAT_STORE=postgres`, `AGENTE_FONTE_SQL=banco`, `CORS_ORIGINS=https://radar.awdigitallab.com`.

### Job diário

- EventBridge Scheduler `scheduler-radar-prod-job`: `cron(0 6 * * ? *)` em America/Sao_Paulo, até 2 novas
  tentativas em 1 hora. Roda a `taskdef-radar-job:9` (ARM64, 1 vCPU, 4 GB), container `radar-job`, comando
  `python -m radar_db extract && python -m radar_engine.cli analyze`, logs em `/ecs/taskdef-radar-job`.
- Roda só na SUBNET-PRIVADA-A, sem IP público; o `SG-radar-job` não aceita conexões.
- Lê a credencial do banco em tempo de execução (`DB_SECRET_ARN` = `radar/prod/db-clean`, `DB_AWS_PROFILE=instance-role`)
  e recebe `PSEUDO_SALT` (`radar/prod/pseudo-salt`). Papel da tarefa: `ecsTaskExecutionRole`.
- Em 12/11/2026 rodou às 06:00 e terminou em cerca de 35 segundos.

### Dados

- **S3** `s3-radar-prod-912668123297`, prefixo `prod/` (camada gold em parquet, por exemplo
  `prod/real/gold/trilha.parquet`). SSE-S3, acesso público bloqueado, política que nega acesso sem TLS. Sem versionamento.
- **Banco da Athié** (conta athie-vector 522294740020, VPC 172.22.0.0/16): RDS PostgreSQL 18.3
  `db-vetorial-prd-clean`, banco `postgres`, com o ERP copiado pelo DMS. O Radar entra com `agent_radar_aw`, só SELECT.
  O endpoint é público.
- **Banco do chat** `radar-prod-chat`: RDS PostgreSQL 18.3 db.t4g.micro, banco `radar_chat`, nas sub-redes privadas
  A e B, criptografado, backup de 7 dias, sem Multi-AZ. O `SG-db-radar-chat` aceita a porta 5432 da VPC, do
  `SG-radar-api` e do IP 152.254.132.243/32.

### Esteira de deploy

- `pipeline-radar-prod` (V2, QUEUED): Source (conexão do GitHub, `main` do radar-perdas-backend) → Build
  (`codebuild-radar-prod`, ARM, `buildspec.yml` do repositório: `make lint && make test`, imagem com a tag dos
  12 primeiros caracteres do commit, nova revisão do job e agendamento apontado para ela) → Deploy (ECS, com o
  `imagedefinitions.json`). O deploy copia a task definition atual do serviço e troca só a imagem.
- ECR `ecr-radar-prod`: tags mutáveis, sem scan no push, AES256, sem política de ciclo de vida.
- O papel do CodeBuild tem `AdministratorAccess`.

### Observabilidade

- Logs da API e do job no CloudWatch por 90 dias. Nenhum alarme configurado.
- GuardDuty com monitoramento em execução das tarefas Fargate.

## Fluxos (mesma numeração do diagrama)

1. O usuário abre radar.awdigitallab.com; o Route 53 aponta para o Amplify.
2. Sem sessão, o front manda para o login único, que devolve o app_token.
3. O navegador chama radar-api.awdigitallab.com; o ALB termina o HTTPS e repassa para a API na porta 8000.
4. A API lê os resultados no S3, usa o Bedrock no chat, consulta o banco da Athié só para leitura e grava as
   conversas no banco do chat.
5. Às 06:00 o job lê o banco da Athié, calcula e grava o parquet no S3.
6. Cada push na `main` do back-end passa pelo pipeline; o front é publicado pelo Amplify.

O caminho de rede até o banco da Athié: a API sai pelo internet gateway com IP público. O job sai da sub-rede
privada pelo NAT, ou pelo Transit Gateway se o DNS resolver o endpoint para o IP privado. Sem flow logs, não dá para
afirmar qual dos dois.

## Correção de segurança de 12/11/2026

- **Antes:** a revisão 29 da API tinha em texto puro `DB_PASSWORD`, `AGENTE_DB_PASSWORD`, `AWS_ACCESS_KEY_ID` e
  `AWS_SECRET_ACCESS_KEY`. A chave era do usuário IAM `radar-api`, com `AdministratorAccess`.
- **Feito:**
  1. Papel novo `role-radar-api-prod`, só com o que a API usa.
  2. Revisão 30 sem as quatro variáveis, com as senhas vindas de `radar/prod/db-clean`.
  3. Serviço atualizado por rolling deploy.
  4. O pipeline mantém a mudança, porque o deploy parte da task definition atual.
- **Verificado:**
  - Tarefa avulsa com a revisão 30 antes da troca: papel certo, nenhuma chave no ambiente, senhas injetadas, S3
    (listar, ler, 404 para ausente) e Bedrock (Sonnet 5 e Haiku 5.5 em streaming).
  - Depois do deploy: serviço estável na revisão 30, alvo saudável no ALB, `/healthz` 200, rota protegida 401 sem
    token e nenhum erro no log.

## Pendências

- Decisões da correção acima:
  - desativar a chave do usuário `radar-api`, hoje sem uso;
  - apagar as 27 revisões antigas da task definition que têm credenciais em texto puro;
  - trocar a senha do `agent_radar_aw`, que ficou exposta nessas revisões (exige o master do banco da Athié).
- O job ainda usa o `ecsTaskExecutionRole` (`AdministratorAccess`, compartilhado com ComfyUI, digital-lab e
  productive-server) como papel da tarefa; o CodeBuild também tem `AdministratorAccess`.
- Nenhum alarme para falha do job ou da API.
- ALB sem WAF; robôs já testam URLs como `/connection.php` (recebem 404).
- ECR sem scan e com tags mutáveis.
- Banco do chat marcado como público, com regra para um IP externo.
- Regra antiga desabilitada no EventBridge (`scheduler-radar-prod-job`, a cada 1 minuto).
- Levar tudo para infraestrutura como código.
