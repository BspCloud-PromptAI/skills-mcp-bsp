# Padrão visual do diagrama (Conecta e Radar)

Objetivo: um diretor não técnico entende o fluxo e um engenheiro acha os nomes reais. Antes de começar, exporte o
PNG do diagrama do Radar e confira o resultado esperado.

## Estrutura

- **Grupos aninhados** (`namedContainer`), escritos no JSON do maior para o menor, porque o primeiro fica atrás:
  1. `AWSCloudAWS2024` ("AWS Cloud");
  2. `AWSAccountAWS2024` ("Conta <nome> · <id>");
  3. `RegionAWS2024` ("Região us-east-1 (N. Virgínia)");
  4. `VirtualPrivateCloudVPCAWS2024` ("VPC <nome> · <CIDR>");
  5. `PublicSubnetAWS2024` (fundo `#F2F6E8`) e `PrivateSubnetAWS2024` (fundo `#E6F2F8`).
- **Grupos genéricos** (`GenericGroupAWS2024`, título centralizado): "Esteira de deploy do back-end",
  "Segurança e operação", "Login único da a|w", "Próximos passos e pendências".
- **Outra conta** (ex.: banco do cliente): outro `AWSAccountAWS2024` dentro do mesmo AWS Cloud, embaixo, com a
  própria VPC e o rótulo "gerenciada pelo cliente".
- **Sub-redes:**
  - por padrão, faixas horizontais (públicas em cima, privadas embaixo) que cobrem as zonas, com título curto
    ("Sub-redes públicas · zonas 1a, 1b e 1c"); os CIDRs ficam no documento;
  - zonas em colunas só quando a distribuição importa (RDS Multi-AZ, tarefas nas duas zonas): é a variante do
    Conecta, em `exemplos/conecta/`.
- **Onde fica cada serviço:**
  - Route 53: na conta, fora da região;
  - serviços regionais (Amplify, S3, Bedrock, Scheduler, ECR): na região, fora da VPC;
  - IGW, NAT e TGW: dentro da VPC, fora das faixas (o NAT entre as faixas);
  - o ícone do ECS (cluster) no alto da VPC.
- **Security groups não viram caixa.** A regra vai no rótulo: "só aceita o ALB na porta 8000", "sem portas abertas".
- **O que fica fora da AWS** (usuários, GitHub, login de terceiros) vai acima da nuvem.

## Grade do Radar (ponto de partida, em px de Lucid)

| Elemento | Posição |
|---|---|
| Título (14pt negrito) | x 40, y 22 |
| Subtítulo (7,5pt, `#687078`) | y 68: domínio · conta · região · data do levantamento |
| Linha de fora da AWS | y 110–320. GitHub em x≈530, rótulo à esquerda. Usuários no eixo, rótulo acima. Caixa de login à direita. |
| AWS Cloud / conta / região | y 340 / 380 / 500, recuos de 40 px |
| Esteira de deploy | grupo em x 160–580. Ícones em x=530, rótulos à esquerda, alinhados à direita (x 180–490). |
| Segurança e operação | ícones em x=204, rótulos em x=244 (326 px de largura), um item a cada 80 px |
| VPC | x 620–1580, a partir de y 660. IGW e ECS em y≈770. |
| Faixa pública | y 810–1080: ALB (y≈896) e serviço da API (y≈1010) no eixo |
| Faixa privada | y 1180–1480: banco do chat e job na primeira linha, TGW na segunda |
| Eixo principal | x = 1100: usuários, IGW, ALB, API e banco da outra conta |
| Job | x = 1440 |
| Serviços regionais | x = 1700, rótulo à direita (x+40, 250 px): Bedrock na altura da API, S3 entre a API e o job, Scheduler na altura do job |
| Rodapé | 40 px abaixo da nuvem: "Como funciona" (980 px), "Segurança e operação" (520 px), "Pendências" (484 px) |

Espaçamento entre ícone e rótulo: 16 a 44 px. Entre itens empilhados: 60 a 110 px.

## Ícones e rótulos

- **Tamanho dos ícones:** 48 px; 56 px nos do eixo principal (usuários, Amplify, ECS, IGW, ALB, banco). Respeite a
  proporção do catálogo: tarefa ECS 48×62, serviço ECS 48×59, Scheduler 48×47, usuários 56×61.
- **Rótulo** = bloco `text` ao lado do ícone (embaixo só para os bancos no fim do desenho). Título e corpo em `<p>`
  separados, que mantêm o alinhamento:

```html
<p style="font-size:8pt;text-align:right;color:#232F3E"><b>API · service-radar-prod</b></p>
<p style="font-size:7pt;text-align:right;color:#232F3E">FastAPI na porta 8000, só aceita o ALB · 1 tarefa (0,5 vCPU, 1 GB)</p>
```

- **Medidas:** 7pt dá cerca de 32 caracteres por linha em 250 px (cerca de 8 px por caractere); o título em 8pt
  negrito, cerca de 9,5 px por caractere. Use altura 70 para título mais 2 linhas e 88 para título mais 3.
  - O bloco de texto **não cresce sozinho**: se transbordar, alargue (`resizeBlock`).
- **Rótulo à esquerda do ícone:** alinhado à direita. À direita do ícone: alinhado à esquerda.
- **Conteúdo do rótulo:**
  - título: nome do serviço e do recurso;
  - corpo: o que faz e o número que importa (tamanho, porta, regra, retenção, agenda).
- **Texto:** sem emojis; escape `&`, `<` e `>`.
- **Classes que funcionaram:**
  - usuários: `UsersAzure2024`; Entra ID: `EnterpriseApplicationsAzure2024`;
  - GitHub: shape `image` com `https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png` e
    `stroke` transparente;
  - PostgreSQL: `ResAmazonAuroraPostgreSQLInstanceAWS2024`; RDS genérico: `ArchAmazonRDSAWS2024`;
  - tarefa ECS: `ResAmazonElasticContainerServiceTaskAWS2024`; serviço ECS:
    `ResAmazonElasticContainerServiceServiceAWS2024`; cluster ECS: `ArchAmazonElasticContainerServiceAWS2024`;
  - ALB: `ResElasticLoadBalancingApplicationLoadBalancerAWS2024`; IGW: `ResAmazonVPCInternetGatewayAWS2024`;
    NAT: `ResAmazonVPCNATGatewayAWS2024`; TGW: `ArchAWSTransitGatewayAWS2024`;
  - Scheduler: `ResAmazonEventBridgeSchedulerAWS2024`; Amplify: `ArchAWSAmplifyAWS2024`; Bedrock:
    `ArchAmazonBedrockAWS2024`; S3: `ArchAmazonSimpleStorageServiceAWS2024`;
  - Secrets Manager: `ArchAWSSecretsManagerAWS2024`; IAM: `ArchAWSIdentityandAccessManagementAWS2024`; GuardDuty:
    `ArchAmazonGuardDutyAWS2024`; CloudWatch: `ArchAmazonCloudWatchAWS2024`; SNS:
    `ArchAmazonSimpleNotificationServiceAWS2024`;
  - CodePipeline: `ArchAWSCodePipelineAWS2024`; CodeBuild: `ArchAWSCodeBuildAWS2024`; ECR:
    `ArchAmazonElasticContainerRegistryAWS2024`; DMS: `ArchAWSDatabaseMigrationServiceAWS2024`;
  - Route 53: `ArchAmazonRoute53AWS2024`; Cognito: `ArchAmazonCognitoAWS2024`.
- **Outras classes:** `lucid://shape-libraries/aws-2024/<categoria>` (compute, containers, database,
  networking-and-content-delivery, security-identity-and-compliance, developer-tools, management-and-governance,
  application-integration, front-end-web-and-mobile, artificial-intelligence, storage, group-shapes). Nunca adivinhe
  a classe.

## Linhas

- **Estilo:** cor `#545B64`, 2 px, seta só no destino (`endpoint2.style = "arrow"`). Tracejada para DNS e login.
- **Pontas:** sempre fixadas (`position` nos dois lados). Prefira linha reta; o validador só confere caminho e
  rótulo das retas. Use `elbow` para L e U: a linha sai na direção da borda da ponta.
- **Rótulo:** "N · frase curta" em 7pt (ex.: "3 · o navegador chama a API (HTTPS)", "5 · 06:00",
  "4 · consultas do chat (só leitura)"), em área livre, com `position` entre 0,2 e 0,8. Prefira o vão entre bordas
  de grupos a ficar em cima de uma borda.
- **Nunca** passe linha por ícone, rótulo ou **faixa de título** de grupo. Os títulos do canto superior esquerdo
  ocupam cerca de 50 px de ícone mais 8 px por caractere: encurte o título ("zonas 1a, 1b e 1c") ou mova a linha.
- **Regra do ciclo:** se dois nós (API e job) se ligam aos mesmos dois serviços (S3 e banco), ponha esses serviços
  em lados opostos do eixo dos dois nós: S3 à direita e banco embaixo. Do contrário, as linhas se cruzam. Ponha o
  job deslocado do eixo (x 1440) para a linha vertical da API até o banco passar livre.
- **Duas linhas saindo do mesmo ícone:** use pontas diferentes (0,2, 0,3, 0,75 e 1,0) e no mínimo cerca de 36 px
  entre verticais paralelas.
- **Serviços transversais** (Secrets Manager, IAM, GuardDuty, CloudWatch, SNS) **não ganham linhas**: ficam no
  grupo "Segurança e operação", com a explicação no rótulo.

## Numeração e rodapé

- **Fluxos de 1 a N** na ordem que o usuário vive: abre o site → login → chama a API → dados e IA → rotina agendada
  → deploy.
- **"Como funciona":** um parágrafo por número, em linguagem para diretoria. O número vai em negrito.
- **"Segurança e operação":** segredos e papéis, rede (o que é público e o que é privado), banco de terceiros,
  histórico ou dados próprios, logs, alarmes e monitoramento.
- **"Pendências":** só o que é real e ainda aberto. Se o usuário pediu para mostrar algo como resolvido, desenhe
  resolvido e trate a correção como tarefa.

## Peculiaridades do Lucid (Standard Import e RunScript)

- **Nome padrão do ícone:** aparece em letra grande embaixo dele mesmo com `"text": ""`. Apague depois com
  `skills.basecanvasediting.setText({itemId, text: ""})`. Os IDs do JSON são preservados; blocos criados por
  script ganham ID aleatório.
- **Fontes:** escreva o tamanho em pt no HTML; em px fica minúsculo (11px ≈ 5pt). Título de grupo é texto simples e
  sai em cerca de 8pt.
- **Validador:** `text-fit` mede pela maior fonte do bloco e dá falso alarme. `shape-clearance` entre ícone e o
  próprio rótulo é esperado. Os achados vêm em ordem alfabética de regra: se `connector-path-clearance` e
  `label-placement` não aparecem antes de `container-padding` e `shape-clearance`, não existem, mesmo com o
  relatório truncado. Linhas `elbow` nunca são verificadas: confira no PNG.
- **Contêineres:** `resizeBlock` não move os filhos; `moveBlock` num contêiner move os filhos junto.
- **`setText`:** troca o texto inteiro e perde os estilos. Para reaplicar:
  1. `text.setItemTextStyle({styles: [{style: "fontSize", value: "7"}, {style: "bold", value: "false"}, {style: "textColor", value: "#232F3E"}]})`;
  2. `text.setPartialTextStyle` no título (negrito, 8 ou 9pt) e nos números;
  3. `text.setTextAlignment`.

  Antes de reescrever um bloco que outra sessão pode ter mudado, leia o texto atual (`inspect(...).label`).
- **Linhas por script:** `editLineEndpoint` com `connection` fixa a ponta; `lines.setTextPosition(linha, area, {location})`
  move o rótulo; `createLine({..., shape: "elbow"})` cria linha nova.
- **Script atômico:** se falhar, nada é aplicado. Termine sempre com `validateCanvas` nos itens alterados.
- **Exportação:** o PNG sai com cerca de 2.100 px de largura. Para conferir de perto, passe o `bounding_box` da região.

## Checklist do PNG final

- [ ] Nenhum nome padrão de ícone visível.
- [ ] Nenhuma linha atravessa ícone, rótulo ou título de grupo; as `elbow` foram conferidas a olho.
- [ ] Rótulos de linha legíveis, fora de bordas sempre que possível, sem dois rótulos sobrepostos.
- [ ] Mesma fonte por tipo (título 8pt, corpo 7pt, rodapé 7pt com título 9pt) e nenhum texto transbordando.
- [ ] Nenhum contêiner sobreposto; cada item no grupo certo (sub-rede, VPC, região, conta).
- [ ] Números dos fluxos iguais aos do "Como funciona".
- [ ] Nomes, CIDRs, portas e tamanhos conferidos na conta, e data do levantamento no subtítulo.
- [ ] Gerador atualizado com os ajustes feitos por script.
