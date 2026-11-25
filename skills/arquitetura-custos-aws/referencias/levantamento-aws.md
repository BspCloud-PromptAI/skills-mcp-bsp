# Levantamento da conta AWS (só leitura)

Preparo do Git Bash no Windows. O `MSYS_NO_PATHCONV` evita que o bash troque `/ecs/...` por um caminho do Windows:

```bash
export AWS_PROFILE=<perfil> AWS_REGION=us-east-1 AWS_PAGER="" MSYS_NO_PATHCONV=1
```

Este CLI devolve datas como epoch (número) nos serviços de protocolo JSON (ECS, CodePipeline) e como ISO nos
demais. Em Python, trate os dois formatos.

Para ver o conteúdo de um JSON grande, use `--query` com poucos campos. Quando forem muitas chamadas, escreva um
script Python em `%TEMP%` que chama o `aws` por `subprocess`.

## 1. Computação (ECS)

```bash
aws ecs list-clusters
aws ecs describe-services --cluster <c> --services <s> --query 'services[0].{td:taskDefinition,desired:desiredCount,cap:capacityProviderStrategy,net:networkConfiguration.awsvpcConfiguration,lb:loadBalancers,cb:deploymentConfiguration.deploymentCircuitBreaker,exec:enableExecuteCommand}'
aws ecs describe-task-definition --task-definition <família:rev> --query 'taskDefinition.{cpu:cpu,mem:memory,arch:runtimePlatform.cpuArchitecture,taskRole:taskRoleArn,execRole:executionRoleArn,secrets:containerDefinitions[0].secrets[].[name,valueFrom],env:containerDefinitions[0].environment[].name,log:containerDefinitions[0].logConfiguration.options}'
aws ecs describe-tasks --cluster <c> --tasks <arn> --query 'tasks[0].{az:availabilityZone,containers:containers[].name}'
aws scheduler get-schedule --name <agendamento> --query '{expr:ScheduleExpression,tz:ScheduleExpressionTimezone,td:Target.EcsParameters.TaskDefinitionArn,net:Target.EcsParameters.NetworkConfiguration}'
aws events list-rules --name-prefix <projeto>
```

- **Variáveis de ambiente:** liste só os **nomes**. Imprima o valor só das que não são sensíveis (host, modelo,
  modo), com um filtro explícito: `--query "...environment[?contains(\`[\"DB_HOST\",\"AUTH_MODE\"]\`, name)]"`.
- **Senha, chave ou URL com senha no `environment`** é achado de segurança: avise o usuário na hora.
- **Um segundo container** chamado `aws-guardduty-agent-*` vem do GuardDuty Runtime Monitoring. Não é duplicação.

## 2. Rede

```bash
aws ec2 describe-subnets --filters Name=vpc-id,Values=<vpc> --query 'Subnets[].{id:SubnetId,az:AvailabilityZone,cidr:CidrBlock,name:Tags[?Key==`Name`]|[0].Value}' --output table
aws ec2 describe-route-tables --filters Name=vpc-id,Values=<vpc> --query 'RouteTables[].{name:Tags[?Key==`Name`]|[0].Value,subnets:Associations[].SubnetId,routes:Routes[].[DestinationCidrBlock||DestinationPrefixListId,GatewayId||NatGatewayId||VpcPeeringConnectionId||TransitGatewayId]}'
aws ec2 describe-nat-gateways --filter Name=vpc-id,Values=<vpc>     # sem SubnetId e com vários IPs: NAT regional
aws ec2 describe-vpc-endpoints --filters Name=vpc-id,Values=<vpc> --query 'VpcEndpoints[].[ServiceName,VpcEndpointType]'
aws ec2 describe-transit-gateway-attachments
aws ec2 describe-vpc-peering-connections
aws ec2 describe-flow-logs --filter Name=resource-id,Values=<vpc>
aws ec2 describe-security-groups --group-ids <sg> --query 'SecurityGroups[0].{nome:GroupName,entrada:IpPermissions[].{p:FromPort,cidr:IpRanges[].CidrIp,sg:UserIdGroupPairs[].GroupId}}'
aws ec2 describe-network-interfaces --filters Name=vpc-id,Values=<vpc> --query 'NetworkInterfaces[].[InterfaceType,Description,Association.PublicIp!=`null`]' --output text | sort | uniq -c
```

- **Sub-rede pública ou privada:** é a rota `0.0.0.0/0` que decide (IGW ou NAT), não o nome.
- **Quem usa a VPC:** a contagem de ENIs por descrição mostra os outros ALBs, ElastiCache, EFS e tarefas. É assim que
  se descobre o que é compartilhado.
- **Caminho até um banco em outra conta:**
  - veja se o endpoint resolve para IP público (`nslookup`) e se existe rota para o CIDR dela (TGW ou peering);
  - a sub-rede pública sem rota para o TGW sai pela internet;
  - sem flow logs, não afirme o caminho exato: diga que é incerto.

## 3. Entrada

```bash
aws elbv2 describe-load-balancers --names <alb> --query 'LoadBalancers[0].{scheme:Scheme,azs:AvailabilityZones[].[ZoneName,SubnetId],sgs:SecurityGroups}'
aws elbv2 describe-listeners --load-balancer-arn <arn> --query 'Listeners[].{port:Port,proto:Protocol,policy:SslPolicy,cert:Certificates[0].CertificateArn}'
aws wafv2 get-web-acl-for-resource --resource-arn <arn-alb>
aws elbv2 describe-target-groups --target-group-arns <tg> --query 'TargetGroups[0].{hc:HealthCheckPath,type:TargetType}'
aws acm describe-certificate --certificate-arn <arn> --query 'Certificate.{dom:DomainName,status:Status}'
aws route53 list-resource-record-sets --hosted-zone-id <zona> --query "ResourceRecordSets[?contains(Name, '<projeto>')]"
aws amplify get-app --app-id <app>; aws amplify list-domain-associations --app-id <app>
```

## 4. Dados, IA e segredos

```bash
aws rds describe-db-instances --query 'DBInstances[].{id:DBInstanceIdentifier,engine:Engine,ver:EngineVersion,classe:DBInstanceClass,publico:PubliclyAccessible,multiaz:MultiAZ,cripto:StorageEncrypted,gb:AllocatedStorage,tipo:StorageType,subnets:DBSubnetGroup.Subnets[].SubnetIdentifier}'
aws s3api get-bucket-encryption --bucket <b>; aws s3api get-public-access-block --bucket <b>; aws s3api get-bucket-policy --bucket <b>
aws cloudwatch list-metrics --namespace AWS/Bedrock --metric-name InputTokenCount --query 'Metrics[].Dimensions[].Value'
aws secretsmanager list-secrets --filters Key=name,Values=<prefixo>/ --query 'SecretList[].Name'
```

- **Política do bucket que cita um papel pelo nome:** confira antes de trocar o papel da tarefa. Leia a política
  inteira e procure `Deny` para outros principais.
- **Bedrock:** a dimensão `ModelId` mostra os perfis em uso (ex.: `global.anthropic.claude-sonnet-5`). A métrica
  soma todos os sistemas da conta que usam o mesmo perfil.
- **Endereço de banco guardado num segredo** (ex.: URL do chat): leia o valor só dentro de um script e imprima
  apenas o host, a porta e o nome do banco.

## 5. Esteira, papéis e operação

```bash
aws codepipeline get-pipeline --name <p> --query 'pipeline.stages[].{stage:name,acts:actions[].[actionTypeId.provider,configuration.BranchName||configuration.ProjectName||configuration.ServiceName]}'
aws codebuild batch-get-projects --names <proj> --query 'projects[0].{img:environment.image,type:environment.type,compute:environment.computeType,role:serviceRole,bs:source.buildspec}'
aws ecr describe-repositories --repository-names <repo> --query 'repositories[0].{mut:imageTagMutability,scan:imageScanningConfiguration.scanOnPush}'
aws iam list-attached-role-policies --role-name <papel>
aws ecs list-task-definition-families --status ACTIVE                       # quem mais usa o mesmo papel
aws logs describe-log-groups --log-group-name-prefix /ecs/ --query 'logGroups[].[logGroupName,retentionInDays,storedBytes]'
aws cloudwatch describe-alarms --query "MetricAlarms[?contains(AlarmName, '<projeto>')].[AlarmName,StateValue]"
aws guardduty list-detectors
```

- **O `buildspec.yml` do repositório** mostra se o deploy parte da task definition atual (`imagedefinitions.json`).
  Se partir, mudanças feitas na task definition persistem nos próximos deploys.

## 6. Comparar segredos sem imprimir

Modelo para conferir se a senha em texto puro é igual à do segredo e de quem é a chave fixa. O script roda em
`%TEMP%` e nada sensível vai para a tela:

```python
td = aws("ecs", "describe-task-definition", "--task-definition", "<família:rev>")["taskDefinition"]
env = {e["name"]: e["value"] for e in td["containerDefinitions"][0]["environment"]}
segredo = json.loads(aws("secretsmanager", "get-secret-value", "--secret-id", "<nome>")["SecretString"])
print("campos do segredo:", sorted(segredo))
print("DB_PASSWORD igual ao segredo:", env.get("DB_PASSWORD") == segredo.get("password"))
print("conta da chave fixa:", aws("sts", "get-access-key-info", "--access-key-id", env["AWS_ACCESS_KEY_ID"]).get("Account"))
```

- **Dono da chave:** procure o usuário IAM comparando os `AccessKeyId` de `list-access-keys` com a chave, sem
  imprimir o ID.
- **Uso atual:** `get-access-key-last-used` mostra o último serviço e a última data.

## 7. Correção de credenciais (só quando o usuário pedir)

Padrão que funcionou no Radar em 12/11/2026:

1. **Papel da tarefa próprio**, com o mínimo que a aplicação usa:
   - confiança em `ecs-tasks.amazonaws.com` com as condições `aws:SourceAccount` e `aws:SourceArn`;
   - `s3:ListBucket` sem condição de prefixo, porque o `head_object` precisa devolver 404 e não 403;
   - `bedrock:InvokeModel*` nos ARNs `inference-profile/*anthropic.*`, `foundation-model/anthropic.*` e
     `arn:aws:bedrock:::foundation-model/anthropic.*`;
   - `ssmmessages:*` se o ECS Exec estiver ligado.
2. **Simulação** com `aws iam simulate-principal-policy`: tanto o que deve ser permitido quanto o que deve ser negado.
3. **Revisão nova da task definition:**
   - tira do `environment` as senhas e chaves;
   - põe `secrets` com `valueFrom: <arn-do-segredo>:password::`;
   - troca o `taskRoleArn`.
4. **Tarefa avulsa da revisão nova** (`run-task` com `command` substituído), com um teste que só lê: identidade,
   variáveis, S3 e uma chamada mínima ao modelo. Só depois disso, `update-service`.
   - Se a aplicação lê um segredo em tempo de execução (ex.: o job com `DB_SECRET_ARN`), o hook de segredos do
     plugin aws-core e o classificador do modo automático bloqueiam esse teste, mesmo sem imprimir o valor.
   - Nesse caso, valide pela simulação e por uma execução real autorizada pelo usuário. Exemplo:
     `role-radar-job-prod`, em `Projetos/radar/arquitetura/iam/`.
5. **Conferência depois do deploy:**
   - `services-stable`;
   - alvo saudável no ALB;
   - `/healthz` respondendo 200;
   - rota protegida respondendo 401;
   - log sem erro.
6. **Pendências que ficam com o usuário:** desativar a chave antiga, apagar revisões antigas (irreversível) e trocar
   a senha exposta.
