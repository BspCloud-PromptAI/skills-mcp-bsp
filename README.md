# skills-mcp

Servidor MCP que entrega as skills da BSP para qualquer cliente MCP (Claude Code, Claude Desktop, Cursor e similares).

## O que ele expõe

| Tipo | Nome | Para quê |
|---|---|---|
| Tool | `list_skills` | Lista nome e descrição de cada skill |
| Tool | `get_skill` | Instruções completas da skill e lista de arquivos auxiliares |
| Tool | `get_skill_file` | Lê um arquivo auxiliar da skill |
| Prompt | um por skill | Invocação explícita (ex.: `/aw-authentication`) |

## Configurar

Requer Node 20+. A primeira execução baixa e compila o pacote; depois o `npx` usa o cache.

**Claude Code**

```bash
claude mcp add skills -s user -- npx -y github:BspCloud-PromptAI/skills-mcp
```

No Windows, use `cmd /c npx -y github:BspCloud-PromptAI/skills-mcp` no lugar de `npx ...`.

**Claude Desktop** (`claude_desktop_config.json`), Cursor e outros clientes usam o mesmo bloco:

```json
{
  "mcpServers": {
    "skills": {
      "command": "npx",
      "args": ["-y", "github:BspCloud-PromptAI/skills-mcp"]
    }
  }
}
```

Para receber skills novas, reinicie o cliente com `npx -y github:BspCloud-PromptAI/skills-mcp@main` ou limpe o cache do npx (`npx clear-npx-cache`).

## Adicionar uma skill

1. Crie `skills/<nome>/SKILL.md` no formato oficial:

   ```markdown
   ---
   name: <nome>
   description: O que a skill faz e quando usar.
   ---

   Instruções da skill.
   ```

2. Arquivos auxiliares (templates, referências) ficam na mesma pasta e são citados pelo caminho relativo no `SKILL.md`.
3. Faça push na `main`.

## Desenvolver

```bash
npm install
npm run build
npx @modelcontextprotocol/inspector node dist/index.js
```
