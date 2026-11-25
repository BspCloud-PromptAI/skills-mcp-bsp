---
name: aw-authentication
description: Integra um projeto da Athie ao SSO do aw-authentication (Cognito central + app_token). Cadastra o projeto no portal (projects.ts com os links de prod e hml do app) e configura o front e o back do projeto para fazer o handoff e validar o app_token via JWKS. Use quando o usuário pedir para "integrar com o aw-authentication", "colocar o projeto no SSO/portal", "configurar login Cognito da Athie" ou "/aw-authentication".
---

# Integração com o aw-authentication

Responda sempre em pt-BR. Raiz da Athie: `C:\Users\gusta\Documentos\github\BspCloud\athie\`.

## Como o SSO funciona (contrato)
- Só o **aw-authentication** fala com o Cognito (pool central). O app **não** configura Cognito, app client nem Hosted UI.
- Fluxo: usuário loga no portal → clica no card → `GET /api/handoff/<appId>` → redireciona para `<url>/auth/handoff#code=<código>` (`url` = link do app no ambiente do portal, `urls.prod` ou `urls.hml` em `projects.ts`; código criptografado, vale 60 s, uso único, `audience` = origem da `url`).
- O app troca o código em `POST <HUB>/api/handoff/redeem` com `{ code }`. A origem do app precisa ser a mesma da `url` (CORS). Respostas:
  - `200`: `{ app_token, access_token, id_token, expires_in }`
  - `403 { error: "sem-acesso" }`: usuário sem acesso ao app
  - `401`: código inválido, expirado ou já usado
- `app_token`: JWT **ES256**, `iss` = issuer do portal, `aud` = `appId`, `sub` (identidade, sub do Cognito), `email`, `name`, `role` (só em apps com roles), `exp`, `jti`. Chave pública em `<HUB>/api/jwks`.
- Sem token, expirou ou deu 401: mostrar a tela "precisa entrar pelo portal", com um botão que aponta para `<HUB>/api/handoff/<appId>` (reentrada). Não redirecionar sozinho. Sem refresh token.
- Quem tem acesso a qual app (e com qual role) é definido no portal, em `/admin/usuarios`. O app só aplica as permissões da role.
- Dois ambientes, cada um com portal, pool, chave e `iss` próprios: prod `https://authentication.awdigitallab.com` e hml `https://hml-authentication.awdigitallab.com`. A `PROJECT_KEY` do portal escolhe o link do app; o portal hml só mostra apps com `urls.hml`.

Fonte da verdade, leia antes de começar: `aw-authentication/docs/specs/2026-10-16-acesso-e-roles-por-app-design.md`, `aw-authentication/docs/specs/2026-11-18-ambientes-prod-hml.md`, `aw-authentication/src/_data/projects.ts` e `aw-authentication/src/lib/redeem.ts`. Se divergirem do que está aqui, o código vence.

## Implementações de referência
Copie o padrão da que tiver a stack mais próxima:
| App | Front | Back |
|---|---|---|
| AutoQuant | `autoquant/athie_autoquant_frontend` (Next.js export estático): `src/lib/hub.ts`, `src/lib/handoff.ts`, `src/lib/sessao.ts`, `src/app/auth/handoff/page.tsx` | `autoquant/athie_autoquant_backend` (FastAPI): `app/auth.py`, `app/config.py`, `tests/conftest.py` |
| AWA Assistant | `chat-awa-project/CHAT-AWA/frontend` (React): `src/lib/handoff.js`, `src/pages/AuthHandoffPage.jsx` | `chat-awa-project/chat-awa-backend` (NestJS): `src/auth/app-token-verifier.ts` |
| AW Avaliar (com roles) | `avalia-o_for/web/app.js` | `avalia-o_for/server/appToken.js`, `server/auth.js` |

## Passo 1: levantar dados
Leia o projeto alvo (stack, estrutura, como autentica hoje) e confirme com o usuário, numa pergunta só:
- `appId` (kebab-case, vira o `aud` do token), nome e descrição curta para o card, cor (`green | yellow | red | blue | purple`)
- URL base do front em produção (`https://<dominio>`) e em homologação, se já existir (ex.: `https://hml-<dominio>`); o app precisa servir a rota `/auth/handoff` nos dois
- O app tem roles? Se sim, quais
- O que acontece com a autenticação atual do app (substituir ou conviver)

## Passo 2: cadastrar no aw-authentication
O `AGENTS.md` do portal avisa que o Next.js é uma versão nova: consulte `node_modules/next/dist/docs/` antes de mexer em APIs do Next.
1. `src/_data/projects.ts`: novo item em `projects` com `id`, `name`, `description`, `urls: { prod, hml? }` (só a origem de cada front, ex.: `{ prod: "https://app.awdigitallab.com", hml: "https://hml-app.awdigitallab.com" }`), `accent`, `handoff: true`, `roles`. O portal monta `<url>/auth/handoff` sozinho, com o link do ambiente; nada de env nem `amplify.yml`.
   Sem link de hml, grave só `urls: { prod }` e avise o usuário: o app não aparece no portal hml (sem card, handoff 404, fora de `/admin/usuarios`) até ganhar `urls.hml`.
4. Nada no DynamoDB nem no Cognito: o acesso é dado depois, pelo admin, em `/admin/usuarios`.

## Passo 3: configurar o projeto
**Front**
- Variável com a URL do portal do ambiente (ex.: `NEXT_PUBLIC_AUTH_HUB_URL`, mesmo valor do `AW_AUTH_ISSUER`) e constante com o `appId`.
- Página `/auth/handoff`: lê o `code` do fragmento (`#code=`), chama o redeem, trata `403` (tela "sem acesso" com link para o portal) e falha (tela de erro com link de reentrada), guarda o `app_token` na sessão e limpa o fragmento da URL.
- Tela "precisa entrar pelo portal": quem abre o app sem `app_token` válido (sem token, vencido ou inválido) vê uma tela que diz que é preciso fazer login no portal, com um botão "Entrar pelo portal" apontando para `<HUB>/api/handoff/<appId>`. O app não abre nem redireciona sozinho. A mesma tela vale quando o back responde `401`.
- Sessão: lê nome/e-mail (e `role`) do payload do `app_token`, controla expiração pelo `exp` e mostra a tela "precisa entrar pelo portal" quando expirar.
- Chamadas ao back com `Authorization: Bearer <app_token>`; um `401` do back leva à reentrada.

**Back**
- Uma variável só: `AW_AUTH_ISSUER` (igual ao `APP_URL` do portal do ambiente, sem barra final; prod: `https://authentication.awdigitallab.com`, hml: `https://hml-authentication.awdigitallab.com`), validada na inicialização. O JWKS é derivado (`<AW_AUTH_ISSUER>/api/jwks`) e o `appId` (`aud` esperado) é constante no código, nunca env.
- Middleware/guard que valida o Bearer: algoritmo fixo `ES256`, `iss`, `aud`, `exp` e `sub` obrigatórios, JWKS com cache e timeout. JWKS fora do ar responde `503`, não `401`.
- Identidade do usuário = `sub`. Apps com roles: validar a `role` contra a lista do app e aplicar as permissões no código.
- Atualizar `.env.example`, docker-compose e definições de deploy com as novas variáveis.

**Testes** (escreva; só rode se o usuário pedir)
- Back: token válido, assinatura errada, `aud` de outro app, expirado, sem token, JWKS indisponível e, se houver, role inválida. Gere um par ES256 de teste no próprio teste, como nas referências.
- Front: redeem com sucesso, `403` sem acesso, código ausente/inválido, abrir sem token e expiração mostrando a tela "precisa entrar pelo portal" com o botão para a reentrada.

## Passo 4: entregar
Resuma por projeto o que mudou e liste o que o usuário precisa fazer fora do código:
- Criar `AW_AUTH_ISSUER` no deploy do back e a URL do portal no build do front, com o valor de cada ambiente (prod e hml)
- Sem link de hml: lembrar que o app não aparece no portal hml até ganhar `urls.hml`
- Dar acesso aos usuários em `/admin/usuarios` do portal

## Regras
- Não altere o contrato do `app_token` nem o fluxo do portal para encaixar um app; se precisar, pare e leve ao usuário.
- Nunca coloque chave privada, secret ou token real em código ou em arquivo versionado.
- Não faça commit, push nem qualquer ação git que altere estado sem pedido explícito.
- Rodando dentro do `dev-orquestrator`, cada passo vira tarefa para o agente da stack (`dev-frontend-ui-ux`, `dev-backend-*`) e os testes para o `dev-tester`.
