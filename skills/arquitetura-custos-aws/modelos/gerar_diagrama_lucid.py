# Gera o JSON (Lucid Standard Import) do diagrama de arquitetura AWS do Radar de Perdas (produção).
# Mesmo método do diagrama do Conecta: coordenadas manuais, fluxo de cima para baixo, ícones AWS 2024 com o rótulo
# ao lado e fontes em pt. Eixo central: usuário -> internet gateway -> ALB -> API -> banco da Athié (embaixo).
# Uso: python -I gerar-diagrama-lucid.py > diagrama-radar-lucid.json
# Depois de importar (sem layout assistido), rode por script no Lucid: setText "" em todos os ícones (o "text": ""
# do JSON não apaga o nome padrão do ícone) e textVAlign "top" nos três blocos do rodapé.
# Documento: https://lucid.app/lucidchart/e03b2a92-7b41-4251-816a-51010c2cc027/edit (a fonte da verdade é o Lucid).
import json
import sys

FORMAS = []
LINHAS = []
COR_TEXTO = "#232F3E"
COR_LINHA = "#545B64"
COR_NOTA = "#687078"

X_A = 1100  # eixo: usuários, internet gateway, ALB, API e RDS
X_J = 1440  # job diário
X_R = 1700  # serviços regionais: Bedrock, S3 e Scheduler
X_P = 530   # esteira: GitHub, CodePipeline, CodeBuild e ECR
X_S = 204   # ícones do grupo de segurança e operação


def caixa(x, y, w, h):
    return {"x": x, "y": y, "w": w, "h": h}


def icone(id_, classe, cx, cy, w=48, h=48):
    FORMAS.append({"id": id_, "type": "namedShape", "className": classe,
                   "boundingBox": caixa(cx - w // 2, cy - h // 2, w, h), "text": ""})


def grupo(id_, classe, x, y, w, h, texto, fundo=None):
    forma = {"id": id_, "type": "namedContainer", "className": classe, "boundingBox": caixa(x, y, w, h), "text": texto}
    if fundo:
        forma["style"] = {"fill": {"type": "color", "color": fundo}}
    FORMAS.append(forma)


def texto(id_, x, y, w, h, html):
    FORMAS.append({"id": id_, "type": "text", "boundingBox": caixa(x, y, w, h), "text": html})


def rotulo(id_, x, y, w, h, titulo, corpo=None, alinhamento="left"):
    estilo = f"text-align:{alinhamento};color:{COR_TEXTO}"
    html = f'<p style="font-size:8pt;{estilo}"><b>{titulo}</b></p>'
    if corpo:
        html += f'<p style="font-size:7pt;{estilo}">{corpo}</p>'
    texto(id_, x, y, w, h, html)


def linha(id_, a, pa, b, pb, tipo="straight", tracejada=False, rotulo_=None, posicao=0.5, lado="middle"):
    item = {
        "id": id_,
        "lineType": tipo,
        "endpoint1": {"type": "shapeEndpoint", "style": "none", "shapeId": a, "position": {"x": pa[0], "y": pa[1]}},
        "endpoint2": {"type": "shapeEndpoint", "style": "arrow", "shapeId": b, "position": {"x": pb[0], "y": pb[1]}},
        "stroke": {"color": COR_LINHA, "width": 2, "style": "dashed" if tracejada else "solid"},
    }
    if rotulo_:
        item["text"] = [{"text": f'<span style="font-size:7pt;color:{COR_TEXTO}">{rotulo_}</span>',
                         "position": posicao, "side": lado}]
    LINHAS.append(item)


# ── Contêineres (de fora para dentro: o primeiro fica atrás) ───────────────────
grupo("nuvem", "AWSCloudAWS2024", 40, 340, 2064, 1640, "AWS Cloud")
grupo("conta", "AWSAccountAWS2024", 80, 380, 1984, 1220, "Conta athie-digital-prod · 912668123297")
grupo("regiao", "RegionAWS2024", 120, 500, 1904, 1060, "Região us-east-1 (N. Virgínia)")
grupo("g_esteira", "GenericGroupAWS2024", 160, 690, 420, 340, "Esteira de deploy do back-end")
grupo("g_seg", "GenericGroupAWS2024", 160, 1070, 420, 470, "Segurança e operação")
grupo("vpc", "VirtualPrivateCloudVPCAWS2024", 620, 660, 960, 860, "VPC VPC-ATHIE-PRD · 172.20.0.0/16")
grupo("pub", "PublicSubnetAWS2024", 660, 810, 880, 270, "Sub-redes públicas · zonas 1a, 1b e 1c", "#F2F6E8")
grupo("priv", "PrivateSubnetAWS2024", 660, 1180, 880, 300, "Sub-redes privadas · zonas 1a, 1b e 1c", "#E6F2F8")
grupo("conta_banco", "AWSAccountAWS2024", 80, 1640, 1984, 300, "Conta athie-vector · 522294740020 · gerenciada pela Athié")
grupo("vpc_banco", "VirtualPrivateCloudVPCAWS2024", 620, 1700, 960, 210, "VPC do banco · 172.22.0.0/16 · us-east-1")
grupo("g_login", "GenericGroupAWS2024", 1640, 104, 400, 212, "Login único da a|w")

# ── Título ─────────────────────────────────────────────────────────────────────
texto("titulo", 40, 22, 1500, 44,
      f'<p style="font-size:14pt;color:{COR_TEXTO}"><b>Radar de Perdas · arquitetura na AWS (produção)</b></p>')
texto("subtitulo", 40, 68, 1500, 28,
      f'<p style="font-size:7.5pt;color:{COR_NOTA}">radar.awdigitallab.com · conta athie-digital-prod (912668123297) · '
      'região us-east-1 · levantado na conta em 12/11/2026</p>')

# ── Fora da AWS ────────────────────────────────────────────────────────────────
icone("usuarios", "UsersAzure2024", X_A, 202, 56, 61)
rotulo("r_usuarios", X_A - 140, 112, 280, 54, "Diretoria e gestores a|w", "navegador com a conta Microsoft", "center")
FORMAS.append({"id": "github", "type": "image", "boundingBox": caixa(X_P - 28, 172, 56, 56),
               "image": {"type": "image", "url": "https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png"},
               "stroke": {"color": "#00000000", "width": 0, "style": "solid"}})
rotulo("r_github", 180, 166, 310, 70, "GitHub · BspCloud-PromptAI",
       "radar-perdas-backend e radar-perdas-frontend, branch main", "right")
icone("cognito", "ArchAmazonCognitoAWS2024", 1810, 172)
icone("entra", "EnterpriseApplicationsAzure2024", 1870, 172)
rotulo("r_login", 1660, 206, 360, 96, "authentication.awdigitallab.com",
       "portal aw-authentication: Cognito (pool central da a|w) + Microsoft Entra ID; emite o app_token que a API confere",
       "center")

# ── Global (na conta, fora da região) ──────────────────────────────────────────
icone("route53", "ArchAmazonRoute53AWS2024", 1400, 444)
rotulo("r_route53", 1440, 409, 300, 70, "Route 53", "awdigitallab.com: radar → Amplify, radar-api → ALB")

# ── Região, fora da VPC ────────────────────────────────────────────────────────
icone("amplify", "ArchAWSAmplifyAWS2024", 820, 588, 56, 56)
rotulo("r_amplify", 860, 544, 200, 88, "AWS Amplify", "front-end Next.js com SSR, publicado a cada push na main")

icone("codepipeline", "ArchAWSCodePipelineAWS2024", X_P, 770)
rotulo("r_codepipeline", 180, 736, 310, 70, "CodePipeline",
       "pipeline-radar-prod: dispara a cada push na main do back-end", "right")
icone("codebuild", "ArchAWSCodeBuildAWS2024", X_P, 870)
rotulo("r_codebuild", 180, 836, 310, 70, "CodeBuild", "lint e testes, imagem ARM64 no ECR e o job apontado para ela", "right")
icone("ecr", "ArchAmazonElasticContainerRegistryAWS2024", X_P, 970)
rotulo("r_ecr", 180, 936, 310, 70, "Amazon ECR", "ecr-radar-prod: imagem com a tag do commit", "right")

icone("segredos", "ArchAWSSecretsManagerAWS2024", X_S, 1160)
rotulo("r_segredos", 244, 1125, 326, 70, "Secrets Manager",
       "senha do banco, URL do chat e sal, entregues às tarefas na subida")
icone("iam", "ArchAWSIdentityandAccessManagementAWS2024", X_S, 1240)
rotulo("r_iam", 244, 1205, 326, 70, "IAM", "a API tem papel próprio, só com S3, Bedrock e ECS Exec; sem chaves fixas")
icone("guardduty", "ArchAmazonGuardDutyAWS2024", X_S, 1320)
rotulo("r_guardduty", 244, 1285, 326, 70, "GuardDuty", "monitora as tarefas em execução (agente ao lado do app)")
icone("cloudwatch", "ArchAmazonCloudWatchAWS2024", X_S, 1400)
rotulo("r_cloudwatch", 244, 1365, 326, 70, "CloudWatch", "logs por 90 dias e 9 alarmes (API, job, banco do chat e front)")
icone("sns", "ArchAmazonSimpleNotificationServiceAWS2024", X_S, 1480)
rotulo("r_sns", 244, 1445, 326, 70, "SNS", "envia os alarmes e as falhas de deploy para bsp-ia@bspcloud.com")

icone("bedrock", "ArchAmazonBedrockAWS2024", X_R, 904)
rotulo("r_bedrock", X_R + 40, 869, 250, 70, "Amazon Bedrock", "Claude Sonnet 5 (perfil global): chat e análises")
icone("s3", "ArchAmazonSimpleStorageServiceAWS2024", X_R, 1110)
rotulo("r_s3", X_R + 40, 1066, 250, 90, "Amazon S3 · resultados",
       "s3-radar-prod-912668123297 (prefixo prod/): camada gold em parquet, privado e criptografado")
icone("scheduler", "ResAmazonEventBridgeSchedulerAWS2024", X_R, 1300, 48, 47)
rotulo("r_scheduler", X_R + 40, 1266, 250, 70, "EventBridge Scheduler", "todo dia às 06:00 (São Paulo), até 2 novas tentativas")

# ── VPC ────────────────────────────────────────────────────────────────────────
icone("ecs", "ArchAmazonElasticContainerServiceAWS2024", 720, 770, 56, 56)
rotulo("r_ecs", 764, 735, 290, 70, "Amazon ECS · Fargate ARM64", "cluster-radar-prod: a API e o job diário")
icone("igw", "ResAmazonVPCInternetGatewayAWS2024", X_A, 770, 56, 56)
rotulo("r_igw", X_A + 44, 735, 240, 70, "Internet gateway", "entrada do ALB e saída da API")

icone("alb", "ResElasticLoadBalancingApplicationLoadBalancerAWS2024", X_A, 896, 56, 56)
rotulo("r_alb", 840, 862, 220, 70, "Load balancer (ALB)", "HTTPS 443, TLS 1.3, certificado do ACM", "right")
icone("api", "ResAmazonElasticContainerServiceServiceAWS2024", X_A, 1010, 48, 59)
rotulo("r_api", 800, 966, 260, 88, "API · service-radar-prod",
       "FastAPI na porta 8000, só aceita o ALB · 1 tarefa (0,5 vCPU, 1 GB)", "right")

icone("nat", "ResAmazonVPCNATGatewayAWS2024", 720, 1130)
rotulo("r_nat", 756, 1096, 260, 70, "NAT gateway", "saída da sub-rede privada para a internet")

icone("chat", "ResAmazonAuroraPostgreSQLInstanceAWS2024", 990, 1300)
rotulo("r_chat", 700, 1256, 250, 88, "Banco do chat",
       "radar-prod-chat · PostgreSQL 18.3: histórico das conversas, criptografado, backup de 7 dias", "right")
icone("tgw", "ArchAWSTransitGatewayAWS2024", 720, 1420)
rotulo("r_tgw", 756, 1386, 300, 70, "Transit Gateway da Athié",
       "rota privada para a VPC do banco (172.22.0.0/16) e outras redes")
icone("job", "ResAmazonElasticContainerServiceTaskAWS2024", X_J, 1300, 48, 62)
rotulo("r_job", 1170, 1256, 236, 88, "Job diário",
       "taskdef-radar-job: extrai e calcula (1 vCPU, 4 GB, ~1 min); sem portas abertas", "right")

# ── Conta do banco (Athié) ─────────────────────────────────────────────────────
icone("rds", "ResAmazonAuroraPostgreSQLInstanceAWS2024", X_A, 1790, 56, 56)
rotulo("r_rds", X_A - 165, 1824, 330, 70, "RDS PostgreSQL 18.3",
       "db-vetorial-prd-clean · o Radar entra com agent_radar_aw, só SELECT", "center")
icone("dms", "ArchAWSDatabaseMigrationServiceAWS2024", 800, 1790)
rotulo("r_dms", 680, 1824, 240, 70, "AWS DMS", "copia o ERP da Athié (SQL Server) para o RDS", "center")

# ── Rodapé ─────────────────────────────────────────────────────────────────────
def bloco(titulo, itens):
    corpo = "".join(f'<p style="font-size:7pt;color:{COR_TEXTO}">{item}</p>' for item in itens)
    return f'<p style="font-size:9pt;color:{COR_TEXTO}"><b>{titulo}</b></p>' + corpo


COMO = bloco("Como funciona", [
    "<b>1</b> · O usuário abre radar.awdigitallab.com. O Route 53 aponta o nome para o Amplify, que entrega o "
    "front-end Next.js.",
    "<b>2</b> · Sem sessão, o front manda para o login único da a|w (authentication.awdigitallab.com), que autentica "
    "pela conta Microsoft (Cognito + Entra ID) e devolve o app_token.",
    "<b>3</b> · O navegador chama a API em radar-api.awdigitallab.com com esse token. O ALB termina o HTTPS e repassa "
    "para a tarefa da API na porta 8000; a API confere o token na chave pública do login (JWKS).",
    "<b>4</b> · A API responde com os resultados prontos no S3. O chat usa o Claude Sonnet 5 no Bedrock, consulta o "
    "banco da Athié só para leitura e guarda as conversas no banco do chat.",
    "<b>5</b> · Todo dia às 06:00 o EventBridge Scheduler roda o job: ele lê o banco (o ERP copiado pelo DMS), calcula "
    "o panorama das obras e grava os arquivos parquet no S3, que a API passa a servir.",
    "<b>6</b> · Cada push na main do back-end dispara o CodePipeline: o CodeBuild roda lint e testes, publica a imagem "
    "no ECR e aponta o job para ela; depois o pipeline faz o rolling deploy da API, que volta sozinha para a versão "
    "anterior se a nova não subir. O front-end é publicado pelo Amplify a cada push na main.",
])
SEGURANCA = bloco("Segurança e operação", [
    "· Senhas e segredos ficam no Secrets Manager e chegam às tarefas na subida: nada no código, na imagem ou na "
    "task definition. A API usa um papel IAM próprio, só com o que precisa, e nenhuma chave de acesso fixa.",
    "· A API fica nas sub-redes públicas, com IP público, mas o security group só aceita o ALB na porta 8000. O job "
    "fica na sub-rede privada da zona 1a, sem portas abertas, e sai pelo NAT.",
    "· O banco da Athié fica na conta athie-vector: o Radar só lê, com o usuário agent_radar_aw e TLS. As sub-redes "
    "privadas também têm rota para a VPC do banco pelo Transit Gateway da Athié.",
    "· O histórico do chat fica no banco radar-prod-chat, nas sub-redes privadas (criptografado, backup de 7 dias).",
    "· Logs no CloudWatch por 90 dias e 9 alarmes (API fora do ar, erros 5xx, CPU e memória, job sem concluir em "
    "26 h, banco do chat e front); falhas do pipeline, do deploy da API e do build do front também avisam. Tudo chega "
    "por e-mail (SNS) em bsp-ia@bspcloud.com. O GuardDuty monitora as tarefas em execução.",
])
# O bloco de pendências saiu do diagrama no editor do Lucid em 12/11/2026; elas ficam em ARQUITETURA-RADAR-AWS.md.
texto("como_funciona", 40, 2020, 980, 290, COMO)
texto("seguranca", 1060, 2020, 520, 380, SEGURANCA)

# ── Linhas ─────────────────────────────────────────────────────────────────────
linha("l_usuarios_amplify", "usuarios", (0, 0.5), "amplify", (0.5, 0), tipo="elbow",
      rotulo_="1 · abre radar.awdigitallab.com", posicao=0.25)
linha("l_usuarios_login", "usuarios", (1, 0.25), "cognito", (0, 0.5), tracejada=True,
      rotulo_="2 · login com a conta Microsoft", posicao=0.45)
linha("l_usuarios_dns", "usuarios", (1, 0.8), "route53", (0.5, 0), tipo="elbow", tracejada=True,
      rotulo_="DNS", posicao=0.75)
linha("l_usuarios_igw", "usuarios", (0.5, 1), "igw", (0.5, 0), rotulo_="3 · o navegador chama a API (HTTPS)", posicao=0.42)
linha("l_igw_alb", "igw", (0.5, 1), "alb", (0.5, 0))
linha("l_alb_api", "alb", (0.5, 1), "api", (0.5, 0))
linha("l_api_bedrock", "api", (1, 0.3), "bedrock", (0, 0.5), rotulo_="4 · chat com IA", posicao=0.6)
linha("l_api_s3", "api", (1, 0.75), "s3", (0, 0.4), rotulo_="4 · lê os resultados", posicao=0.5)
linha("l_api_rds", "api", (1, 1), "rds", (0.93, 0), rotulo_="4 · consultas do chat (só leitura)", posicao=0.69)
linha("l_api_chat", "api", (0.2, 1), "chat", (1, 0.5), tipo="elbow")
linha("l_scheduler_job", "scheduler", (0, 0.5), "job", (1, 0.65), rotulo_="5 · 06:00", posicao=0.5)
linha("l_job_s3", "job", (1, 0.2), "s3", (0.5, 1), rotulo_="5 · grava os resultados", posicao=0.5)
linha("l_job_rds", "job", (0.5, 1), "rds", (1, 0.5), tipo="elbow", rotulo_="5 · extrai os dados (só leitura)", posicao=0.27)
linha("l_dms_rds", "dms", (1, 0.5), "rds", (0, 0.5))
linha("l_github_pipeline", "github", (0.5, 1), "codepipeline", (0.5, 0), rotulo_="6 · push na main (back-end)")
linha("l_github_amplify", "github", (1, 0.5), "amplify", (0, 0.5), tipo="elbow", rotulo_="push na main (front-end)")
linha("l_pipeline_build", "codepipeline", (0.5, 1), "codebuild", (0.5, 0))
linha("l_build_ecr", "codebuild", (0.5, 1), "ecr", (0.5, 0))
linha("l_pipeline_ecs", "codepipeline", (1, 0.5), "ecs", (0, 0.5), rotulo_="6 · deploy")

documento = {"version": 1, "pages": [{"id": "producao", "title": "Produção", "shapes": FORMAS, "lines": LINHAS}]}
sys.stdout.reconfigure(encoding="utf-8")
print(json.dumps(documento, ensure_ascii=False, separators=(",", ":")))
