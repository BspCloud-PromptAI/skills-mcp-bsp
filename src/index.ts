#!/usr/bin/env node
import { readFileSync } from "node:fs";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { createServer } from "./server.js";
import { loadSkills } from "./skills.js";

const { version } = JSON.parse(readFileSync(new URL("../package.json", import.meta.url), "utf8"));

const server = createServer(loadSkills(), version);
await server.connect(new StdioServerTransport());
