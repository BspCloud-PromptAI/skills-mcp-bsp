# Calculadora de custos mensais da arquitetura do Radar na AWS (conta athie-digital-prod, us-east-1).
# Preços: AWS Pricing API. Uso: medido nos últimos 30 dias (CloudWatch, ECS, ECR, CodeBuild, CodePipeline, Amplify).
# Gera nesta pasta: precos-aws.json, uso-medido.json, calculadora-custos-radar.xlsx e CUSTOS-RADAR.md.
# Uso (Git Bash): MSYS_NO_PATHCONV=1 uv run --with openpyxl python -I calcular_custos.py
import json
import math
import statistics
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from openpyxl import Workbook
from openpyxl.cell.cell import MergedCell
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.workbook.defined_name import DefinedName

PASTA = Path(__file__).resolve().parent
PERFIL = ["--profile", "athie-digital-prod", "--region", "us-east-1", "--output", "json"]
DIAS = 30
AGORA = datetime.now(timezone.utc)
INICIO = AGORA - timedelta(days=DIAS)
GB = 2**30
CLUSTER = "cluster-radar-prod"
BUCKET = "s3-radar-prod-912668123297"
NAT = "nat-10a9a2c0a2a455b95"
APP_AMPLIFY = "dbcyul9zaxv7z"
MODELOS = {"sonnet": "global.anthropic.claude-sonnet-5", "haiku": "global.anthropic.claude-haiku-5-5"}


def aws(*args, tolerar=False):
    resultado = subprocess.run(["aws", *args, *PERFIL], capture_output=True, text=True, encoding="utf-8")
    if resultado.returncode != 0:
        if tolerar:
            return {}
        sys.exit(f"falhou: aws {' '.join(args[:2])}: {resultado.stderr.strip()[:300]}")
    return json.loads(resultado.stdout) if resultado.stdout.strip() else {}


def instante(valor):
    if isinstance(valor, (int, float)):
        return datetime.fromtimestamp(valor, timezone.utc)
    return datetime.fromisoformat(valor)


def minutos(inicio, fim):
    return math.ceil((instante(fim) - instante(inicio)).total_seconds() / 60)


# ── Preços (AWS Pricing API) ───────────────────────────────────────────────────
def termo(campo, valor):
    return {"Type": "TERM_MATCH", "Field": campo, "Value": valor}


LOCAL = termo("location", "US East (N. Virginia)")


def item_preco(chave, servico, tipo_uso, *extras, trecho=None, faixa="0", local=True):
    filtros = ([LOCAL] if local else []) + [termo("usagetype", tipo_uso), *extras]
    return {"chave": chave, "servico": servico, "filtros": filtros, "trecho": trecho, "faixa": faixa}


PG_SINGLE_AZ = (termo("databaseEngine", "PostgreSQL"), termo("deploymentOption", "Single-AZ"))
ALB = termo("productFamily", "Load Balancer-Application")
PRECOS = [
    item_preco("fargate_vcpu", "AmazonECS", "USE1-Fargate-ARM-vCPU-Hours:perCPU"),
    item_preco("fargate_gb", "AmazonECS", "USE1-Fargate-ARM-GB-Hours"),
    item_preco("guardduty_fargate", "AmazonGuardDuty", "USE1-PaidFargatevCPUMonitored"),
    item_preco("alb_hora", "AWSELB", "LoadBalancerUsage", ALB),
    item_preco("alb_lcu", "AWSELB", "LCUUsage", ALB),
    item_preco("ipv4", "AmazonVPC", "USE1-PublicIPv4:InUseAddress"),
    item_preco("nat_hora", "AmazonEC2", "RegionalNatGateway-Hours"),
    item_preco("nat_gb", "AmazonEC2", "USE1-RegionalNatGateway-Bytes"),
    item_preco("tgw_hora", "AmazonVPC", "USE1-TransitGateway-Hours", trecho="VPC Attachment Hour"),
    item_preco("tgw_gb", "AmazonVPC", "USE1-TransitGateway-Bytes", trecho="VPC Attachment"),
    item_preco("rds_hora", "AmazonRDS", "InstanceUsage:db.t4g.micro", *PG_SINGLE_AZ),
    item_preco("rds_gp2", "AmazonRDS", "RDS:GP2-Storage", *PG_SINGLE_AZ),
    item_preco("rds_backup", "AmazonRDS", "RDS:ChargedBackupUsage", *PG_SINGLE_AZ),
    item_preco("s3_gb", "AmazonS3", "TimedStorage-ByteHrs"),
    item_preco("s3_put", "AmazonS3", "Requests-Tier1"),
    item_preco("s3_get", "AmazonS3", "Requests-Tier2"),
    item_preco("ecr_gb", "AmazonECR", "TimedStorage-ByteHrs"),
    item_preco("logs_ingestao", "AmazonCloudWatch", "USE1-DataProcessing-Bytes", trecho="ingested in Standard"),
    item_preco("logs_armazenamento", "AmazonCloudWatch", "USE1-TimedStorage-ByteHrs"),
    item_preco("segredo", "AWSSecretsManager", "USE1-AWSSecretsManager-Secrets"),
    item_preco("segredo_api", "AWSSecretsManager", "USE1-AWSSecretsManagerAPIRequest"),
    item_preco("r53_zona", "AmazonRoute53", "HostedZone", local=False),
    item_preco("r53_consulta", "AmazonRoute53", "DNS-Queries", local=False),
    item_preco("amplify_build", "AWSAmplify", "USE1-BuildDuration"),
    item_preco("amplify_armazenamento", "AWSAmplify", "USE1-DataStorage"),
    item_preco("amplify_transferencia", "AWSAmplify", "USE1-DataTransferOut"),
    item_preco("amplify_requisicao", "AWSAmplify", "USE1-HostingComputeRequestCount"),
    item_preco("amplify_gb_segundo", "AWSAmplify", "USE1-HostingComputeRequestDuration"),
    item_preco("codebuild_minuto", "CodeBuild", "USE1-Build-Min:ARM:g1.small"),
    item_preco("codepipeline_minuto", "AWSCodePipeline", "USE1-actionExecutionMinute"),
    item_preco("scheduler", "AWSEvents", "USE1-ScheduledInvocation", faixa="14000000"),
    item_preco("saida_internet", "AWSDataTransfer", "DataTransfer-Out-Bytes", termo("fromLocation", "US East (N. Virginia)"),
               termo("transferType", "AWS Outbound"), local=False),
    *[item_preco(f"{apelido}_{tipo}", "AmazonBedrockFoundationModels", f"USE1-MP:USE1_{uso}_global_standard-Units",
                 termo("model", nome), local=False)
      for apelido, nome in [("sonnet", "Claude Sonnet 5"), ("haiku", "Claude Haiku 5.5")]
      for tipo, uso in [("entrada", "input_tokens"), ("saida", "output_tokens"),
                        ("cache_leitura", "cache_read_tokens"), ("cache_escrita", "cache_write_tokens")]],
]


def buscar_preco(definicao):
    resposta = aws("pricing", "get-products", "--service-code", definicao["servico"], "--max-items", "200",
                   "--filters", json.dumps(definicao["filtros"]))
    candidatos = []
    for bruto in resposta.get("PriceList", []):
        produto = json.loads(bruto)
        for oferta in produto.get("terms", {}).get("OnDemand", {}).values():
            for dimensao in oferta["priceDimensions"].values():
                if definicao["faixa"] is not None and dimensao.get("beginRange") != definicao["faixa"]:
                    continue
                if definicao["trecho"] and definicao["trecho"] not in dimensao["description"]:
                    continue
                candidatos.append({
                    "chave": definicao["chave"], "servico": definicao["servico"],
                    "tipo_uso": produto["product"]["attributes"].get("usagetype"),
                    "descricao": dimensao["description"], "preco_usd": float(dimensao["pricePerUnit"]["USD"]),
                    "unidade": dimensao["unit"], "vigencia": oferta["effectiveDate"][:10], "sku": produto["product"]["sku"],
                })
    precos = {round(c["preco_usd"], 12) for c in candidatos}
    if len(precos) != 1:
        sys.exit(f"preço de {definicao['chave']} ambíguo ou ausente: {sorted(precos)}")
    return candidatos[0]


# ── Uso medido (últimos 30 dias) ───────────────────────────────────────────────
def metrica(namespace, nome, dimensoes, estatistica="Sum"):
    resposta = aws("cloudwatch", "get-metric-statistics", "--namespace", namespace, "--metric-name", nome,
                   "--dimensions", *[f"Name={chave},Value={valor}" for chave, valor in dimensoes],
                   "--start-time", INICIO.isoformat(), "--end-time", AGORA.isoformat(),
                   "--period", "86400", "--statistics", estatistica)
    return sorted(((instante(p["Timestamp"]), p[estatistica]) for p in resposta.get("Datapoints", [])),
                  key=lambda ponto: ponto[0])


def soma(namespace, nome, dimensoes):
    return sum(valor for _, valor in metrica(namespace, nome, dimensoes))


def ultimo(namespace, nome, dimensoes):
    pontos = metrica(namespace, nome, dimensoes, "Average")
    return pontos[-1][1] if pontos else 0.0


def medir():
    uso = {"medido_em": AGORA.isoformat(timespec="minutes"), "janela_dias": DIAS}

    servico = aws("ecs", "describe-services", "--cluster", CLUSTER, "--services", "service-radar-prod")["services"][0]
    td_api = aws("ecs", "describe-task-definition", "--task-definition", servico["taskDefinition"])["taskDefinition"]
    td_job = aws("ecs", "describe-task-definition", "--task-definition", "taskdef-radar-job")["taskDefinition"]
    uso |= {"api_tarefas": servico["desiredCount"], "api_vcpu": int(td_api["cpu"]) / 1024,
            "api_gb": int(td_api["memory"]) / 1024, "job_vcpu": int(td_job["cpu"]) / 1024,
            "job_gb": int(td_job["memory"]) / 1024}

    fluxos = aws("logs", "describe-log-streams", "--log-group-name", "/ecs/taskdef-radar-job", "--order-by",
                 "LastEventTime", "--descending", "--max-items", "100")["logStreams"]
    recentes = [f for f in fluxos if f.get("firstEventTimestamp") and f["lastEventTimestamp"] / 1000 >= INICIO.timestamp()]
    duracoes = [(f["lastEventTimestamp"] - f["firstEventTimestamp"]) / 1000 for f in recentes]
    uso |= {"job_execucoes_medidas": len(recentes), "job_segundos_medio": statistics.mean(duracoes) if duracoes else 60}

    alb = aws("elbv2", "describe-load-balancers", "--names", "alb-radar-prod")["LoadBalancers"][0]
    dimensao_alb = [("LoadBalancer", alb["LoadBalancerArn"].split("loadbalancer/")[1])]
    lcu = [valor for _, valor in metrica("AWS/ApplicationELB", "ConsumedLCUs", dimensao_alb, "Average")]
    uso |= {"alb_lcu_medio": statistics.mean(lcu) if lcu else 0.0,
            "alb_gb_processados": soma("AWS/ApplicationELB", "ProcessedBytes", dimensao_alb) / GB,
            "alb_requisicoes": soma("AWS/ApplicationELB", "RequestCount", dimensao_alb)}

    interfaces = aws("ec2", "describe-network-interfaces", "--filters",
                     f"Name=description,Values=ELB {dimensao_alb[0][1]}")["NetworkInterfaces"]
    ips_alb = sum(1 for interface in interfaces if interface.get("Association", {}).get("PublicIp"))
    tarefa = aws("ecs", "list-tasks", "--cluster", CLUSTER, "--service-name", "service-radar-prod")["taskArns"][0]
    anexo = aws("ecs", "describe-tasks", "--cluster", CLUSTER, "--tasks", tarefa)["tasks"][0]["attachments"][0]
    eni = next(d["value"] for d in anexo["details"] if d["name"] == "networkInterfaceId")
    ip_api = 1 if aws("ec2", "describe-network-interfaces", "--network-interface-ids", eni)["NetworkInterfaces"][0].get(
        "Association", {}).get("PublicIp") else 0
    chat = aws("rds", "describe-db-instances", "--db-instance-identifier", "radar-prod-chat")["DBInstances"][0]
    uso |= {"ipv4_alb": ips_alb, "ipv4_api": ip_api, "ipv4_chat": 1 if chat["PubliclyAccessible"] else 0,
            "rds_chat_gb": chat["AllocatedStorage"], "rds_chat_tipo": chat["StorageType"],
            "rds_chat_backup_cobrado_gb": ultimo("AWS/RDS", "TotalBackupStorageBilled",
                                                 [("DBInstanceIdentifier", "radar-prod-chat")]) / GB}

    nat = aws("ec2", "describe-nat-gateways", "--nat-gateway-ids", NAT)["NatGateways"][0]
    zonas = sorted({d["Value"] for m in aws("cloudwatch", "list-metrics", "--namespace", "AWS/NATGateway", "--metric-name",
                                             "BytesOutToDestination", "--dimensions", f"Name=NatGatewayId,Value={NAT}")["Metrics"]
                    for d in m["Dimensions"] if d["Name"] == "AvailabilityZone"})
    bytes_nat = sum(soma("AWS/NATGateway", nome, [("NatGatewayId", NAT), ("AvailabilityZone", zona)])
                    for zona in zonas for nome in ("BytesOutToDestination", "BytesOutToSource"))
    uso |= {"nat_zonas": len(zonas), "nat_ipv4": len(nat["NatGatewayAddresses"]), "nat_gb_processados": bytes_nat / GB}

    uso |= {"s3_gb": ultimo("AWS/S3", "BucketSizeBytes", [("BucketName", BUCKET), ("StorageType", "StandardStorage")]) / GB,
            "s3_objetos": ultimo("AWS/S3", "NumberOfObjects", [("BucketName", BUCKET), ("StorageType", "AllStorageTypes")])}

    imagens = aws("ecr", "describe-images", "--repository-name", "ecr-radar-prod", "--max-items", "1000")["imageDetails"]
    uso |= {"ecr_gb": sum(i["imageSizeInBytes"] for i in imagens) / GB, "ecr_imagens": len(imagens)}

    ingeridos = guardados = 0.0
    for grupo in ("/ecs/taksdef-radar-api", "/ecs/taskdef-radar-job"):
        info = next(g for g in aws("logs", "describe-log-groups", "--log-group-name-prefix", grupo)["logGroups"]
                    if g["logGroupName"] == grupo)
        guardados += info.get("storedBytes", 0)
        ingeridos += soma("AWS/Logs", "IncomingBytes", [("LogGroupName", grupo)])
    segredos = aws("secretsmanager", "list-secrets", "--filters", "Key=name,Values=radar/prod/")["SecretList"]
    uso |= {"logs_ingeridos_gb": ingeridos / GB, "logs_guardados_gb": guardados / GB, "segredos": len(segredos)}

    ids = aws("codebuild", "list-builds-for-project", "--project-name", "codebuild-radar-prod", "--sort-order",
              "DESCENDING", "--max-items", "100")["ids"]
    builds = aws("codebuild", "batch-get-builds", "--ids", *ids)["builds"] if ids else []
    builds = [b for b in builds if b.get("endTime") and instante(b["startTime"]) >= INICIO]
    uso |= {"codebuild_builds": len(builds), "codebuild_minutos": sum(minutos(b["startTime"], b["endTime"]) for b in builds)}

    acoes = aws("codepipeline", "list-action-executions", "--pipeline-name", "pipeline-radar-prod",
                "--max-items", "1000")["actionExecutionDetails"]
    acoes = [a for a in acoes if a.get("lastUpdateTime") and instante(a["startTime"]) >= INICIO]
    uso |= {"codepipeline_execucoes": len({a["pipelineExecutionId"] for a in acoes}),
            "codepipeline_minutos": sum(minutos(a["startTime"], a["lastUpdateTime"]) for a in acoes)}

    jobs = aws("amplify", "list-jobs", "--app-id", APP_AMPLIFY, "--branch-name", "main", "--max-items", "100")["jobSummaries"]
    jobs = [j for j in jobs if j.get("endTime") and instante(j["startTime"]) >= INICIO]
    dimensao_app = [("App", APP_AMPLIFY)]
    uso |= {"amplify_builds": len(jobs), "amplify_build_minutos": sum(minutos(j["startTime"], j["endTime"]) for j in jobs),
            "amplify_requisicoes": soma("AWS/AmplifyHosting", "Requests", dimensao_app),
            "amplify_gb_servidos": soma("AWS/AmplifyHosting", "BytesDownloaded", dimensao_app) / GB}

    for apelido, modelo in MODELOS.items():
        dimensao = [("ModelId", modelo)]
        uso |= {f"{apelido}_invocacoes": soma("AWS/Bedrock", "Invocations", dimensao),
                f"{apelido}_entrada": soma("AWS/Bedrock", "InputTokenCount", dimensao),
                f"{apelido}_saida": soma("AWS/Bedrock", "OutputTokenCount", dimensao),
                f"{apelido}_cache_leitura": soma("AWS/Bedrock", "CacheReadInputTokenCount", dimensao),
                f"{apelido}_cache_escrita": soma("AWS/Bedrock", "CacheWriteInputTokenCount", dimensao)}
    return uso


# ── Premissas e itens da calculadora ───────────────────────────────────────────
def montar_premissas(u):
    medido = f"Medido em {AGORA:%d/%m/%Y}, últimos {DIAS} dias"
    return [
        ("Geral", None, None, None, None),
        ("horas_mes", "Horas cobradas por mês", 730, "horas", "Padrão de cobrança da AWS (730 h por mês)"),
        ("rateio", "Parcela do Radar na infra compartilhada", 0, "fração",
         "Premissa: 0 não rateia. Ex.: 0,25 se o Radar responder por um quarto do NAT e do Transit Gateway"),
        ("cotacao", "Cotação do dólar (R$ por US$)", None, "R$", "Preencha para ver os totais em reais. Ex.: 5,40"),
        ("API e job (ECS Fargate ARM64)", None, None, None, None),
        ("api_tarefas", "API: tarefas rodando o mês todo", u["api_tarefas"], "tarefas", f"{medido}: desiredCount do serviço"),
        ("api_vcpu", "API: vCPU por tarefa", u["api_vcpu"], "vCPU", "Medido: task definition da API"),
        ("api_gb", "API: memória por tarefa", u["api_gb"], "GB", "Medido: task definition da API"),
        ("job_execucoes", "Job: execuções por mês", 30, "execuções",
         f"Premissa: uma por dia às 06:00 ({u['job_execucoes_medidas']} execuções com log nos últimos {DIAS} dias)"),
        ("job_minutos", "Job: minutos cobrados por execução", round(max(1.0, u["job_segundos_medio"] / 60 + 1), 2), "minutos",
         f"Medido: {u['job_segundos_medio']:.0f} s de log por execução, mais 1 minuto (premissa) para baixar a imagem e subir"),
        ("job_vcpu", "Job: vCPU por execução", u["job_vcpu"], "vCPU", "Medido: taskdef-radar-job"),
        ("job_gb", "Job: memória por execução", u["job_gb"], "GB", "Medido: taskdef-radar-job"),
        ("Rede e balanceamento", None, None, None, None),
        ("alb_lcu", "ALB: LCU médio por hora", round(u["alb_lcu_medio"], 6), "LCU", f"{medido}: ConsumedLCUs (média)"),
        ("ipv4_radar", "IPv4 públicos do Radar", u["ipv4_alb"] + u["ipv4_api"] + u["ipv4_chat"], "endereços",
         f"Medido: {u['ipv4_alb']} do ALB, {u['ipv4_api']} da tarefa da API e {u['ipv4_chat']} do banco do chat (marcado como público)"),
        ("saida_gb", "Saída para a internet pelo ALB", round(u["alb_gb_processados"], 3), "GB por mês",
         f"{medido}: ProcessedBytes do ALB (entrada mais saída, usado como teto)"),
        ("saida_franquia", "Saída: franquia grátis atribuída ao Radar", 0, "GB",
         "A conta tem 100 GB grátis por mês, divididos com outros sistemas; 0 é o cenário conservador"),
        ("Dados", None, None, None, None),
        ("rds_chat_gb", "Banco do chat: armazenamento gp2", u["rds_chat_gb"], "GB", "Medido: radar-prod-chat (gp2)"),
        ("rds_chat_backup_gb", "Banco do chat: backup acima da franquia", round(u["rds_chat_backup_cobrado_gb"], 3), "GB",
         "Medido: TotalBackupStorageBilled (a franquia é do tamanho do banco)"),
        ("s3_gb", "S3: armazenamento Standard", round(u["s3_gb"], 4), "GB",
         f"Medido: BucketSizeBytes ({u['s3_objetos']:.0f} objetos)"),
        ("s3_put", "S3: PUT, COPY e LIST por mês", 3000, "requisições",
         "Premissa: o job regrava os parquet todo dia; o bucket não tem métricas de requisição"),
        ("s3_get", "S3: GET por mês", 30000, "requisições", "Premissa: leituras da API e do job"),
        ("ecr_gb", "ECR: imagens guardadas", round(u["ecr_gb"], 3), "GB",
         f"Medido: {u['ecr_imagens']} imagens, sem política de limpeza"),
        ("logs_gb_ingeridos", "CloudWatch Logs: ingestão por mês", round(u["logs_ingeridos_gb"], 4), "GB",
         f"{medido}: IncomingBytes dos logs da API e do job"),
        ("logs_gb_guardados", "CloudWatch Logs: volume guardado", round(u["logs_guardados_gb"], 4), "GB",
         "Medido: storedBytes (retenção de 90 dias)"),
        ("segredos", "Secrets Manager: segredos do Radar", u["segredos"], "segredos", "Medido: radar/prod/*"),
        ("segredos_chamadas", "Secrets Manager: chamadas por mês", 300, "chamadas",
         "Premissa: o job lê a senha todo dia e o ECS injeta os segredos a cada tarefa nova"),
        ("Front-end (Amplify)", None, None, None, None),
        ("amplify_build_min", "Amplify: minutos de build por mês", u["amplify_build_minutos"], "minutos",
         f"{medido}: {u['amplify_builds']} builds da main"),
        ("amplify_gb_guardados", "Amplify: artefatos de build guardados", 1, "GB", "Premissa"),
        ("amplify_gb_servidos", "Amplify: dados servidos por mês", round(u["amplify_gb_servidos"], 3), "GB",
         f"{medido}: BytesDownloaded"),
        ("amplify_requisicoes", "Amplify: requisições por mês", u["amplify_requisicoes"], "requisições", f"{medido}: Requests"),
        ("amplify_parcela_ssr", "Amplify: parcela das requisições que roda o servidor (SSR)", 0.3, "fração",
         "Premissa: o resto sai do cache da CDN sem custo de computação"),
        ("amplify_segundos_ssr", "Amplify: duração média de uma requisição SSR", 0.5, "segundos", "Premissa"),
        ("amplify_gb_ssr", "Amplify: memória da computação SSR", 1, "GB", "Premissa"),
        ("Esteira de deploy", None, None, None, None),
        ("codebuild_min", "CodeBuild: minutos ARM small por mês", u["codebuild_minutos"], "minutos",
         f"{medido}: {u['codebuild_builds']} builds"),
        ("codepipeline_min", "CodePipeline V2: minutos de ação por mês", u["codepipeline_minutos"], "minutos",
         f"{medido}: {u['codepipeline_execucoes']} execuções"),
        ("codepipeline_franquia", "CodePipeline: minutos grátis atribuídos ao Radar", 0, "minutos",
         "A conta tem 100 minutos grátis por mês, divididos com outros pipelines; 0 é o cenário conservador"),
        ("scheduler_invocacoes", "EventBridge Scheduler: invocações por mês", 30, "invocações",
         "Premissa: uma por dia; os primeiros 14 milhões do mês são grátis"),
        ("IA (Amazon Bedrock, perfis globais)", None, None, None, None),
        *[(f"{apelido}_{tipo}", f"{rotulo}: tokens de {nome_tipo} por mês", round(u[f"{apelido}_{tipo}"]), "tokens",
           f"{medido}: {metrica_cw} de {MODELOS[apelido]} ({u[f'{apelido}_invocacoes']:.0f} chamadas; inclui qualquer "
           "outro sistema da conta que use o mesmo perfil)")
          for apelido, rotulo in [("sonnet", "Sonnet 5"), ("haiku", "Haiku 5.5")]
          for tipo, nome_tipo, metrica_cw in [("entrada", "entrada", "InputTokenCount"), ("saida", "saída", "OutputTokenCount"),
                                              ("cache_leitura", "leitura de cache", "CacheReadInputTokenCount"),
                                              ("cache_escrita", "escrita de cache", "CacheWriteInputTokenCount")]],
        ("Infra compartilhada da VPC e da conta", None, None, None, None),
        ("nat_zonas", "NAT regional: zonas ativas", u["nat_zonas"], "zonas", "Medido: métricas do NAT por zona"),
        ("nat_gb", "NAT: dados processados por mês (toda a VPC)", round(u["nat_gb_processados"], 3), "GB",
         f"{medido}: BytesOutToDestination mais BytesOutToSource"),
        ("nat_ipv4", "NAT: IPs elásticos", u["nat_ipv4"], "endereços", "Medido: endereços do NAT regional"),
        ("tgw_gb", "Transit Gateway: dados processados por mês", 0, "GB",
         "Sem medição: a métrica fica na conta dona do Transit Gateway"),
        ("dns_consultas", "Route 53: consultas por mês", 100000, "consultas", "Premissa"),
    ]


def montar_itens():
    def item(grupo, componente, servico, expressao, unidade, preco, nota=""):
        return {"grupo": grupo, "componente": componente, "servico": servico, "expressao": expressao,
                "unidade": unidade, "preco": preco, "nota": nota}

    horas_job = "u_job_execucoes*u_job_minutos/60"
    itens = [
        item("Radar", "API: vCPU", "ECS Fargate", "u_horas_mes*u_api_tarefas*u_api_vcpu", "vCPU-hora", "fargate_vcpu"),
        item("Radar", "API: memória", "ECS Fargate", "u_horas_mes*u_api_tarefas*u_api_gb", "GB-hora", "fargate_gb"),
        item("Radar", "Job diário: vCPU", "ECS Fargate", f"{horas_job}*u_job_vcpu", "vCPU-hora", "fargate_vcpu"),
        item("Radar", "Job diário: memória", "ECS Fargate", f"{horas_job}*u_job_gb", "GB-hora", "fargate_gb"),
        item("Radar", "Monitoramento das tarefas", "GuardDuty",
             f"(u_horas_mes*u_api_tarefas*u_api_vcpu+{horas_job}*u_job_vcpu)/u_horas_mes", "vCPU-mês", "guardduty_fargate"),
        item("Radar", "ALB: horas", "Elastic Load Balancing", "u_horas_mes", "hora", "alb_hora"),
        item("Radar", "ALB: capacidade (LCU)", "Elastic Load Balancing", "u_horas_mes*u_alb_lcu", "LCU-hora", "alb_lcu"),
        item("Radar", "IPv4 públicos (ALB, API e banco do chat)", "VPC", "u_horas_mes*u_ipv4_radar", "IP-hora", "ipv4"),
        item("Radar", "Saída de dados para a internet", "Transferência de dados", "MAX(0,u_saida_gb-u_saida_franquia)", "GB",
             "saida_internet"),
        item("Radar", "Banco do chat: instância db.t4g.micro", "RDS", "u_horas_mes", "hora", "rds_hora"),
        item("Radar", "Banco do chat: armazenamento gp2", "RDS", "u_rds_chat_gb", "GB-mês", "rds_gp2"),
        item("Radar", "Banco do chat: backup acima da franquia", "RDS", "u_rds_chat_backup_gb", "GB-mês", "rds_backup"),
        item("Radar", "Resultados: armazenamento", "S3", "u_s3_gb", "GB-mês", "s3_gb"),
        item("Radar", "Resultados: PUT, COPY e LIST", "S3", "u_s3_put", "requisição", "s3_put"),
        item("Radar", "Resultados: GET", "S3", "u_s3_get", "requisição", "s3_get"),
        item("Radar", "Imagens da API e do job", "ECR", "u_ecr_gb", "GB-mês", "ecr_gb"),
        item("Radar", "Logs: ingestão", "CloudWatch", "u_logs_gb_ingeridos", "GB", "logs_ingestao"),
        item("Radar", "Logs: armazenamento", "CloudWatch", "u_logs_gb_guardados", "GB-mês", "logs_armazenamento"),
        item("Radar", "Segredos", "Secrets Manager", "u_segredos", "segredo-mês", "segredo"),
        item("Radar", "Chamadas aos segredos", "Secrets Manager", "u_segredos_chamadas", "chamada", "segredo_api"),
        item("Radar", "Front-end: minutos de build", "Amplify", "u_amplify_build_min", "minuto", "amplify_build"),
        item("Radar", "Front-end: artefatos guardados", "Amplify", "u_amplify_gb_guardados", "GB", "amplify_armazenamento"),
        item("Radar", "Front-end: dados servidos", "Amplify", "u_amplify_gb_servidos", "GB", "amplify_transferencia"),
        item("Radar", "Front-end: requisições SSR", "Amplify", "u_amplify_requisicoes*u_amplify_parcela_ssr", "requisição",
             "amplify_requisicao"),
        item("Radar", "Front-end: duração SSR", "Amplify",
             "u_amplify_requisicoes*u_amplify_parcela_ssr*u_amplify_segundos_ssr*u_amplify_gb_ssr", "GB-segundo",
             "amplify_gb_segundo"),
        item("Radar", "Build da imagem", "CodeBuild", "u_codebuild_min", "minuto", "codebuild_minuto"),
        item("Radar", "Pipeline V2", "CodePipeline", "MAX(0,u_codepipeline_min-u_codepipeline_franquia)", "minuto",
             "codepipeline_minuto"),
        item("Radar", "Agendamento do job", "EventBridge Scheduler", "MAX(0,u_scheduler_invocacoes-14000000)", "invocação",
             "scheduler", "Os primeiros 14 milhões de invocações do mês são grátis"),
    ]
    for apelido, nome in [("sonnet", "Claude Sonnet 5"), ("haiku", "Claude Haiku 5.5")]:
        for tipo, rotulo in [("entrada", "entrada"), ("saida", "saída"), ("cache_leitura", "leitura de cache"),
                             ("cache_escrita", "escrita de cache")]:
            itens.append(item("Radar", f"{nome}: tokens de {rotulo}", "Bedrock", f"u_{apelido}_{tipo}/1000000",
                              "milhão de tokens", f"{apelido}_{tipo}"))
    itens += [
        item("Compartilhado", "NAT regional: horas por zona", "VPC", "u_horas_mes*u_nat_zonas", "zona-hora", "nat_hora",
             "Do projeto digital-lab; atende todas as sub-redes privadas da VPC"),
        item("Compartilhado", "NAT regional: dados processados", "VPC", "u_nat_gb", "GB", "nat_gb", "Tráfego de toda a VPC"),
        item("Compartilhado", "NAT: IPs elásticos", "VPC", "u_horas_mes*u_nat_ipv4", "IP-hora", "ipv4"),
        item("Compartilhado", "Transit Gateway: anexo da VPC", "Transit Gateway", "u_horas_mes", "hora", "tgw_hora",
             "Confirmar na fatura se o anexo é cobrado nesta conta ou na dona do Transit Gateway"),
        item("Compartilhado", "Transit Gateway: dados processados", "Transit Gateway", "u_tgw_gb", "GB", "tgw_gb"),
        item("Compartilhado", "Zona awdigitallab.com", "Route 53", "1", "zona-mês", "r53_zona",
             "Também atende o Conecta, o login e outros sistemas"),
        item("Compartilhado", "Consultas de DNS", "Route 53", "u_dns_consultas", "consulta", "r53_consulta"),
    ]
    return itens


def avaliar(expressao, valores):
    return eval(expressao, {"__builtins__": {}}, {"MAX": max, **valores})  # expressões fixas deste arquivo


# ── Planilha ───────────────────────────────────────────────────────────────────
ARIAL = "Arial"
FONTE = Font(name=ARIAL, size=10)
NEGRITO = Font(name=ARIAL, size=10, bold=True)
TITULO = Font(name=ARIAL, size=14, bold=True)
SUBTITULO = Font(name=ARIAL, size=9, italic=True, color="595959")
ENTRADA = Font(name=ARIAL, size=10, color="0000FF")
LIGACAO = Font(name=ARIAL, size=10, color="008000")
CABECALHO = PatternFill("solid", fgColor="D9E1F2")
SECAO = PatternFill("solid", fgColor="F2F2F2")
DESTAQUE = PatternFill("solid", fgColor="FFFF00")
BORDA = Border(bottom=Side(style="thin", color="BFBFBF"))
DOLAR = '"US$" #,##0.00;-"US$" #,##0.00;"-"'
REAL = '"R$" #,##0.00;-"R$" #,##0.00;"-"'
QUANTIDADE = '#,##0.00;-#,##0.00;"-"'
PRECO = '0.00000000'


def cabecalho(aba, linha, titulos, larguras):
    for coluna, (titulo, largura) in enumerate(zip(titulos, larguras), start=1):
        celula = aba.cell(row=linha, column=coluna, value=titulo)
        celula.font, celula.fill = NEGRITO, CABECALHO
        celula.alignment = Alignment(wrap_text=True, vertical="center")
        aba.column_dimensions[celula.column_letter].width = largura


def nomear(livro, nome, aba, celula):
    livro.defined_names[nome] = DefinedName(nome, attr_text=f"{aba}!${celula.column_letter}${celula.row}")


def montar_planilha(precos, premissas, itens, destino):
    livro = Workbook()
    resumo = livro.active
    resumo.title = "Resumo"
    aba_itens, aba_premissas, aba_precos = (livro.create_sheet(nome) for nome in ("Itens", "Premissas", "Precos"))

    # Preços
    aba_precos["A1"], aba_precos["A1"].font = "Preços da AWS Pricing API (us-east-1, sob demanda)", TITULO
    aba_precos["A2"] = f"Consultados em {AGORA:%d/%m/%Y} com pricing:GetProducts; atualize rodando calcular_custos.py"
    aba_precos["A2"].font = SUBTITULO
    cabecalho(aba_precos, 4, ["Chave", "Serviço (código)", "Tipo de uso", "Descrição da AWS", "Preço (US$)", "Unidade",
                              "Vigência", "SKU"], [22, 26, 44, 70, 14, 14, 12, 20])
    for linha, preco in enumerate(precos, start=5):
        valores = [preco["chave"], preco["servico"], preco["tipo_uso"], preco["descricao"], preco["preco_usd"],
                   preco["unidade"], preco["vigencia"], preco["sku"]]
        for coluna, valor in enumerate(valores, start=1):
            celula = aba_precos.cell(row=linha, column=coluna, value=valor)
            celula.font = ENTRADA if coluna == 5 else FONTE
        aba_precos.cell(row=linha, column=5).number_format = PRECO
        nomear(livro, f"p_{preco['chave']}", "Precos", aba_precos.cell(row=linha, column=5))
    aba_precos.freeze_panes = "A5"

    # Premissas
    aba_premissas["A1"], aba_premissas["A1"].font = "Premissas e uso medido", TITULO
    aba_premissas["A2"] = "Edite só a coluna Valor (azul). Fundo amarelo: premissas que mais pesam ou que você deve preencher."
    aba_premissas["A2"].font = SUBTITULO
    cabecalho(aba_premissas, 4, ["Premissa", "Valor", "Unidade", "Origem", "Nome usado nas fórmulas"], [52, 16, 14, 96, 26])
    linha = 5
    for chave, rotulo, valor, unidade, origem in premissas:
        if rotulo is None:
            celula = aba_premissas.cell(row=linha, column=1, value=chave)
            celula.font = NEGRITO
            for coluna in range(1, 6):
                aba_premissas.cell(row=linha, column=coluna).fill = SECAO
            linha += 1
            continue
        aba_premissas.cell(row=linha, column=1, value=rotulo).font = FONTE
        celula = aba_premissas.cell(row=linha, column=2, value=valor)
        celula.font, celula.number_format = ENTRADA, '#,##0.####'
        if chave in {"rateio", "cotacao", "job_execucoes", "amplify_parcela_ssr", "s3_put", "s3_get"}:
            celula.fill = DESTAQUE
        aba_premissas.cell(row=linha, column=3, value=unidade).font = FONTE
        aba_premissas.cell(row=linha, column=4, value=origem).font = FONTE
        aba_premissas.cell(row=linha, column=5, value=f"u_{chave}").font = SUBTITULO
        nomear(livro, f"u_{chave}", "Premissas", celula)
        linha += 1
    aba_premissas.freeze_panes = "A5"

    # Itens
    aba_itens["A1"], aba_itens["A1"].font = "Itens de custo: quantidade por mês x preço", TITULO
    aba_itens["A2"] = ("Quantidade e custo são fórmulas: mude as premissas na aba Premissas. Preço em verde vem da aba Precos.")
    aba_itens["A2"].font = SUBTITULO
    cabecalho(aba_itens, 4, ["Grupo", "Componente", "Serviço", "Quantidade por mês", "Unidade", "Preço (US$)",
                             "Custo por mês (US$)", "Chave do preço", "Observação"], [15, 42, 24, 18, 18, 14, 18, 22, 60])
    primeira = 5
    for linha, item in enumerate(itens, start=primeira):
        aba_itens.cell(row=linha, column=1, value=item["grupo"]).font = FONTE
        aba_itens.cell(row=linha, column=2, value=item["componente"]).font = FONTE
        aba_itens.cell(row=linha, column=3, value=item["servico"]).font = FONTE
        quantidade = aba_itens.cell(row=linha, column=4, value=f"={item['expressao']}")
        quantidade.font, quantidade.number_format = FONTE, QUANTIDADE
        aba_itens.cell(row=linha, column=5, value=item["unidade"]).font = FONTE
        preco = aba_itens.cell(row=linha, column=6, value=f"=p_{item['preco']}")
        preco.font, preco.number_format = LIGACAO, PRECO
        custo = aba_itens.cell(row=linha, column=7, value=f"=D{linha}*F{linha}")
        custo.font, custo.number_format = FONTE, DOLAR
        aba_itens.cell(row=linha, column=8, value=item["preco"]).font = SUBTITULO
        aba_itens.cell(row=linha, column=9, value=item["nota"]).font = FONTE
        for coluna in range(1, 10):
            aba_itens.cell(row=linha, column=coluna).border = BORDA
    ultima = primeira + len(itens) - 1
    aba_itens.freeze_panes = "A5"
    aba_itens.auto_filter.ref = f"A4:I{ultima}"
    intervalo = lambda coluna: f"Itens!${coluna}${primeira}:${coluna}${ultima}"  # noqa: E731

    # Resumo
    resumo["A1"], resumo["A1"].font = "Radar de Perdas: custo mensal na AWS", TITULO
    resumo["A2"] = (f"Conta athie-digital-prod (912668123297), us-east-1. Preços da AWS Pricing API e uso medido em "
                    f"{AGORA:%d/%m/%Y} (últimos {DIAS} dias). Valores sob demanda, sem impostos, créditos ou descontos.")
    resumo["A2"].font = SUBTITULO
    resumo["A3"] = "Como usar: mude só as células azuis da aba Premissas (as amarelas são as que mais mudam o resultado)."
    resumo["A3"].font = SUBTITULO
    resumo.column_dimensions["A"].width, resumo.column_dimensions["B"].width = 62, 20
    resumo.column_dimensions["C"].width = 20
    cabecalho(resumo, 5, ["Total por mês", "US$", "R$"], [62, 20, 20])
    linhas = [
        ("Radar: recursos exclusivos", f'=SUMIFS({intervalo("G")},{intervalo("A")},"Radar")'),
        ("Infra compartilhada da VPC e da conta (valor cheio)", f'=SUMIFS({intervalo("G")},{intervalo("A")},"Compartilhado")'),
        ("Parcela do Radar na infra compartilhada (premissa de rateio)", "=B7*u_rateio"),
        ("Total do Radar com o rateio", "=B6+B8"),
    ]
    for deslocamento, (rotulo, formula) in enumerate(linhas):
        linha = 6 + deslocamento
        resumo.cell(row=linha, column=1, value=rotulo).font = NEGRITO if deslocamento == 3 else FONTE
        celula = resumo.cell(row=linha, column=2, value=formula)
        celula.font, celula.number_format = (NEGRITO if deslocamento == 3 else FONTE), DOLAR
        real = resumo.cell(row=linha, column=3, value=f'=IF(ISNUMBER(u_cotacao),B{linha}*u_cotacao,"")')
        real.font, real.number_format = FONTE, REAL
    resumo["B9"].fill = DESTAQUE
    resumo["B9"].comment = Comment("Soma dos itens do grupo Radar mais a parcela rateada da infra compartilhada.", "calculadora")

    cabecalho(resumo, 11, ["Recursos exclusivos do Radar por serviço", "US$ por mês", "Parte do total"], [62, 20, 20])
    servicos = sorted({item["servico"] for item in itens if item["grupo"] == "Radar"})
    for deslocamento, servico in enumerate(servicos):
        linha = 12 + deslocamento
        resumo.cell(row=linha, column=1, value=servico).font = FONTE
        valor = resumo.cell(row=linha, column=2,
                            value=f'=SUMIFS({intervalo("G")},{intervalo("A")},"Radar",{intervalo("C")},A{linha})')
        valor.font, valor.number_format = FONTE, DOLAR
        parte = resumo.cell(row=linha, column=3, value=f"=IF($B$6=0,0,B{linha}/$B$6)")
        parte.font, parte.number_format = FONTE, "0.0%"
    linha = 12 + len(servicos) + 1
    notas = [
        "Fora desta conta (não entra nos totais): o RDS db-vetorial-prd-clean e o DMS ficam na conta athie-vector e "
        "são pagos pela Athié.",
        "Bedrock: as métricas são por perfil de inferência e somam qualquer sistema da conta que use o mesmo perfil.",
        "Infra compartilhada: o NAT regional (projeto digital-lab), o anexo do Transit Gateway e a zona do Route 53 "
        "atendem outros sistemas; use a premissa de rateio para atribuir uma parte ao Radar.",
        "Franquias da conta (100 GB de saída e 100 minutos de CodePipeline por mês) não foram descontadas: elas são "
        "divididas com outros sistemas.",
    ]
    resumo.cell(row=linha, column=1, value="Notas").font = NEGRITO
    for deslocamento, nota in enumerate(notas, start=1):
        celula = resumo.cell(row=linha + deslocamento, column=1, value=nota)
        celula.font, celula.alignment = FONTE, Alignment(wrap_text=True, vertical="top")
        resumo.merge_cells(start_row=linha + deslocamento, start_column=1, end_row=linha + deslocamento, end_column=3)
        resumo.row_dimensions[linha + deslocamento].height = 28

    for aba in (resumo, aba_itens, aba_premissas, aba_precos):
        aba.sheet_view.showGridLines = False
        for linha_celulas in aba.iter_rows():
            for celula in linha_celulas:
                if isinstance(celula, MergedCell) or celula.font.name == ARIAL:
                    continue
                celula.font = Font(name=ARIAL, size=10, bold=celula.font.bold)
    livro.calculation.fullCalcOnLoad = True
    livro.save(destino)
    return primeira, ultima


# ── Relatório em Markdown ──────────────────────────────────────────────────────
def dolar(valor):
    texto = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"US$ {texto}"


def numero(valor, significativos=4):
    if not valor:
        return "0"
    texto = f"{valor:,.0f}" if abs(valor) >= 1000 else format(Decimal(f"{valor:.{significativos}g}"), "f")
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def montar_relatorio(precos, premissas, itens, uso, destino):
    valores = {f"u_{chave}": (valor if valor is not None else 0) for chave, rotulo, valor, *_ in premissas if rotulo}
    preco_por_chave = {preco["chave"]: preco for preco in precos}
    for item in itens:
        item["quantidade"] = avaliar(item["expressao"], valores)
        item["preco_usd"] = preco_por_chave[item["preco"]]["preco_usd"]
        item["custo"] = item["quantidade"] * item["preco_usd"]
    radar = sum(item["custo"] for item in itens if item["grupo"] == "Radar")
    compartilhado = sum(item["custo"] for item in itens if item["grupo"] == "Compartilhado")
    por_servico = {}
    for item in itens:
        if item["grupo"] == "Radar":
            por_servico[item["servico"]] = por_servico.get(item["servico"], 0) + item["custo"]

    linhas = [
        "# Radar de Perdas: custo mensal na AWS",
        "",
        f"- Conta athie-digital-prod (912668123297), us-east-1. Levantado em {AGORA:%d/%m/%Y}.",
        "- Preços: AWS Pricing API (`pricing:GetProducts`), sob demanda, sem impostos, créditos ou descontos.",
        f"- Uso: medido nos últimos {DIAS} dias (CloudWatch, ECS, ECR, CodeBuild, CodePipeline, Amplify); o que não dá "
        "para medir está marcado como premissa na planilha.",
        "- Calculadora editável: [calculadora-custos-radar.xlsx](./calculadora-custos-radar.xlsx). Arquitetura: "
        "[../arquitetura/ARQUITETURA-RADAR-AWS.md](../arquitetura/ARQUITETURA-RADAR-AWS.md).",
        "",
        "## Resumo",
        "",
        "| Total por mês | US$ |",
        "|---|---:|",
        f"| **Radar: recursos exclusivos** | **{dolar(radar)}** |",
        f"| Infra compartilhada da VPC e da conta (valor cheio, atende outros sistemas) | {dolar(compartilhado)} |",
        "",
        "A infra compartilhada (NAT regional do digital-lab, anexo do Transit Gateway e zona do Route 53) não entra no "
        "total do Radar. A planilha tem uma premissa de rateio para atribuir uma parte dela.",
        "",
        "## Por serviço (recursos exclusivos)",
        "",
        "| Serviço | US$ por mês | Parte |",
        "|---|---:|---:|",
        *[f"| {servico} | {dolar(valor)} | {valor / radar:.0%} |" for servico, valor in
          sorted(por_servico.items(), key=lambda par: -par[1])],
        "",
        "## Itens",
        "",
        "| Grupo | Componente | Quantidade por mês | Preço (US$) | US$ por mês |",
        "|---|---|---:|---:|---:|",
        *[f"| {item['grupo']} | {item['componente']} | {numero(item['quantidade'])} {item['unidade']} | "
          f"{numero(item['preco_usd'], 6)} | {dolar(item['custo'])} |" for item in itens],
        "",
        "## Uso medido que mais pesa",
        "",
        f"- API: {uso['api_tarefas']} tarefa de {numero(uso['api_vcpu'])} vCPU e {numero(uso['api_gb'])} GB o mês todo.",
        f"- ALB: {numero(uso['alb_lcu_medio'], 2)} LCU por hora em média e {numero(uso['alb_requisicoes'])} requisições em "
        f"{DIAS} dias.",
        f"- Bedrock: Sonnet 5 com {numero(uso['sonnet_entrada'])} tokens de entrada e {numero(uso['sonnet_saida'])} de "
        f"saída; Haiku 5.5 com {numero(uso['haiku_entrada'])} e {numero(uso['haiku_saida'])}.",
        f"- Job: {uso['job_execucoes_medidas']} execuções com log em {DIAS} dias, {uso['job_segundos_medio']:.0f} s em média.",
        f"- NAT regional: {uso['nat_zonas']} zonas e {numero(uso['nat_gb_processados'])} GB processados (toda a VPC).",
        "",
        "## Fora do cálculo",
        "",
        "- O RDS db-vetorial-prd-clean e o DMS ficam na conta athie-vector e são pagos pela Athié.",
        "- Franquias grátis da conta (100 GB de saída e 100 minutos de CodePipeline por mês), porque são divididas com "
        "outros sistemas; Savings Plans, créditos, suporte da AWS e impostos.",
        "- O Bedrock é medido por perfil de inferência: se outro sistema da conta usar o mesmo perfil, o consumo dele "
        "entra aqui.",
        "",
        "## Como recalcular",
        "",
        "```bash",
        "MSYS_NO_PATHCONV=1 uv run --with openpyxl python -I calcular_custos.py",
        "```",
        "",
        "O script consulta a Pricing API e as métricas com o perfil `athie-digital-prod` e regrava os quatro arquivos "
        "desta pasta (`precos-aws.json`, `uso-medido.json`, a planilha e este relatório).",
    ]
    destino.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return radar, compartilhado


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    print("consultando preços...", flush=True)
    precos = [buscar_preco(definicao) for definicao in PRECOS]
    (PASTA / "precos-aws.json").write_text(json.dumps(precos, ensure_ascii=False, indent=1), encoding="utf-8")
    print("medindo uso...", flush=True)
    uso = medir()
    (PASTA / "uso-medido.json").write_text(json.dumps(uso, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    premissas = montar_premissas(uso)
    itens = montar_itens()
    primeira, ultima = montar_planilha(precos, premissas, itens, PASTA / "calculadora-custos-radar.xlsx")
    radar, compartilhado = montar_relatorio(precos, premissas, itens, uso, PASTA / "CUSTOS-RADAR.md")
    print(f"itens: {len(itens)} (linhas {primeira} a {ultima}) | Radar: US$ {radar:.2f} | compartilhado: "
          f"US$ {compartilhado:.2f}")
    for item in sorted(itens, key=lambda i: -i["custo"])[:8]:
        print(f"  {item['grupo']:13} {item['componente'][:44]:44} US$ {item['custo']:8.2f}")


if __name__ == "__main__":
    main()
