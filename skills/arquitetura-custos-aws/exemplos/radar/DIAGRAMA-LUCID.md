# Diagrama de arquitetura AWS do Radar (Lucid)

- Editar: https://lucid.app/lucidchart/e03b2a92-7b41-4251-816a-51010c2cc027/edit
- Visualizar: https://lucid.app/lucidchart/e03b2a92-7b41-4251-816a-51010c2cc027/view
- Levantado na conta athie-digital-prod (912668123297) em 12/11/2026, com o perfil `athie-digital-prod`.
- O documento no Lucid é a fonte da verdade. Os detalhes técnicos estão em [ARQUITETURA-RADAR-AWS.md](./ARQUITETURA-RADAR-AWS.md).
- O documento antigo (32120363-479d-4d61-a1fd-fc905ab068b0) ficou obsoleto e foi renomeado com o prefixo "[obsoleto]".

## O que o diagrama mostra

Mesmo padrão visual do diagrama do Conecta a|w: ícones AWS 2024 pequenos com o rótulo ao lado, grupos aninhados
(AWS Cloud → conta → região → VPC → sub-redes) e fluxos numerados, explicados no rodapé.

1. O usuário abre radar.awdigitallab.com (Route 53 → Amplify).
2. Login único da a|w (authentication.awdigitallab.com: Cognito + Microsoft Entra ID), que devolve o app_token.
3. O navegador chama a API (radar-api.awdigitallab.com → internet gateway → ALB HTTPS 443 → tarefa na porta 8000).
4. A API lê os resultados no S3, usa o Claude Sonnet 5 no Bedrock no chat e consulta o banco só para leitura.
5. Às 06:00 o EventBridge Scheduler roda o job na sub-rede privada: lê o banco da Athié e grava o parquet no S3.
6. Push na main do back-end: CodePipeline → CodeBuild → ECR → rolling deploy da API. O front sai pelo Amplify.

A conta athie-vector (522294740020), da Athié, aparece embaixo, com o RDS PostgreSQL 18.3 e o DMS que copia o ERP.

## O que foi corrigido em relação à primeira versão

- A API roda nas sub-redes **públicas**, com IP público; o security group só aceita o ALB na porta 8000.
- O job roda só na sub-rede **privada** da zona 1a, sem portas abertas, e sai pelo NAT gateway.
- Entraram o internet gateway, o NAT, o Transit Gateway da Athié (rota para 172.22.0.0/16), o GuardDuty, o
  CloudWatch Logs e o banco do chat (`radar-prod-chat`, nas sub-redes privadas), que guarda o histórico das conversas.
- A API aparece com papel IAM próprio e as senhas vindas do Secrets Manager. É o estado depois da correção de
  12/11/2026; antes, a task definition tinha as senhas e uma chave AWS em texto puro.
- O login é o portal único da a|w, e não um Cognito próprio do Radar.
- Os security groups deixaram de ser desenhados como caixas sobrepostas: as regras estão nos rótulos.
- As pendências reais ficaram no rodapé: sem alarmes, ALB sem WAF, CodeBuild e job com AdministratorAccess, ECR sem
  scan, banco do chat marcado como público e recursos criados à mão.

## Como regenerar

```bash
python -I gerar-diagrama-lucid.py > diagrama-radar-lucid.json
```

1. Importe o JSON no Lucid (Standard Import, `use_assisted_layout=false`).
2. Rode por script `skills.basecanvasediting.setText({itemId, text: ""})` em todos os ícones. O `"text": ""` do JSON
   não apaga o nome padrão que o Lucid escreve embaixo de cada ícone AWS.
3. Rode `skills.text.setTextAlignment({itemId, textVAlign: "top"})` nos blocos `como_funciona`, `seguranca` e
   `pendencias`.
4. Exporte em PNG e confira. Para mudanças pequenas, edite direto no Lucid em vez de regenerar.
