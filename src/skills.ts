import { readdirSync, readFileSync, existsSync } from "node:fs";
import { join, relative, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";
import { parse } from "yaml";

export interface Skill {
  name: string;
  description: string;
  dir: string;
  body: string;
}

const SKILL_FILE = "SKILL.md";
const FRONTMATTER = /^---\r?\n([\s\S]*?)\r?\n---\r?\n?([\s\S]*)$/;

export const skillsDir = fileURLToPath(new URL("../skills", import.meta.url));

export function loadSkills(root = skillsDir): Skill[] {
  return readdirSync(root, { withFileTypes: true })
    .filter((entry) => entry.isDirectory() && existsSync(join(root, entry.name, SKILL_FILE)))
    .map((entry) => parseSkill(join(root, entry.name)))
    .sort((a, b) => a.name.localeCompare(b.name));
}

function parseSkill(dir: string): Skill {
  const raw = readFileSync(join(dir, SKILL_FILE), "utf8");
  const match = raw.match(FRONTMATTER);
  if (!match) throw new Error(`${dir}/${SKILL_FILE} sem frontmatter`);

  const meta = parse(match[1]) as { name?: string; description?: string };
  if (!meta.name || !meta.description) {
    throw new Error(`${dir}/${SKILL_FILE} precisa de name e description no frontmatter`);
  }
  return { name: meta.name, description: meta.description, dir, body: match[2].trim() };
}

export function listSkillFiles(skill: Skill): string[] {
  return readdirSync(skill.dir, { recursive: true, withFileTypes: true })
    .filter((entry) => entry.isFile())
    .map((entry) => relative(skill.dir, join(entry.parentPath, entry.name)).split(sep).join("/"))
    .filter((path) => path !== SKILL_FILE)
    .sort();
}

export function readSkillFile(skill: Skill, path: string): string {
  const target = resolve(skill.dir, path);
  if (!target.startsWith(skill.dir + sep)) {
    throw new Error(`Caminho fora da skill: ${path}`);
  }
  if (!existsSync(target)) {
    throw new Error(`Arquivo não encontrado: ${path}`);
  }
  return readFileSync(target, "utf8");
}
