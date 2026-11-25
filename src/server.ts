import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { listSkillFiles, readSkillFile, type Skill } from "./skills.js";

type ToolResult = { content: { type: "text"; text: string }[]; isError?: boolean };

const text = (value: string): ToolResult => ({ content: [{ type: "text", text: value }] });
const error = (value: string): ToolResult => ({ ...text(value), isError: true });

function catalog(skills: Skill[]): string {
  return skills.map((skill) => `- ${skill.name}: ${skill.description}`).join("\n");
}

function instructions(skills: Skill[]): string {
  return [
    "Este servidor guarda skills: instruções passo a passo para tarefas específicas.",
    "Antes de começar uma tarefa, confira se alguma skill abaixo se aplica. Se sim, chame get_skill e siga as instruções dela.",
    "Arquivos citados pela skill são lidos com get_skill_file.",
    "",
    "Skills disponíveis:",
    catalog(skills),
  ].join("\n");
}

function renderSkill(skill: Skill): string {
  const files = listSkillFiles(skill);
  const fileList = files.length
    ? `\n\n---\nArquivos da skill (leia com get_skill_file):\n${files.map((file) => `- ${file}`).join("\n")}`
    : "";
  return `# Skill: ${skill.name}\n\n${skill.body}${fileList}`;
}

export function createServer(skills: Skill[], version: string): McpServer {
  const byName = new Map(skills.map((skill) => [skill.name, skill]));
  const server = new McpServer({ name: "skills-mcp", version }, { instructions: instructions(skills) });

  server.registerTool(
    "list_skills",
    {
      description: `Lista as skills disponíveis com nome e descrição. Skills atuais:\n${catalog(skills)}`,
      inputSchema: {},
    },
    async () => text(catalog(skills) || "Nenhuma skill disponível."),
  );

  server.registerTool(
    "get_skill",
    {
      description: "Retorna as instruções completas de uma skill e a lista dos seus arquivos auxiliares.",
      inputSchema: { name: z.string().describe("Nome da skill, como aparece em list_skills") },
    },
    async ({ name }) => {
      const skill = byName.get(name);
      return skill ? text(renderSkill(skill)) : error(`Skill não encontrada: ${name}`);
    },
  );

  server.registerTool(
    "get_skill_file",
    {
      description: "Lê um arquivo auxiliar de uma skill (template, referência, script).",
      inputSchema: {
        name: z.string().describe("Nome da skill"),
        path: z.string().describe("Caminho relativo do arquivo, como listado em get_skill"),
      },
    },
    async ({ name, path }) => {
      const skill = byName.get(name);
      if (!skill) return error(`Skill não encontrada: ${name}`);
      try {
        return text(readSkillFile(skill, path));
      } catch (err) {
        return error((err as Error).message);
      }
    },
  );

  for (const skill of skills) {
    server.registerPrompt(skill.name, { description: skill.description }, async () => ({
      messages: [{ role: "user", content: { type: "text", text: renderSkill(skill) } }],
    }));
  }

  return server;
}
