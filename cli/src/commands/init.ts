import { Command } from "commander";
import { writeFileSync, existsSync } from "fs";
import { resolve } from "path";
import chalk from "chalk";

const DEFAULT_CONFIG = `# AIGIS configuration
version: "1"
aigis: eval
name: "my-first-eval"
description: "Initial evaluation"

model:
  provider: openai
  model: gpt-4o-mini
  temperature: 0.0

eval:
  prompts:
    - "Answer the following: {{input}}"
  tests:
    - input: "What is 2+2?"
      expected: "4"
  assertions:
    - type: contains
    - type: exact
`;

export const initCommand = new Command("init")
  .description("Initialize a new AIGIS project")
  .argument("[path]", "project directory", ".")
  .action((path: string) => {
    const target = resolve(path, "aigis.yaml");
    if (existsSync(target)) {
      console.error(chalk.red(`File exists: ${target}`));
      process.exit(1);
    }
    writeFileSync(target, DEFAULT_CONFIG, "utf-8");
    console.log(chalk.green(`Created ${target}`));
    console.log("Run: aigis eval aigis.yaml");
  });
