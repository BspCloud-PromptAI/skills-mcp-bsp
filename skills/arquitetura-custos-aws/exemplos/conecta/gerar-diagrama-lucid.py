# Gera o JSON (Lucid Standard Import) do diagrama de arquitetura AWS do Conecta a|w (produção).
# Coordenadas manuais: AZs em colunas, fluxo de cima para baixo (usuário -> WAF -> IGW -> ALB -> tarefas -> RDS),
# esteira de deploy à esquerda e segurança/observabilidade à direita. Uso: python -I gerar-diagrama-lucid.py > saida.json
# Isto gera só a primeira versão. O documento no Lucid (85a74f75-18d4-4543-95bf-19ab8cfdf1a7) recebeu ajustes depois,
# por script: nomes padrão dos ícones apagados, fontes em pt (7/8), zona us-east-1b 220 px mais larga e ECS deslocado.
# A fonte da verdade é o Lucid.
import json
import sys

FORMAS = []
LINHAS = []
COR_TEXTO = "#232F3E"
COR_LINHA = "#545B64"
COR_NOTA = "#687078"


def caixa(x, y, w, h):
    return {"x": x, "y": y, "w": w, "h": h}


def icone(id_, classe, x, y, w=56, h=56):
    FORMAS.append({"id": id_, "type": "namedShape", "className": classe, "boundingBox": caixa(x, y, w, h)})


def grupo(id_, classe, x, y, w, h, texto, fundo=None):
    forma = {"id": id_, "type": "namedContainer", "className": classe, "boundingBox": caixa(x, y, w, h), "text": texto}
    if fundo:
        forma["style"] = {"fill": {"type": "color", "color": fundo}}
    FORMAS.append(forma)


def rotulo(id_, x, y, w, h, titulo, corpo=None, alinhamento="left", tamanho=11, cor=COR_TEXTO):
    html = (f'<p style="font-size:{tamanho}px;text-align:{alinhamento};color:{cor}">'
            f'<span style="font-size:{tamanho + 1}px"><b>{titulo}</b></span>')
    if corpo:
        html += f"<br>{corpo}"
    html += "</p>"
    FORMAS.append({"id": id_, "type": "text", "boundingBox": caixa(x, y, w, h), "text": html})


def nota(id_, x, y, w, h, texto, alinhamento="left"):
    html = f'<p style="font-size:11px;text-align:{alinhamento};color:{COR_NOTA}"><i>{texto}</i></p>'
    FORMAS.append({"id": id_, "type": "text", "boundingBox": caixa(x, y, w, h), "text": html})


def linha(id_, a, pa, b, pb, tipo="straight", seta=True, tracejada=False, texto=None, posicao=0.5, lado="middle"):
    item = {
        "id": id_,
        "lineType": tipo,
        "endpoint1": {"type": "shapeEndpoint", "style": "none", "shapeId": a, "position": {"x": pa[0], "y": pa[1]}},
        "endpoint2": {"type": "shapeEndpoint", "style": "arrow" if seta else "none", "shapeId": b,
                      "position": {"x": pb[0], "y": pb[1]}},
        "stroke": {"color": COR_LINHA, "width": 2, "style": "dashed" if tracejada else "solid"},
    }
    if texto:
        item["text"] = [{"text": f'<span style="font-size:11px;color:{COR_TEXTO}">{texto}</span>',
                         "position": posicao, "side": lado}]
    LINHAS.append(item)


# ── Grade ──────────────────────────────────────────────────────────────────────
VPC_X, VPC_Y = 560, 640
AZ_W, VAO = 480, 160
AZA_X = VPC_X + 40                 # 600
AZB_X = AZA_X + AZ_W + VAO         # 1240
EIXO = AZA_X + AZ_W + VAO // 2     # 1160: usuário, WAF, IGW e ALB
SUB_W = AZ_W - 60                  # 420
SUBA_X, SUBB_X = AZA_X + 30, AZB_X + 30
AZ_Y = 880
PUB_Y, PUB_H = 930, 200
APP_Y, APP_H = 1160, 120
DAD_Y, DAD_H = 1310, 210
AZ_H = DAD_Y + DAD_H + 30 - AZ_Y   # 670
VPC_W = 40 + AZ_W + VAO + AZ_W + 40  # 1200
VPC_H = AZ_Y + AZ_H + 40 - VPC_Y   # 950
LINHA_TAREFA = 1050                # centro das tarefas e do ALB
X_B = 1490                         # coluna da tarefa b, endpoint, S3 e RDS primária
X_A = 990                          # coluna da tarefa a

# ── Contêineres (de fora para dentro: o primeiro fica atrás) ───────────────────
grupo("nuvem", "AWSCloudAWS2024", 40, 340, 2180, 1380, "AWS Cloud")
grupo("conta", "AWSAccountAWS2024", 80, 380, 2100, 1300, "Conta athie-digital-prod")
grupo("regiao", "RegionAWS2024", 120, 510, 2020, 1130, "Região us-east-1 (N. Virgínia)")
grupo("g_esteira", "GenericGroupAWS2024", 160, 550, 360, 380, "Esteira de deploy (família Code)")
grupo("g_iac", "GenericGroupAWS2024", 160, 970, 360, 200, "Infraestrutura como código")
grupo("vpc", "VirtualPrivateCloudVPCAWS2024", VPC_X, VPC_Y, VPC_W, VPC_H, "VPC conecta-prd · 10.41.0.0/16")
grupo("az_a", "AvailabilityZoneAWS2024", AZA_X, AZ_Y, AZ_W, AZ_H, "Zona us-east-1a")
grupo("az_b", "AvailabilityZoneAWS2024", AZB_X, AZ_Y, AZ_W, AZ_H, "Zona us-east-1b")
grupo("pub_a", "PublicSubnetAWS2024", SUBA_X, PUB_Y, SUB_W, PUB_H, "Pública · 10.41.0.0/24", "#F2F6E8")
grupo("pub_b", "PublicSubnetAWS2024", SUBB_X, PUB_Y, SUB_W, PUB_H, "Pública · 10.41.1.0/24", "#F2F6E8")
grupo("app_a", "PrivateSubnetAWS2024", SUBA_X, APP_Y, SUB_W, APP_H, "Aplicação · 10.41.4.0/22", "#EEF6FA")
grupo("app_b", "PrivateSubnetAWS2024", SUBB_X, APP_Y, SUB_W, APP_H, "Aplicação · 10.41.8.0/22", "#EEF6FA")
grupo("dad_a", "PrivateSubnetAWS2024", SUBA_X, DAD_Y, SUB_W, DAD_H, "Dados · 10.41.100.0/24", "#E6F2F8")
grupo("dad_b", "PrivateSubnetAWS2024", SUBB_X, DAD_Y, SUB_W, DAD_H, "Dados · 10.41.101.0/24", "#E6F2F8")
grupo("g_seg", "GenericGroupAWS2024", 1800, 660, 300, 470, "Segurança")
grupo("g_obs", "GenericGroupAWS2024", 1800, 1170, 300, 310, "Observabilidade")
grupo("g_prox", "GenericGroupAWS2024", 1580, 108, 620, 212, "Próximos passos e pendências")

# ── Título ─────────────────────────────────────────────────────────────────────
FORMAS.append({"id": "titulo", "type": "text", "boundingBox": caixa(40, 24, 1480, 44),
               "text": f'<p style="font-size:26px;color:{COR_TEXTO}"><b>Conecta a|w · arquitetura na AWS (produção)</b></p>'})
FORMAS.append({"id": "subtitulo", "type": "text", "boundingBox": caixa(40, 70, 1480, 28),
               "text": f'<p style="font-size:14px;color:{COR_NOTA}">conecta.awdigitallab.com · conta athie-digital-prod · '
                       'região us-east-1 · tudo criado por Terraform (infra/aws) · novembro de 2026</p>'})

# ── Fora da AWS ────────────────────────────────────────────────────────────────
icone("usuarios", "UsersAzure2024", EIXO - 28, 150, 56, 61)
rotulo("r_usuarios", 920, 150, 200, 60, "Colaboradores a|w", "navegador + link de acesso", "right")
FORMAS.append({"id": "github", "type": "image", "boundingBox": caixa(448, 232, 56, 56),
               "image": {"type": "image", "url": "https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png"},
               "stroke": {"color": "#00000000", "width": 0, "style": "solid"}})
rotulo("r_github", 176, 234, 260, 52, "GitHub", "athie-wohnrath/intranet · branch main", "right")

# Próximos passos (planejado)
icone("cognito", "ArchAmazonCognitoAWS2024", 1640, 156, 48, 48)
icone("entra", "EnterpriseApplicationsAzure2024", 1700, 156, 48, 48)
rotulo("r_login", 1600, 212, 190, 96, "1 · Login único pelo HUB",
       "Cognito (o mesmo pool do Radar e do AutoQuant) + Microsoft Entra ID", "center")
FORMAS.append({"id": "datalake", "type": "database", "boundingBox": caixa(1871, 156, 48, 48),
               "style": {"fill": {"type": "color", "color": "#F2F3F3"}, "stroke": {"color": COR_NOTA, "width": 2, "style": "solid"}}})
rotulo("r_datalake", 1800, 212, 190, 96, "2 · Dados reais", "banco da intranet ligado ao Data Lake da Athié (só leitura)", "center")
FORMAS.append({"id": "ia", "type": "cloud", "boundingBox": caixa(2063, 160, 64, 42),
               "style": {"fill": {"type": "color", "color": "#F2F3F3"}, "stroke": {"color": COR_NOTA, "width": 2, "style": "solid"}}})
rotulo("r_ia", 2000, 212, 190, 96, "Depende da Athié", "chaves de IA do Arquimedes: Anthropic, ElevenLabs e Deepgram", "center")

# ── Global (na conta, fora da região) ──────────────────────────────────────────
icone("route53", "ArchAmazonRoute53AWS2024", 1297, 394)
rotulo("r_route53", 1215, 454, 220, 44, "Route 53", "conecta.awdigitallab.com → ALB", "center")

# ── Região, fora da VPC ────────────────────────────────────────────────────────
icone("waf", "ArchAWSWAFAWS2024", EIXO - 28, 560)
rotulo("r_waf", 1200, 556, 230, 64, "AWS WAF", "regras gerenciadas da AWS e limite de tentativas no login da Central")
icone("s3", "ArchAmazonSimpleStorageServiceAWS2024", X_B - 28, 560)
rotulo("r_s3", 1530, 556, 230, 76, "Amazon S3 · mídia", "bucket privado, versionado e só HTTPS: fotos, PDFs e vídeos até 2 GB")

# Esteira de deploy
icone("codepipeline", "ArchAWSCodePipelineAWS2024", 448, 600)
rotulo("r_codepipeline", 176, 600, 260, 56, "CodePipeline", "dispara a cada push na main", "right")
icone("codebuild", "ArchAWSCodeBuildAWS2024", 448, 712)
rotulo("r_codebuild", 176, 708, 260, 64, "CodeBuild", "testes, docker build e deploy no ECS", "right")
icone("ecr", "ArchAmazonElasticContainerRegistryAWS2024", 448, 824)
rotulo("r_ecr", 176, 820, 260, 64, "Amazon ECR", "imagem conecta-aw com a tag do commit (imutável, com scan)", "right")

# Infraestrutura como código
icone("tfstate", "ResAmazonSimpleStorageServiceGeneralpurposebucketAWS2024", 450, 1030, 54, 56)
rotulo("r_tfstate", 176, 1026, 260, 76, "Terraform", "infra/aws no repositório; estado no S3 (athie-terraform-state) com lock", "right")

# Segurança
icone("acm", "ArchAWSCertificateManagerAWS2024", 1822, 712, 48, 48)
rotulo("r_acm", 1882, 706, 204, 60, "Certificate Manager", "certificado TLS do ALB, validado no Route 53")
icone("segredos", "ArchAWSSecretsManagerAWS2024", 1822, 812, 48, 48)
rotulo("r_segredos", 1882, 806, 204, 60, "Secrets Manager", "segredos entregues à tarefa na subida; nada no código")
icone("iam", "ArchAWSIdentityandAccessManagementAWS2024", 1822, 912, 48, 48)
rotulo("r_iam", 1882, 906, 204, 60, "IAM", "a tarefa só acessa o bucket de mídia; sem chaves de acesso")
icone("guardduty", "ArchAmazonGuardDutyAWS2024", 1822, 1012, 48, 48)
rotulo("r_guardduty", 1882, 1006, 204, 60, "GuardDuty", "monitora as tarefas em execução (agente ao lado do app)")

# Observabilidade
icone("cloudwatch", "ArchAmazonCloudWatchAWS2024", 1822, 1222, 48, 48)
rotulo("r_cloudwatch", 1882, 1216, 204, 60, "CloudWatch", "logs por 90 dias, Container Insights e 9 alarmes")
icone("sns", "ArchAmazonSimpleNotificationServiceAWS2024", 1822, 1372, 48, 48)
rotulo("r_sns", 1882, 1366, 204, 60, "SNS", "avisa os alarmes por e-mail")

# ── VPC ────────────────────────────────────────────────────────────────────────
icone("igw", "ResAmazonVPCInternetGatewayAWS2024", EIXO - 28, 712)
rotulo("r_igw", 1200, 712, 240, 60, "Internet gateway", "entrada do ALB e saída das tarefas para a internet (sem NAT)")
icone("endpoint", "ResAmazonVPCEndpointsAWS2024", X_B - 24, 664, 48, 48)
rotulo("r_endpoint", 1526, 664, 200, 48, "Gateway endpoint", "o S3 sem sair da rede da AWS")
icone("ecs", "ArchAmazonElasticContainerServiceAWS2024", 840, 712)
rotulo("r_ecs", 760, 776, 216, 72, "Amazon ECS · Fargate",
       "serviço conecta-prd · 2 a 6 tarefas · auto scaling por CPU · rollback automático", "center")
icone("alb", "ResElasticLoadBalancingApplicationLoadBalancerAWS2024", EIXO - 28, LINHA_TAREFA - 28)
rotulo("r_alb", EIXO - 74, 1086, 148, 72, "Load balancer (ALB)", "HTTPS 443 · TLS 1.2/1.3 · porta 80 vira 443", "center")

# Tarefas Fargate (sub-redes públicas, com IP público e entrada só do ALB)
icone("tarefa_a", "ResAmazonElasticContainerServiceTaskAWS2024", X_A - 24, LINHA_TAREFA - 31, 48, 62)
rotulo("r_tarefa_a", 680, 1020, 274, 60, "Tarefa Fargate", "conecta-aw (1 vCPU, 2 GB) + agente do GuardDuty", "right")
icone("tarefa_b", "ResAmazonElasticContainerServiceTaskAWS2024", X_B - 24, LINHA_TAREFA - 31, 48, 62)
rotulo("r_tarefa_b", 1524, 1018, 160, 64, "Tarefa Fargate", "conecta-aw (1 vCPU, 2 GB) + agente do GuardDuty")

nota("n_app_a", 650, 1200, 300, 60, "Reservada: as tarefas vêm para cá quando houver NAT")
nota("n_app_b", 1290, 1200, 170, 60, "Reservada: as tarefas vêm para cá quando houver NAT")

# RDS PostgreSQL 17 Multi-AZ (sub-redes de dados, sem rota para a internet)
icone("rds_standby", "ResAmazonAuroraPostgreSQLInstanceAWS2024", 700, 1400)
rotulo("r_rds_standby", 766, 1398, 180, 60, "RDS standby", "réplica pronta para assumir")
icone("rds_primaria", "ResAmazonAuroraPostgreSQLInstanceAWS2024", X_B - 28, 1400)
rotulo("r_rds_primaria", 1528, 1394, 156, 76, "RDS primária",
       "PostgreSQL 17 · db.t4g.medium · TLS obrigatório · backup diário (14 dias)")

# ── Legenda ────────────────────────────────────────────────────────────────────
COMO = (f'<p style="font-size:12px;color:{COR_TEXTO}"><span style="font-size:14px"><b>Como funciona</b></span><br>'
        "<b>1</b> · O colaborador abre o link de acesso. O Route 53 aponta conecta.awdigitallab.com para o ALB, "
        "o WAF filtra os pedidos e o ALB termina o HTTPS com o certificado do ACM.<br>"
        "<b>2</b> · O ALB divide o tráfego entre as tarefas Fargate das duas zonas. As tarefas só aceitam conexões "
        "do ALB, na porta 3000.<br>"
        "<b>3</b> · As tarefas usam o RDS PostgreSQL 17 Multi-AZ com TLS obrigatório. Se a primária cair, a standby "
        "assume sozinha.<br>"
        "<b>4</b> · Fotos, PDFs e vídeos vão direto do navegador para o S3 por URL assinada. As tarefas acessam o bucket "
        "pelo gateway endpoint.<br>"
        "<b>5</b> · Cada push na main, inclusive as páginas aprovadas na Central de Conteúdo, dispara o CodePipeline: "
        "o CodeBuild roda os testes, gera a imagem no ECR e faz o rolling deploy no ECS. Se a versão nova não subir, "
        "o ECS volta sozinho para a anterior.</p>")
NOTAS = (f'<p style="font-size:12px;color:{COR_TEXTO}"><span style="font-size:14px"><b>Segurança e operação</b></span><br>'
         "· Segredos no Secrets Manager, entregues à tarefa na subida: nada fica no código nem na imagem.<br>"
         "· Logs por 90 dias, Container Insights e 9 alarmes no CloudWatch, com aviso por e-mail pelo SNS.<br>"
         "· O GuardDuty monitora as tarefas em execução: por isso cada tarefa mostra 2 contêineres (o app e o agente).<br>"
         "· Sem NAT por enquanto: as tarefas ficam nas sub-redes públicas com IP público, mas só aceitam o ALB. "
         "As sub-redes de aplicação já existem para quando o NAT entrar.<br>"
         "· O banco fica em sub-redes sem rota para a internet e só aceita as tarefas, na porta 5432.</p>")
FORMAS.append({"id": "legenda", "type": "text", "boundingBox": caixa(40, 1760, 1080, 210), "text": COMO})
FORMAS.append({"id": "notas", "type": "text", "boundingBox": caixa(1160, 1760, 1060, 210), "text": NOTAS})

# ── Linhas ─────────────────────────────────────────────────────────────────────
linha("l_usuarios_waf", "usuarios", (0.5, 1), "waf", (0.5, 0), texto="1 · HTTPS com o link de acesso", posicao=0.25)
linha("l_usuarios_dns", "usuarios", (1, 0.75), "route53", (0.5, 0), tipo="elbow", tracejada=True, texto="DNS", posicao=0.75)
linha("l_usuarios_s3", "usuarios", (1, 0.25), "s3", (0.5, 0), tipo="elbow", texto="4 · upload direto (URL assinada)",
      posicao=0.22, lado="top")
linha("l_waf_igw", "waf", (0.5, 1), "igw", (0.5, 0))
linha("l_igw_alb", "igw", (0.5, 1), "alb", (0.5, 0))
linha("l_alb_a", "alb", (0, 0.5), "tarefa_a", (1, 0.5))
linha("l_alb_b", "alb", (1, 0.5), "tarefa_b", (0, 0.5), texto="2 · porta 3000, só do ALB", lado="top")
linha("l_b_endpoint", "tarefa_b", (0.5, 0), "endpoint", (0.5, 1), seta=False)
linha("l_endpoint_s3", "endpoint", (0.5, 0), "s3", (0.5, 1))
linha("l_b_rds", "tarefa_b", (0.5, 1), "rds_primaria", (0.5, 0), texto="3 · PostgreSQL com TLS", posicao=0.2)
linha("l_a_rds", "tarefa_a", (0.5, 1), "rds_primaria", (0, 0.5), tipo="elbow")
linha("l_replica", "rds_primaria", (0.5, 1), "rds_standby", (0.5, 1), tipo="elbow", tracejada=True,
      texto="réplica síncrona (Multi-AZ)", lado="bottom")
linha("l_github_pipeline", "github", (0.5, 1), "codepipeline", (0.5, 0), texto="5 · push na main")
linha("l_pipeline_build", "codepipeline", (0.5, 1), "codebuild", (0.5, 0))
linha("l_build_ecr", "codebuild", (0.5, 1), "ecr", (0.5, 0))
linha("l_build_ecs", "codebuild", (1, 0.5), "ecs", (0, 0.5), texto="deploy rolling", lado="top")
linha("l_ecs_github", "ecs", (0.5, 0), "github", (1, 0.5), tipo="elbow", tracejada=True,
      texto="Central de Conteúdo abre PR", posicao=0.78, lado="top")
linha("l_cw_sns", "cloudwatch", (0.5, 1), "sns", (0.5, 0), texto="alarmes")

documento = {"version": 1, "pages": [{"id": "producao", "title": "Produção", "shapes": FORMAS, "lines": LINHAS}]}
sys.stdout.reconfigure(encoding="utf-8")
print(json.dumps(documento, ensure_ascii=False, separators=(",", ":")))
